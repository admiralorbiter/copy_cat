import asyncio
import edge_tts
from copycat.domain.models import SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider

class EdgeTTSSpeechProvider(SpeechProvider):
    """Speech provider implementation using edge-tts online Bing neural voice service."""

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def synthesize(self, request: SpeechRequest) -> AudioChunk:
        if not request.text or not request.text.strip():
            raise ValueError("Speech request text cannot be empty.")

        async def _stream_synthesis() -> bytes:
            communicate = edge_tts.Communicate(request.text, request.voice, rate=request.rate)
            audio_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.extend(chunk["data"])
            return bytes(audio_bytes)

        try:
            raw_audio = await asyncio.wait_for(_stream_synthesis(), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Edge TTS synthesis timed out after {self.timeout_seconds}s.")
        except Exception as err:
            raise RuntimeError(f"Edge TTS synthesis failed: {err}") from err

        if not raw_audio:
            raise RuntimeError("Edge TTS returned zero audio bytes.")

        # Estimate duration in ms (CBR 48 kbps -> 6 bytes per ms)
        estimated_duration_ms = int(len(raw_audio) / 6.0)

        return AudioChunk(
            chunk_id=f"chunk-{request.request_id}",
            request_id=request.request_id,
            audio_bytes=raw_audio,
            format="mp3",
            duration_ms=estimated_duration_ms,
            block_id=request.block_id,
        )
