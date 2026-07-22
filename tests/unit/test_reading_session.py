from copycat.domain.models import (
    BlockType,
    DocumentBlock,
    ReadableDocument,
    SourceSnapshot,
    ReadingSession,
    ReadingPosition,
)

def _create_sample_doc():
    snapshot = SourceSnapshot(raw_text="Sample text")
    blocks = [
        DocumentBlock(block_id="b1", block_type=BlockType.HEADING, text="Title", level=1),
        DocumentBlock(block_id="b2", block_type=BlockType.PARAGRAPH, text="First paragraph text."),
        DocumentBlock(block_id="b3", block_type=BlockType.PARAGRAPH, text="Second paragraph text."),
    ]
    return ReadableDocument(
        document_id="doc1", snapshot=snapshot, title="Title", blocks=blocks
    )

def test_reading_session_initial_state():
    doc = _create_sample_doc()
    session = ReadingSession(document=doc)

    assert session.total_blocks == 3
    assert session.position.block_index == 0
    assert session.current_block == doc.blocks[0]
    assert session.can_skip_prev() is False
    assert session.can_skip_next() is True

def test_reading_session_navigation_next_and_prev():
    doc = _create_sample_doc()
    session = ReadingSession(document=doc)

    gen0 = session.generation

    # Skip next to Block 1
    b1 = session.skip_next()
    assert b1 == doc.blocks[1]
    assert session.position.block_index == 1
    assert session.generation > gen0

    gen1 = session.generation

    # Skip next to Block 2
    b2 = session.skip_next()
    assert b2 == doc.blocks[2]
    assert session.position.block_index == 2
    assert session.can_skip_next() is False
    assert session.generation > gen1

    # Attempt skip next at boundary -> None
    assert session.skip_next() is None
    assert session.position.block_index == 2

    # Skip prev back to Block 1
    prev_b1 = session.skip_prev()
    assert prev_b1 == doc.blocks[1]
    assert session.position.block_index == 1

def test_reading_session_seek_to_block():
    doc = _create_sample_doc()
    session = ReadingSession(document=doc)

    assert session.seek_to_block(2) == doc.blocks[2]
    assert session.position.block_index == 2

    # Invalid seek bounds
    assert session.seek_to_block(-1) is None
    assert session.seek_to_block(99) is None
    assert session.position.block_index == 2
