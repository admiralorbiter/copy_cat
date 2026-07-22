import pytest
from copycat.domain.models import BlockType, DocumentBlock
from copycat.services.ollama_transformer import OllamaTransformer
from tests.mocks.mock_ollama import MockOllamaTransport

@pytest.mark.asyncio
async def test_ollama_transformer_happy_path_code_summary(event_loop):
    transport = MockOllamaTransport(response_text="Python function that processes numbers.")
    transformer = OllamaTransformer(transport=transport)

    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.CODE,
        text="def add(x, y):\n    return x + y\n",
        language="python",
    )

    summary = await transformer.transform_block(block, mode="code_summary")
    assert summary == "AI summary: Python function that processes numbers."
    assert len(transport.requests) == 1

@pytest.mark.asyncio
async def test_ollama_transformer_mode_off_or_invalid(event_loop):
    transport = MockOllamaTransport()
    transformer = OllamaTransformer(transport=transport)

    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.PARAGRAPH,
        text="Normal paragraph text.",
    )

    # Mode 'off' returns None without hitting network
    assert await transformer.transform_block(block, mode="off") is None
    assert len(transport.requests) == 0

@pytest.mark.asyncio
async def test_ollama_transformer_bad_path_connection_refused(event_loop):
    transport = MockOllamaTransport(should_fail_connection=True)
    transformer = OllamaTransformer(transport=transport)

    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.CODE,
        text="def foo(): pass",
    )

    # Catches connection refusal and returns None for transparent fallback
    summary = await transformer.transform_block(block, mode="code_summary")
    assert summary is None

@pytest.mark.asyncio
async def test_ollama_transformer_bad_path_3s_timeout(event_loop):
    transport = MockOllamaTransport(should_timeout=True)
    transformer = OllamaTransformer(transport=transport)

    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.CODE,
        text="def foo(): pass",
    )

    # Catches timeout and returns None
    summary = await transformer.transform_block(block, mode="code_summary")
    assert summary is None

@pytest.mark.asyncio
async def test_ollama_transformer_health_check(event_loop):
    transport = MockOllamaTransport()
    transformer = OllamaTransformer(transport=transport)

    assert await transformer.check_health() is True
