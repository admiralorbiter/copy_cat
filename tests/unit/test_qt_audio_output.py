import pytest
from unittest.mock import patch, MagicMock
from copycat.domain.models import AudioChunk
from copycat.services.qt_audio_output import QtAudioPlayerService

@pytest.fixture
def mock_qt_multimedia():
    with patch("copycat.services.qt_audio_output.QMediaPlayer") as mock_player_cls, \
         patch("copycat.services.qt_audio_output.QAudioOutput") as mock_output_cls:
        mock_player = MagicMock()
        mock_output = MagicMock()
        mock_player.MediaStatus.EndOfMedia = "EndOfMedia"
        mock_player.Error.ResourceError = "ResourceError"
        mock_player_cls.MediaStatus.EndOfMedia = "EndOfMedia"
        mock_player_cls.Error.ResourceError = "ResourceError"
        mock_player_cls.return_value = mock_player
        mock_output_cls.return_value = mock_output
        yield mock_player, mock_output

def test_qt_audio_output_play_empty_chunk(mock_qt_multimedia):
    mock_player, _ = mock_qt_multimedia
    service = QtAudioPlayerService()

    error_messages = []
    service.playback_error.connect(error_messages.append)

    empty_chunk = AudioChunk(chunk_id="c0", request_id="r0", audio_bytes=b"")
    service.play(empty_chunk)

    assert len(error_messages) == 1
    assert "Cannot play empty audio chunk" in error_messages[0]
    mock_player.play.assert_not_called()

def test_qt_audio_output_play_valid_chunk_and_stop(mock_qt_multimedia):
    mock_player, _ = mock_qt_multimedia
    service = QtAudioPlayerService()

    valid_chunk = AudioChunk(chunk_id="c1", request_id="r1", audio_bytes=b"fake_audio_bytes")
    service.play(valid_chunk)

    assert service._active_buffer is not None
    assert service._active_bytes is not None
    mock_player.play.assert_called_once()

    service.pause()
    mock_player.pause.assert_called_once()

    service.resume()
    assert mock_player.play.call_count == 2

    service.stop()
    assert mock_player.stop.call_count == 2
    assert service._active_buffer is None
    assert service._active_bytes is None

def test_qt_audio_output_media_status_signals(mock_qt_multimedia):
    mock_player, _ = mock_qt_multimedia
    service = QtAudioPlayerService()

    finished_signals = []
    service.playback_finished.connect(lambda: finished_signals.append(True))

    service._on_media_status_changed(mock_player.MediaStatus.EndOfMedia)
    assert len(finished_signals) == 1

def test_qt_audio_output_error_signals(mock_qt_multimedia):
    mock_player, _ = mock_qt_multimedia
    service = QtAudioPlayerService()

    error_messages = []
    service.playback_error.connect(error_messages.append)

    service._on_error_occurred(mock_player.Error.ResourceError, "Resource unavailable")
    assert len(error_messages) == 1
    assert "Resource unavailable" in error_messages[0]
