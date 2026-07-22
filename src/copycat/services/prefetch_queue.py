import asyncio
import logging
import uuid
from typing import Dict, Optional, TYPE_CHECKING
from copycat.domain.models import DocumentBlock, SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider
from copycat.protocols.transformer import DocumentTransformer

if TYPE_CHECKING:
    from copycat.speech.planner import SpeechPlanner

logger = logging.getLogger(__name__)

class BoundedPrefetchQueue:
    """Bounded lookahead pre-fetch queue (K=2) supporting Dual-Stage pre-fetching.
    
    Stage 1: Async LLM DocumentTransformer (Ollama Gemma 3 12B)
    Stage 2: Async SpeechProvider (Edge TTS)
    """

    def __init__(
        self,
        speech_provider: SpeechProvider,
        planner: Optional["SpeechPlanner"] = None,
        transformer: Optional[DocumentTransformer] = None,
        capacity: int = 2,
    ):
        self.speech_provider = speech_provider
        self.planner = planner
        self.transformer = transformer
        self.capacity = capacity
        self._cache: Dict[str, AudioChunk] = {}  # block_id -> AudioChunk
        self._tasks: Dict[str, asyncio.Task] = {}  # block_id -> asyncio.Task
        self._generation: int = 0
        self._llm_semaphore = asyncio.Semaphore(1)

    def set_generation(self, generation: int) -> None:
        """Sets active generation token and purges stale background tasks if changed."""
        if self._generation != generation:
            self.clear()
            self._generation = generation

    def has_chunk(self, block_id: str) -> bool:
        return block_id in self._cache

    def clear(self) -> None:
        """Cancels all active pre-fetch tasks and clears audio cache."""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()
        self._cache.clear()

    async def prefetch_block(
        self,
        block: DocumentBlock,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        generation: Optional[int] = None,
    ) -> None:
        """Launches background dual-stage pre-synthesis task for upcoming DocumentBlock."""
        target_gen = generation if generation is not None else self._generation
        if target_gen != self._generation:
            return

        block_id = block.block_id
        if block_id in self._cache or block_id in self._tasks:
            return

        if len(self._cache) >= self.capacity:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        task = asyncio.create_task(self._dual_stage_task(block, voice, rate, target_gen))
        self._tasks[block_id] = task

    async def prefetch(self, request: SpeechRequest, generation: Optional[int] = None) -> None:
        """Backwards compatible prefetch using pre-formed SpeechRequest."""
        target_gen = generation if generation is not None else self._generation
        if target_gen != self._generation:
            return

        block_id = request.block_id
        if block_id in self._cache or block_id in self._tasks:
            return

        if len(self._cache) >= self.capacity:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        task = asyncio.create_task(self._synthesize_direct_task(request, target_gen))
        self._tasks[block_id] = task

    async def _dual_stage_task(self, block: DocumentBlock, voice: str, rate: str, target_gen: int) -> None:
        try:
            spoken_text = ""
            if self.planner:
                async with self._llm_semaphore:
                    if target_gen != self._generation:
                        return
                    spoken_text = await self.planner.plan_block_async(block, self.transformer)
            if not spoken_text or not spoken_text.strip():
                return

            if target_gen != self._generation:
                return

            req = SpeechRequest(
                request_id=str(uuid.uuid4()),
                text=spoken_text,
                voice=voice,
                rate=rate,
                block_id=block.block_id,
            )

            chunk = await self.speech_provider.synthesize(req)
            if target_gen == self._generation:
                self._cache[block.block_id] = chunk
        except asyncio.CancelledError:
            pass
        except Exception as err:
            logger.warning(f"Background pre-fetch for block {block.block_id} failed ({err}). Will synthesize on-demand.")
        finally:
            self._tasks.pop(block.block_id, None)

    async def _synthesize_direct_task(self, request: SpeechRequest, target_gen: int) -> None:
        try:
            chunk = await self.speech_provider.synthesize(request)
            if target_gen == self._generation:
                self._cache[request.block_id] = chunk
        except asyncio.CancelledError:
            pass
        except Exception as err:
            logger.warning(f"Background pre-fetch for block {request.block_id} failed ({err}). Will synthesize on-demand.")
        finally:
            self._tasks.pop(request.block_id, None)

    async def get_chunk(
        self,
        request: SpeechRequest,
        generation: Optional[int] = None,
    ) -> AudioChunk:
        """Retrieves cached chunk or synthesizes immediately on cache miss."""
        target_gen = generation if generation is not None else self._generation

        block_id = request.block_id
        if block_id in self._cache:
            return self._cache.pop(block_id)

        if block_id in self._tasks:
            task = self._tasks.pop(block_id)
            try:
                await task
                if block_id in self._cache:
                    return self._cache.pop(block_id)
            except Exception:
                pass

        # Cache miss: synthesize directly
        return await self.speech_provider.synthesize(request)
