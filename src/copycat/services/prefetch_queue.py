import asyncio
from typing import Dict, Optional
from copycat.domain.models import SpeechRequest, AudioChunk
from copycat.protocols.speech import SpeechProvider

class BoundedPrefetchQueue:
    """Bounded lookahead pre-fetch queue (K=2) for zero-latency block audio transitions.
    
    Validates generation tokens to prevent race conditions and memory leaks.
    """

    def __init__(self, speech_provider: SpeechProvider, capacity: int = 2):
        self.speech_provider = speech_provider
        self.capacity = capacity
        self._cache: Dict[str, AudioChunk] = {}  # block_id -> AudioChunk
        self._tasks: Dict[str, asyncio.Task] = {}  # block_id -> asyncio.Task
        self._generation: int = 0

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

    async def prefetch(self, request: SpeechRequest, generation: Optional[int] = None) -> None:
        """Launches background pre-synthesis task for upcoming request."""
        target_gen = generation if generation is not None else self._generation
        if target_gen != self._generation:
            return

        block_id = request.block_id
        if block_id in self._cache or block_id in self._tasks:
            return  # Already cached or in-flight

        # Enforce capacity limit by pruning oldest entry if needed
        if len(self._cache) >= self.capacity:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        task = asyncio.create_task(self._synthesize_task(request, target_gen))
        self._tasks[block_id] = task

    async def _synthesize_task(self, request: SpeechRequest, target_gen: int) -> None:
        try:
            chunk = await self.speech_provider.synthesize(request)
            if target_gen == self._generation:
                self._cache[request.block_id] = chunk
        except asyncio.CancelledError:
            pass
        except Exception:
            # Errors will be handled upon direct fetch if needed
            pass
        finally:
            self._tasks.pop(request.block_id, None)

    async def get_chunk(self, request: SpeechRequest, generation: Optional[int] = None) -> AudioChunk:
        """Retrieves cached chunk or synthesizes immediately on cache miss."""
        target_gen = generation if generation is not None else self._generation

        block_id = request.block_id
        if block_id in self._cache:
            return self._cache.pop(block_id)

        if block_id in self._tasks:
            task = self._tasks.pop(block_id)
            try:
                chunk = await task
                if chunk and target_gen == self._generation:
                    return chunk
            except Exception:
                pass

        # Cache miss: synthesize immediately
        return await self.speech_provider.synthesize(request)
