import pytest
import asyncio
from PySide6.QtWidgets import QApplication
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState
from tests.mocks.mock_speech_provider import MockSpeechProvider
from tests.mocks.mock_audio_output import MockAudioOutput

@pytest.mark.asyncio
async def test_controller_continuous_multi_block_reading(event_loop):
    speech = MockSpeechProvider(delay=0.01)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    raw_text = "# Block 1 Header\n\nParagraph block 2 text.\n\nParagraph block 3 text."
    await controller.read_text(raw_text)

    assert controller.state == PlaybackState.PLAYING
    assert audio.is_playing is True
    assert len(controller._planned_requests) == 3
    assert controller._current_block_index == 0

    # Simulate completion of Block 0 -> should advance to Block 1
    await controller._on_playback_finished()
    assert controller.state == PlaybackState.PLAYING
    assert controller._current_block_index == 1

    # Simulate completion of Block 1 -> should advance to Block 2
    await controller._on_playback_finished()
    assert controller.state == PlaybackState.PLAYING
    assert controller._current_block_index == 2

    # Simulate completion of Block 2 -> should finish document and transition to IDLE
    await controller._on_playback_finished()
    assert controller.state == PlaybackState.IDLE

@pytest.mark.asyncio
async def test_controller_read_clipboard_success(qapp):
    QApplication.clipboard().setText("Clipboard text prompt")
    speech = MockSpeechProvider(delay=0.01)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    await controller.read_clipboard()

    assert controller.state == PlaybackState.PLAYING
    assert audio.is_playing is True

@pytest.mark.asyncio
async def test_controller_bad_path_empty_input(event_loop):
    speech = MockSpeechProvider()
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    await controller.read_text("   \n\t  ")

    assert controller.state == PlaybackState.CAPTURE_FAILED
    assert len(speech.calls) == 0
    assert audio.is_playing is False

@pytest.mark.asyncio
async def test_controller_bad_path_synthesis_failure(event_loop):
    speech = MockSpeechProvider(should_fail=True)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    await controller.read_text("Hello world")

    assert controller.state == PlaybackState.SYNTHESIS_FAILED
    assert audio.is_playing is False

@pytest.mark.asyncio
async def test_controller_bad_path_audio_device_failure(event_loop):
    speech = MockSpeechProvider()
    audio = MockAudioOutput()
    audio.should_fail = True
    controller = MainController(speech_provider=speech, audio_output=audio)

    await controller.read_text("Test text")

    assert controller.state == PlaybackState.AUDIO_OUTPUT_FAILED
    assert audio.is_playing is False

@pytest.mark.asyncio
async def test_controller_pause_and_resume(event_loop):
    speech = MockSpeechProvider()
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    await controller.read_text("Pause test text")
    assert controller.state == PlaybackState.PLAYING

    controller.pause()
    assert controller.state == PlaybackState.PAUSED
    assert audio.is_paused is True

    controller.resume()
    assert controller.state == PlaybackState.PLAYING
    assert audio.is_paused is False

@pytest.mark.asyncio
async def test_controller_stop_and_rapid_spamming(event_loop):
    speech = MockSpeechProvider(delay=0.1)
    audio = MockAudioOutput()
    controller = MainController(speech_provider=speech, audio_output=audio)

    # Start synthesis task asynchronously
    task = asyncio.create_task(controller.read_text("Rapid stop test text"))
    await asyncio.sleep(0.01)

    assert controller.state in (PlaybackState.PARSING, PlaybackState.BUFFERING)

    # Rapidly call stop 5 times
    for _ in range(5):
        controller.stop()

    assert controller.state == PlaybackState.IDLE
    assert audio.is_playing is False

    await task
    assert controller.state == PlaybackState.IDLE
