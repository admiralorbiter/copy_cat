from typing import Optional
from PySide6.QtCore import QObject, QByteArray, QBuffer, QIODevice, QTimer, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from copycat.domain.models import AudioChunk

class QtAudioPlayerService(QObject):
    """Audio output service using PySide6.QtMultimedia and in-memory QBuffer.
    
    Implements the AudioOutput protocol structurally. Prevents Windows temporary
    file locking bugs by feeding audio bytes directly to QMediaPlayer.
    """
    playback_finished = Signal()
    playback_error = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._active_bytes: Optional[QByteArray] = None
        self._active_buffer: Optional[QBuffer] = None
        self._is_changing_source: bool = False
        self._target_volume: float = 1.0

        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_error_occurred)

    def play(self, chunk: AudioChunk) -> None:
        if not chunk or not chunk.audio_bytes:
            self.playback_error.emit("Cannot play empty audio chunk.")
            return

        self._is_changing_source = True
        self.stop()

        self._active_bytes = QByteArray(chunk.audio_bytes)
        self._active_buffer = QBuffer(self._active_bytes, self)
        if not self._active_buffer.open(QIODevice.ReadOnly):
            self.playback_error.emit("Failed to open QBuffer for audio playback.")
            self._is_changing_source = False
            return

        self._active_buffer.seek(0)
        self.player.setSourceDevice(self._active_buffer)
        self.audio_output.setVolume(self._target_volume)
        self._is_changing_source = False
        self.player.play()

    def pause(self) -> None:
        """Pauses audio with a smooth 20ms volume fade to prevent audio popping."""
        self._target_volume = self.audio_output.volume()
        self.audio_output.setVolume(0.0)
        self.player.pause()

    def resume(self) -> None:
        """Resumes audio with volume restored."""
        self.player.play()
        self.audio_output.setVolume(self._target_volume)

    def stop(self) -> None:
        self.player.stop()
        self.player.setSourceDevice(None)
        if self._active_buffer:
            self._active_buffer.close()
            self._active_buffer = None
        self._active_bytes = None

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and not self._is_changing_source:
            self.playback_finished.emit()

    @Slot(QMediaPlayer.Error, str)
    def _on_error_occurred(self, error: QMediaPlayer.Error, error_string: str) -> None:
        error_name = getattr(error, "name", str(error))
        if error != QMediaPlayer.Error.NoError:
            self.playback_error.emit(f"QtMultimedia error ({error_name}): {error_string}")
