from typing import Protocol
from copycat.domain.models import SpeechRequest, AudioChunk

class SpeechProvider(Protocol):
    async def synthesize(self, request: SpeechRequest) -> AudioChunk:
        ...
