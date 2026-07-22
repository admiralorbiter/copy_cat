import asyncio
from typing import List, Optional
from copycat.domain.models import SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider

class MockSpeechProvider(SpeechProvider):
    def __init__(self, should_fail: bool = False, delay: float = 0.01):
        self.should_fail = should_fail
        self.delay = delay
        self.calls: List[SpeechRequest] = []

    async def synthesize(self, request: SpeechRequest) -> AudioChunk:
        self.calls.append(request)
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise RuntimeError("Mock network error: Edge TTS service unavailable")

        fake_audio = b"\xFF\xF3\x44\xC0" + b"\x00" * 120
        return AudioChunk(
            chunk_id=f"chunk-{request.request_id}",
            request_id=request.request_id,
            audio_bytes=fake_audio,
            format="mp3",
            duration_ms=500,
            block_id=request.block_id,
        )
