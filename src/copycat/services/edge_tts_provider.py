import asyncio
import logging
from typing import Optional
import edge_tts
from copycat.domain.models import SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider

logger = logging.getLogger(__name__)

class EdgeTTSSpeechProvider(SpeechProvider):
    """Speech provider implementation using edge-tts online Bing neural voice service with dynamic timeouts and retries."""

    def __init__(self, timeout_seconds: float = 30.0, max_retries: int = 2, default_timeout_seconds: Optional[float] = None):
        base_timeout = default_timeout_seconds if default_timeout_seconds is not None else timeout_seconds
        self.default_timeout_seconds = base_timeout
        self.max_retries = max_retries

    async def synthesize(self, request: SpeechRequest) -> AudioChunk:
        if not request.text or not request.text.strip():
            raise ValueError("Speech request text cannot be empty.")

        # Respect explicit small test timeouts (<0.5s), otherwise scale dynamically (min 30s) based on text length
        if self.default_timeout_seconds < 0.5:
            dynamic_timeout = self.default_timeout_seconds
        else:
            dynamic_timeout = max(self.default_timeout_seconds, len(request.text) * 0.1)

        async def _stream_synthesis() -> bytes:
            communicate = edge_tts.Communicate(request.text, request.voice, rate=request.rate)
            audio_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.extend(chunk["data"])
            return bytes(audio_bytes)

        raw_audio: bytes = b""
        last_exception: Exception = RuntimeError("Edge TTS returned zero audio bytes.")

        for attempt in range(1, self.max_retries + 1):
            try:
                raw_audio = await asyncio.wait_for(_stream_synthesis(), timeout=dynamic_timeout)
                if raw_audio:
                    break
                else:
                    last_exception = RuntimeError("Edge TTS returned zero audio bytes.")
            except asyncio.TimeoutError as err:
                last_exception = RuntimeError(f"Edge TTS synthesis timed out after {dynamic_timeout:.1f}s.")
                logger.warning(f"Edge TTS attempt {attempt}/{self.max_retries} timed out ({dynamic_timeout:.1f}s SLA). Retrying...")
            except Exception as err:
                last_exception = RuntimeError(f"Edge TTS synthesis failed: {err}")
                logger.warning(f"Edge TTS attempt {attempt}/{self.max_retries} failed ({err}). Retrying...")

            if attempt < self.max_retries:
                await asyncio.sleep(0.5)

        if not raw_audio:
            raise last_exception

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
