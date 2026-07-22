import asyncio
import uuid
from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Slot
import qasync

from copycat.domain.models import (
    PlaybackState,
    SourceSnapshot,
    ReadableDocument,
    SpeechRequest,
    AudioChunk,
)
from copycat.protocols.speech import SpeechProvider
from copycat.protocols.audio import AudioOutput
from copycat.parsing.parser import MarkdownDocumentParser
from copycat.speech.planner import SpeechPlanner
from copycat.sources.clipboard import ClipboardSource

class MainController(QObject):
    """Orchestrates playback state machine transitions, parsing, planning, synthesis, and continuous block reading."""
    state_changed = Signal(object)  # Emits PlaybackState enum
    status_message_changed = Signal(str)
    error_occurred = Signal(str)
    block_changed = Signal(int, int)  # current_block_index, total_blocks

    def __init__(
        self,
        speech_provider: SpeechProvider,
        audio_output: AudioOutput,
        parser: Optional[MarkdownDocumentParser] = None,
        planner: Optional[SpeechPlanner] = None,
        clipboard_source: Optional[ClipboardSource] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.speech_provider = speech_provider
        self.audio_output = audio_output
        self.parser = parser or MarkdownDocumentParser()
        self.planner = planner or SpeechPlanner()
        self.clipboard_source = clipboard_source
        self.state = PlaybackState.IDLE

        self._active_request_id: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None
        self.current_document: Optional[ReadableDocument] = None

        self._planned_requests: List[SpeechRequest] = []
        self._current_block_index: int = 0

        # Connect audio playback finished & error signals if present
        if hasattr(self.audio_output, "playback_finished"):
            self.audio_output.playback_finished.connect(self._on_playback_finished)
        if hasattr(self.audio_output, "playback_error"):
            self.audio_output.playback_error.connect(self._on_playback_error)

    def _set_state(self, new_state: PlaybackState, message: str = "") -> None:
        self.state = new_state
        self.state_changed.emit(new_state)
        if message:
            self.status_message_changed.emit(message)

    @Slot()
    @qasync.asyncSlot()
    async def _on_playback_finished(self) -> None:
        if self.state == PlaybackState.PLAYING:
            # Advance to next block if available
            if self._current_block_index + 1 < len(self._planned_requests):
                self._current_block_index += 1
                await self._play_current_block()
            else:
                self._set_state(PlaybackState.IDLE, "Finished reading document")

    @Slot(str)
    def _on_playback_error(self, error_msg: str) -> None:
        self._set_state(PlaybackState.AUDIO_OUTPUT_FAILED, f"Audio error: {error_msg}")
        self.error_occurred.emit(error_msg)

    async def read_clipboard(self, voice: str = "en-US-JennyNeural", rate: str = "+0%") -> None:
        """Captures text from clipboard and begins continuous reading."""
        if not self.clipboard_source:
            self.clipboard_source = ClipboardSource(self)

        self._set_state(PlaybackState.CAPTURING, "Capturing clipboard...")
        try:
            snapshot = await self.clipboard_source.capture()
        except Exception as err:
            self._set_state(PlaybackState.CAPTURE_FAILED, f"Clipboard error: {err}")
            self.error_occurred.emit(str(err))
            return

        await self.read_text(snapshot.raw_text, voice=voice, rate=rate)

    async def read_text(self, raw_text: str, voice: str = "en-US-JennyNeural", rate: str = "+0%") -> None:
        """Parses text into document blocks, plans speech requests, and begins continuous block playback."""
        if not raw_text or not raw_text.strip():
            self._set_state(PlaybackState.CAPTURE_FAILED, "Input text cannot be empty.")
            return

        self.stop()  # Cancel any ongoing task and stop active audio

        # SourceSnapshot -> MarkdownParser -> SpeechPlanner
        self._set_state(PlaybackState.PARSING, "Parsing document...")
        snapshot = SourceSnapshot(raw_text=raw_text)
        try:
            self.current_document = self.parser.parse(snapshot)
        except Exception as err:
            self._set_state(PlaybackState.PARSE_FAILED, f"Parse error: {err}")
            self.error_occurred.emit(str(err))
            return

        self._planned_requests = self.planner.plan_document(
            self.current_document, voice=voice, rate=rate
        )

        if not self._planned_requests:
            self._set_state(PlaybackState.IDLE, "No speakable content found.")
            return

        self._current_block_index = 0
        await self._play_current_block()

    async def _play_current_block(self) -> None:
        """Synthesizes and plays the SpeechRequest at self._current_block_index."""
        if not self._planned_requests or self._current_block_index >= len(self._planned_requests):
            self._set_state(PlaybackState.IDLE, "Finished reading document")
            return

        request_id = str(uuid.uuid4())
        self._active_request_id = request_id

        request = self._planned_requests[self._current_block_index]
        request.request_id = request_id  # Bind active request ID

        total_blocks = len(self._planned_requests)
        self.block_changed.emit(self._current_block_index + 1, total_blocks)
        msg = f"Reading block {self._current_block_index + 1} of {total_blocks}..."

        self._set_state(PlaybackState.BUFFERING, msg)

        try:
            self._current_task = asyncio.create_task(self.speech_provider.synthesize(request))
            chunk: AudioChunk = await self._current_task
        except asyncio.CancelledError:
            if self._active_request_id == request_id:
                self._set_state(PlaybackState.IDLE, "Playback cancelled.")
            return
        except Exception as err:
            if self._active_request_id == request_id:
                self._set_state(PlaybackState.SYNTHESIS_FAILED, f"Network error: {err}")
                self.error_occurred.emit(str(err))
            return

        if self._active_request_id != request_id:
            return  # Stale request guard

        self._set_state(PlaybackState.PLAYING, f"Playing block {self._current_block_index + 1} of {total_blocks}")
        try:
            self.audio_output.play(chunk)
        except Exception as err:
            self._set_state(PlaybackState.AUDIO_OUTPUT_FAILED, f"Audio error: {err}")
            self.error_occurred.emit(str(err))

    def pause(self) -> None:
        if self.state == PlaybackState.PLAYING:
            self.audio_output.pause()
            self._set_state(PlaybackState.PAUSED, "Paused")

    def resume(self) -> None:
        if self.state == PlaybackState.PAUSED:
            self.audio_output.resume()
            self._set_state(PlaybackState.PLAYING, f"Playing block {self._current_block_index + 1} of {len(self._planned_requests)}")

    def stop(self) -> None:
        self._active_request_id = None
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            self._current_task = None

        self._planned_requests = []
        self._current_block_index = 0
        self.audio_output.stop()
        self._set_state(PlaybackState.IDLE, "Ready")
