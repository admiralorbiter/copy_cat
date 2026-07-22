import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from copycat.domain.models import SpeechRequest, AudioChunk
from copycat.services.edge_tts_provider import EdgeTTSSpeechProvider

@pytest.mark.asyncio
async def test_edge_tts_provider_success():
    provider = EdgeTTSSpeechProvider(timeout_seconds=5.0)
    request = SpeechRequest(request_id="r100", text="Hello from Edge TTS")

    fake_stream_data = [
        {"type": "audio", "data": b"\x00" * 300},
        {"type": "audio", "data": b"\x00" * 300},
    ]

    class FakeCommunicate:
        def __init__(self, text, voice, rate="+0%"):
            pass
        async def stream(self):
            for item in fake_stream_data:
                yield item

    with patch("edge_tts.Communicate", FakeCommunicate):
        chunk = await provider.synthesize(request)
        assert isinstance(chunk, AudioChunk)
        assert chunk.request_id == "r100"
        assert len(chunk.audio_bytes) == 600
        assert chunk.duration_ms == 100

@pytest.mark.asyncio
async def test_edge_tts_provider_empty_input():
    provider = EdgeTTSSpeechProvider()
    request = SpeechRequest(request_id="r101", text="")
    with pytest.raises(ValueError, match="cannot be empty"):
        await provider.synthesize(request)

@pytest.mark.asyncio
async def test_edge_tts_provider_timeout():
    provider = EdgeTTSSpeechProvider(timeout_seconds=0.01)
    request = SpeechRequest(request_id="r102", text="Slow text")

    class SlowCommunicate:
        def __init__(self, text, voice, rate="+0%"):
            pass
        async def stream(self):
            await asyncio.sleep(0.5)
            yield {"type": "audio", "data": b"123"}

    with patch("edge_tts.Communicate", SlowCommunicate):
        with pytest.raises(RuntimeError, match="timed out"):
            await provider.synthesize(request)

@pytest.mark.asyncio
async def test_edge_tts_provider_zero_bytes():
    provider = EdgeTTSSpeechProvider(timeout_seconds=5.0)
    request = SpeechRequest(request_id="r103", text="No audio text")

    class EmptyCommunicate:
        def __init__(self, text, voice, rate="+0%"):
            pass
        async def stream(self):
            if False:
                yield {}

    with patch("edge_tts.Communicate", EmptyCommunicate):
        with pytest.raises(RuntimeError, match="zero audio bytes"):
            await provider.synthesize(request)
