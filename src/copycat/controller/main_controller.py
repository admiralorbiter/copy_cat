import asyncio
import uuid
from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Slot
import qasync

from copycat.domain.models import (
    PlaybackState,
    SourceSnapshot,
    ReadableDocument,
    DocumentBlock,
    ReadingSession,
    SpeechRequest,
    AudioChunk,
    ReadingPolicy,
)
from copycat.protocols.speech import SpeechProvider
from copycat.protocols.audio import AudioOutput
from copycat.protocols.transformer import DocumentTransformer
from copycat.parsing.parser import MarkdownDocumentParser
from copycat.speech.planner import SpeechPlanner
from copycat.sources.clipboard import ClipboardSource
from copycat.services.prefetch_queue import BoundedPrefetchQueue
from copycat.services.ollama_transformer import OllamaTransformer

class MainController(QObject):
    """Orchestrates playback state machine, ReadingSession, pre-fetch queue, AI DocumentTransformer, and navigation."""
    state_changed = Signal(object)  # Emits PlaybackState enum
    status_message_changed = Signal(str)
    error_occurred = Signal(str)
    block_changed = Signal(int, int, object)  # current_block_1idx, total_blocks, DocumentBlock
    boundary_reached = Signal(str)  # "start" or "end"
    transforming_block = Signal(int)  # block_1idx being transformed by Ollama

    def __init__(
        self,
        speech_provider: SpeechProvider,
        audio_output: AudioOutput,
        parser: Optional[MarkdownDocumentParser] = None,
        planner: Optional[SpeechPlanner] = None,
        transformer: Optional[DocumentTransformer] = None,
        clipboard_source: Optional[ClipboardSource] = None,
        prefetch_queue: Optional[BoundedPrefetchQueue] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.speech_provider = speech_provider
        self.audio_output = audio_output
        self.parser = parser or MarkdownDocumentParser()
        self.planner = planner or SpeechPlanner()
        self.transformer = transformer or OllamaTransformer()
        self.clipboard_source = clipboard_source
        
        self.prefetch_queue = prefetch_queue or BoundedPrefetchQueue(
            speech_provider=self.speech_provider,
            planner=self.planner,
            transformer=self.transformer,
            capacity=10,
        )

        self.state = PlaybackState.IDLE
        self.session: Optional[ReadingSession] = None
        self.voice: str = "en-US-JennyNeural"
        self.rate: str = "+0%"
        self.ai_mode: str = "off"

        self._active_request_id: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None

        if hasattr(self.audio_output, "playback_finished"):
            self.audio_output.playback_finished.connect(self._on_playback_finished)
        if hasattr(self.audio_output, "playback_error"):
            self.audio_output.playback_error.connect(self._on_playback_error)

    @property
    def current_document(self) -> Optional[ReadableDocument]:
        return self.session.document if self.session else None

    def _set_state(self, new_state: PlaybackState, message: str = "") -> None:
        self.state = new_state
        self.state_changed.emit(new_state)
        if message:
            self.status_message_changed.emit(message)

    @Slot()
    @qasync.asyncSlot()
    async def _on_playback_finished(self) -> None:
        if self.state == PlaybackState.PLAYING and self.session:
            if self.session.can_skip_next():
                self.session.advance_next()
                await self._play_current_session_block()
            else:
                self._set_state(PlaybackState.IDLE, "Finished reading document")

    @Slot(str)
    def _on_playback_error(self, error_msg: str) -> None:
        self._set_state(PlaybackState.AUDIO_OUTPUT_FAILED, f"Audio error: {error_msg}")
        self.error_occurred.emit(error_msg)

    async def read_clipboard(self, voice: str = "en-US-JennyNeural", rate: str = "+0%", ai_mode: str = "off") -> None:
        if not self.clipboard_source:
            self.clipboard_source = ClipboardSource(self)

        self._set_state(PlaybackState.CAPTURING, "Capturing clipboard...")
        try:
            snapshot = await self.clipboard_source.capture()
        except Exception as err:
            self._set_state(PlaybackState.CAPTURE_FAILED, f"Clipboard error: {err}")
            self.error_occurred.emit(str(err))
            return

        await self.read_text(snapshot.raw_text, voice=voice, rate=rate, ai_mode=ai_mode)

    async def read_text(
        self,
        raw_text: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        ai_mode: str = "off",
    ) -> None:
        if not raw_text or not raw_text.strip():
            self._set_state(PlaybackState.CAPTURE_FAILED, "Input text cannot be empty.")
            return

        self.stop()

        self.voice = voice
        self.rate = rate
        self.ai_mode = ai_mode
        self.planner.policy.ai_mode = ai_mode

        if ai_mode == "document_summary" and self.transformer:
            self._set_state(PlaybackState.PARSING, "🟡 Ollama: Generating full document summary (this may take a while)...")
            summary = await self.transformer.summarize_document(raw_text)
            if summary:
                raw_text = summary
            else:
                self._set_state(PlaybackState.PARSE_FAILED, "Failed to generate document summary.")
                self.error_occurred.emit("Ollama failed to generate document summary.")
                return

        self._set_state(PlaybackState.PARSING, "Parsing document...")
        snapshot = SourceSnapshot(raw_text=raw_text)
        try:
            doc = self.parser.parse(snapshot)
        except Exception as err:
            self._set_state(PlaybackState.PARSE_FAILED, f"Parse error: {err}")
            self.error_occurred.emit(str(err))
            return

        if not doc.blocks:
            self._set_state(PlaybackState.IDLE, "No speakable content found.")
            return

        policy = ReadingPolicy(ai_mode=ai_mode)
        self.session = ReadingSession(document=doc, policy=policy)
        self.prefetch_queue.set_generation(self.session.generation)

        await self._play_current_session_block()

    async def _play_current_session_block(self) -> None:
        if not self.session or not self.session.current_block:
            self._set_state(PlaybackState.IDLE, "Finished reading document")
            return

        block = self.session.current_block
        current_idx = self.session.position.block_index
        total = self.session.total_blocks
        current_gen = self.session.generation

        self.block_changed.emit(current_idx + 1, total, block)

        request_id = str(uuid.uuid4())
        self._active_request_id = request_id

        # Emit transforming status if AI mode active
        if self.ai_mode != "off":
            self.transforming_block.emit(current_idx + 1)
            msg = f"Asking Ollama to summarize block {current_idx + 1} of {total}..."
        else:
            msg = f"Reading block {current_idx + 1} of {total}..."

        self._set_state(PlaybackState.BUFFERING, msg)

        # Stage 1: Async plan & AI transformation
        spoken_text = await self.planner.plan_block_async(block, self.transformer)
        if not spoken_text or not spoken_text.strip():
            if self.session.can_skip_next():
                self.session.advance_next()
                await self._play_current_session_block()
            else:
                self._set_state(PlaybackState.IDLE, "Finished reading document")
            return

        req = SpeechRequest(
            request_id=request_id,
            text=spoken_text,
            voice=self.voice,
            rate=self.rate,
            block_id=block.block_id,
        )

        # Stage 2: Retrieve audio chunk from pre-fetch queue or synthesize
        try:
            self._current_task = asyncio.create_task(self.prefetch_queue.get_chunk(req, current_gen))
            chunk: AudioChunk = await self._current_task
        except asyncio.CancelledError:
            if self.session and self.session.generation == current_gen:
                self._set_state(PlaybackState.IDLE, "Playback cancelled.")
            return
        except Exception as err:
            if self.session and self.session.generation == current_gen:
                self.error_occurred.emit(f"Block {current_idx + 1} synthesis failed: {err}")
                if self.session.can_skip_next():
                    self.status_message_changed.emit(f"Skipping block {current_idx + 1} due to network timeout...")
                    await asyncio.sleep(0.5)
                    self.session.advance_next()
                    await self._play_current_session_block()
                else:
                    self._set_state(PlaybackState.SYNTHESIS_FAILED, f"Network error: {err}")
            return

        if not self.session or self.session.generation != current_gen:
            return  # Stale generation guard

        self._set_state(PlaybackState.PLAYING, f"Playing block {current_idx + 1} of {total}")
        try:
            self.audio_output.play(chunk)
        except Exception as err:
            self._set_state(PlaybackState.AUDIO_OUTPUT_FAILED, f"Audio error: {err}")
            self.error_occurred.emit(str(err))
            return

        # Trigger Dual-Stage background pre-fetch for upcoming blocks (Eager Deep Lookahead)
        for offset in range(1, self.prefetch_queue.capacity):
            if current_idx + offset < total:
                next_block = self.session.document.blocks[current_idx + offset]
                asyncio.create_task(
                    self.prefetch_queue.prefetch_block(
                        next_block, voice=self.voice, rate=self.rate, generation=current_gen
                    )
                )

    @qasync.asyncSlot()
    async def skip_next(self) -> None:
        if not self.session:
            return
        if self.session.can_skip_next():
            self.audio_output.stop()
            self.session.skip_next()
            self.prefetch_queue.set_generation(self.session.generation)
            await self._play_current_session_block()
        else:
            self.boundary_reached.emit("end")

    @qasync.asyncSlot()
    async def skip_prev(self) -> None:
        if not self.session:
            return
        if self.session.can_skip_prev():
            self.audio_output.stop()
            self.session.skip_prev()
            self.prefetch_queue.set_generation(self.session.generation)
            await self._play_current_session_block()
        else:
            self.boundary_reached.emit("start")

    def pause(self) -> None:
        if self.state == PlaybackState.PLAYING:
            self.audio_output.pause()
            self._set_state(PlaybackState.PAUSED, "Paused")

    def resume(self) -> None:
        if self.state == PlaybackState.PAUSED and self.session:
            self.audio_output.resume()
            curr = self.session.position.block_index + 1
            total = self.session.total_blocks
            self._set_state(PlaybackState.PLAYING, f"Playing block {curr} of {total}")

    def stop(self) -> None:
        self._active_request_id = None
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            self._current_task = None

        if self.session:
            self.session.generation += 1
            self.prefetch_queue.set_generation(self.session.generation)
            self.session = None

        self.audio_output.stop()
        self._set_state(PlaybackState.IDLE, "Ready")
