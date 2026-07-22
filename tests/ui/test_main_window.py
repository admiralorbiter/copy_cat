import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from copycat.ui.main_window import MainWindow
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState
from copycat.services.settings_service import SettingsService
from tests.mocks.mock_speech_provider import MockSpeechProvider
from tests.mocks.mock_audio_output import MockAudioOutput

@pytest.mark.asyncio
async def test_main_window_read_and_stop_buttons(qtbot, tmp_path):
    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)
    settings = SettingsService(config_dir=tmp_path)
    window = MainWindow(controller=controller, settings_service=settings)
    qtbot.addWidget(window)

    window.text_edit.setPlainText("PySide6 UI Integration Test.")
    assert window.read_button.isEnabled() is True
    assert window.read_clipboard_button.isEnabled() is True

    # Select voice and rate
    window.voice_combo.setCurrentIndex(1)
    window.rate_combo.setCurrentIndex(3)  # +25%

    assert window.get_selected_voice() == "en-US-GuyNeural"
    assert window.get_selected_rate() == "+25%"

    # Directly invoke read text asynchronously
    await window.controller.read_text("PySide6 UI Integration Test.", voice=window.get_selected_voice(), rate=window.get_selected_rate())

    assert controller.state == PlaybackState.PLAYING
    assert "Playing block 1 of 1" in window.status_label.text()
    assert audio.is_playing is True

    # Click Stop button
    qtbot.mouseClick(window.stop_button, Qt.MouseButton.LeftButton)

    assert controller.state == PlaybackState.IDLE
    assert window.status_label.text() == "Ready"
    assert audio.is_playing is False

@pytest.mark.asyncio
async def test_main_window_navigation_and_highlighting(qtbot, tmp_path):
    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)
    settings = SettingsService(config_dir=tmp_path)
    window = MainWindow(controller=controller, settings_service=settings)
    qtbot.addWidget(window)

    text = "First paragraph block.\n\nSecond paragraph block."
    window.text_edit.setPlainText(text)

    await window.controller.read_text(text)
    assert window.highlighted_block_index == 0

    # Trigger Next block
    await window.controller.skip_next()
    assert window.highlighted_block_index == 1

    # Trigger Prev block
    await window.controller.skip_prev()
    assert window.highlighted_block_index == 0

@pytest.mark.asyncio
async def test_main_window_read_clipboard(qtbot, tmp_path):
    QApplication.clipboard().setText("Clipboard content for UI test")

    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)
    settings = SettingsService(config_dir=tmp_path)
    window = MainWindow(controller=controller, settings_service=settings)
    qtbot.addWidget(window)

    await window.controller.read_clipboard()
    assert controller.state == PlaybackState.PLAYING
    assert audio.is_playing is True
