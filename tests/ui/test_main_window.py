import pytest
from PySide6.QtCore import Qt
from copycat.ui.main_window import MainWindow
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState
from tests.mocks.mock_speech_provider import MockSpeechProvider
from tests.mocks.mock_audio_output import MockAudioOutput

@pytest.mark.asyncio
async def test_main_window_read_and_stop_buttons(qtbot):
    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)
    window = MainWindow(controller=controller)
    qtbot.addWidget(window)

    window.text_edit.setPlainText("PySide6 UI Integration Test.")
    assert window.read_button.isEnabled() is True

    # Directly invoke read text asynchronously
    await window.controller.read_text("PySide6 UI Integration Test.")

    assert controller.state == PlaybackState.PLAYING
    assert window.status_label.text() == "Playing audio"
    assert audio.is_playing is True

    # Click Stop button
    qtbot.mouseClick(window.stop_button, Qt.MouseButton.LeftButton)

    assert controller.state == PlaybackState.IDLE
    assert window.status_label.text() == "Ready"
    assert audio.is_playing is False
