import pytest
import asyncio
from copycat.domain.models import SpeechRequest
from copycat.services.prefetch_queue import BoundedPrefetchQueue
from tests.mocks.mock_speech_provider import MockSpeechProvider

@pytest.mark.asyncio
async def test_prefetch_queue_caching_and_capacity(event_loop):
    speech = MockSpeechProvider(delay=0.0)
    queue = BoundedPrefetchQueue(speech_provider=speech, capacity=2)

    req0 = SpeechRequest(request_id="r0", text="Block 0", block_id="b0")
    req1 = SpeechRequest(request_id="r1", text="Block 1", block_id="b1")
    req2 = SpeechRequest(request_id="r2", text="Block 2", block_id="b2")

    await queue.prefetch(req0)
    await queue.prefetch(req1)
    await asyncio.gather(*list(queue._tasks.values()))

    assert queue.has_chunk("b0") is True
    assert queue.has_chunk("b1") is True

    # Pre-fetch 3rd item exceeding capacity=2 -> should evict b0
    await queue.prefetch(req2)
    await asyncio.gather(*list(queue._tasks.values()))

    assert queue.has_chunk("b0") is False
    assert queue.has_chunk("b1") is True
    assert queue.has_chunk("b2") is True

    # Retrieve chunk
    chunk1 = await queue.get_chunk(req1)
    assert chunk1.block_id == "b1"
    assert queue.has_chunk("b1") is False

@pytest.mark.asyncio
async def test_prefetch_queue_cache_miss_and_clear(event_loop):
    speech = MockSpeechProvider(delay=0.0)
    queue = BoundedPrefetchQueue(speech_provider=speech, capacity=2)

    req0 = SpeechRequest(request_id="r0", text="Block 0", block_id="b0")

    # Cache miss should synthesize directly
    chunk0 = await queue.get_chunk(req0)
    assert chunk0.block_id == "b0"

    # Pre-fetch and clear
    await queue.prefetch(req0)
    queue.clear()
    assert queue.has_chunk("b0") is False

@pytest.mark.asyncio
async def test_prefetch_queue_generation_invalidation(event_loop):
    speech = MockSpeechProvider(delay=0.05)
    queue = BoundedPrefetchQueue(speech_provider=speech, capacity=2)

    req0 = SpeechRequest(request_id="r0", text="Block 0", block_id="b0")

    # Start pre-fetch on generation 0
    queue.set_generation(0)
    await queue.prefetch(req0)
    
    # Advance generation token mid-flight
    queue.set_generation(1)
    await asyncio.sleep(0.06)

    # Chunks from stale generation 0 should be discarded
    assert queue.has_chunk("b0") is False
