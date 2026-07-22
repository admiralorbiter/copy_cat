from typing import Optional
from PySide6.QtCore import QObject, Signal
from copycat.domain.models import AudioChunk

class MockAudioOutput(QObject):
    """Mock AudioOutput for tests. Implements AudioOutput protocol structurally."""
    playback_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.is_playing = False
        self.is_paused = False
        self.current_chunk: Optional[AudioChunk] = None
        self.should_fail = False

    def play(self, chunk: AudioChunk) -> None:
        if self.should_fail:
            raise RuntimeError("Mock audio hardware failure")
        self.current_chunk = chunk
        self.is_playing = True
        self.is_paused = False

    def pause(self) -> None:
        if self.is_playing:
            self.is_paused = True

    def resume(self) -> None:
        if self.is_paused:
            self.is_paused = False

    def stop(self) -> None:
        self.is_playing = False
        self.is_paused = False
        self.current_chunk = None

    def simulate_completion(self) -> None:
        self.is_playing = False
        self.playback_finished.emit()

    def simulate_hardware_error(self, message: str = "Audio endpoint error") -> None:
        self.is_playing = False
        self.error_occurred.emit(message)
