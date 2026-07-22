import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from copycat.ui.main_window import MainWindow
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState
from copycat.services.settings_service import SettingsService
from tests.mocks.mock_speech_provider import MockSpeechProvider
from tests.mocks.mock_audio_output import MockAudioOutput
from tests.mocks.mock_ollama import MockOllamaTransport
from copycat.services.ollama_transformer import OllamaTransformer

@pytest.mark.asyncio
async def test_main_window_ai_mode_selector_and_health(qtbot, tmp_path):
    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    transport = MockOllamaTransport()
    transformer = OllamaTransformer(transport=transport)
    controller = MainController(speech_provider=speech, audio_output=audio, transformer=transformer)
    settings = SettingsService(config_dir=tmp_path)
    window = MainWindow(controller=controller, settings_service=settings)
    qtbot.addWidget(window)

    assert window.ai_mode_combo.count() == 5
    assert window.get_selected_ai_mode() == "off"

    await window._check_ollama_health()
    assert "AI Mode: Off" in window.ollama_status_label.text()

    # Select AI Code Explanation mode
    window.ai_mode_combo.setCurrentIndex(1)  # Code Explanation
    assert window.get_selected_ai_mode() == "code_summary"

    await window._check_ollama_health()
    assert window.ollama_status_label.text() == "🟢 Ollama: Ready (gemma3:12b)"

@pytest.mark.asyncio
async def test_main_window_read_and_stop_buttons(qtbot, tmp_path):
    speech = MockSpeechProvider(delay=0.0)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)
    settings = SettingsService(config_dir=tmp_path)
    window = MainWindow(controller=controller, settings_service=settings)
    qtbot.addWidget(window)

    window.text_edit.setPlainText("PySide6 UI Integration Test.")
    await window.controller.read_text("PySide6 UI Integration Test.", voice=window.get_selected_voice(), rate=window.get_selected_rate())

    assert controller.state == PlaybackState.PLAYING
    assert "Playing block 1 of 1" in window.status_label.text()

    # Click Stop button
    qtbot.mouseClick(window.stop_button, Qt.MouseButton.LeftButton)

    assert controller.state == PlaybackState.IDLE
    assert window.status_label.text() == "Ready"
