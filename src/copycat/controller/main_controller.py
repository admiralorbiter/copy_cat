import asyncio
import uuid
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from copycat.domain.models import PlaybackState, SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider
from copycat.protocols.audio import AudioOutput
from copycat.services.speech_normalizer import normalize_text

class MainController(QObject):
    """Orchestrates playback state machine transitions, synthesis, and audio output."""
    state_changed = Signal(object)  # Emits PlaybackState enum
    status_message_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        speech_provider: SpeechProvider,
        audio_output: AudioOutput,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.speech_provider = speech_provider
        self.audio_output = audio_output
        self.state = PlaybackState.IDLE
        self._active_request_id: Optional[str] = None
        self._current_task: Optional[asyncio.Task] = None

    def _set_state(self, new_state: PlaybackState, message: str = "") -> None:
        self.state = new_state
        self.state_changed.emit(new_state)
        if message:
            self.status_message_changed.emit(message)

    async def read_text(self, raw_text: str, voice: str = "en-US-JennyNeural") -> None:
        """Sanitizes text, triggers async speech synthesis, and initiates playback."""
        cleaned_text = normalize_text(raw_text)
        if not cleaned_text:
            self._set_state(PlaybackState.CAPTURE_FAILED, "Input text cannot be empty.")
            return

        self.stop()  # Cancel any ongoing task and stop audio output

        request_id = str(uuid.uuid4())
        self._active_request_id = request_id

        self._set_state(PlaybackState.BUFFERING, "Synthesizing speech with Edge TTS...")

        request = SpeechRequest(
            request_id=request_id,
            text=cleaned_text,
            voice=voice,
        )

        try:
            self._current_task = asyncio.create_task(self.speech_provider.synthesize(request))
            chunk: AudioChunk = await self._current_task
        except asyncio.CancelledError:
            self._set_state(PlaybackState.IDLE, "Playback cancelled.")
            return
        except Exception as err:
            if self._active_request_id == request_id:
                self._set_state(PlaybackState.SYNTHESIS_FAILED, f"Network error: {err}")
                self.error_occurred.emit(str(err))
            return

        # Stale request guard check
        if self._active_request_id != request_id:
            return

        self._set_state(PlaybackState.PLAYING, "Playing audio")
        try:
            self.audio_output.play(chunk)
        except Exception as err:
            self._set_state(PlaybackState.AUDIO_OUTPUT_FAILED, f"Audio device error: {err}")
            self.error_occurred.emit(str(err))

    def pause(self) -> None:
        if self.state == PlaybackState.PLAYING:
            self.audio_output.pause()
            self._set_state(PlaybackState.PAUSED, "Paused")

    def resume(self) -> None:
        if self.state == PlaybackState.PAUSED:
            self.audio_output.resume()
            self._set_state(PlaybackState.PLAYING, "Playing audio")

    def stop(self) -> None:
        self._active_request_id = None
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            self._current_task = None

        self.audio_output.stop()
        self._set_state(PlaybackState.IDLE, "Ready")
