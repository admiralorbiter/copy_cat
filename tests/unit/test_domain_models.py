from datetime import datetime
from copycat.domain.models import (
    BlockType,
    PlaybackState,
    SourceSnapshot,
    DocumentBlock,
    ReadableDocument,
    SpeechRequest,
    AudioChunk,
)

def test_source_snapshot_defaults():
    snap = SourceSnapshot(raw_text="Hello world")
    assert snap.raw_text == "Hello world"
    assert snap.source_id == "clipboard"
    assert isinstance(snap.captured_at, datetime)

def test_document_block_creation():
    block = DocumentBlock(
        block_id="block-1",
        block_type=BlockType.PARAGRAPH,
        text="Sample paragraph",
    )
    assert block.block_id == "block-1"
    assert block.block_type == BlockType.PARAGRAPH
    assert block.text == "Sample paragraph"
    assert block.children == []

def test_readable_document_creation():
    snap = SourceSnapshot(raw_text="Hello")
    block = DocumentBlock(block_id="b1", block_type=BlockType.HEADING, text="Title")
    doc = ReadableDocument(
        document_id="doc-1",
        snapshot=snap,
        title="Doc Title",
        blocks=[block],
        outline=["Title"],
    )
    assert doc.document_id == "doc-1"
    assert doc.title == "Doc Title"
    assert len(doc.blocks) == 1

def test_speech_request_and_audio_chunk():
    req = SpeechRequest(request_id="r1", text="Read me")
    chunk = AudioChunk(chunk_id="c1", request_id="r1", audio_bytes=b"12345", duration_ms=100)
    assert req.request_id == "r1"
    assert chunk.request_id == "r1"
    assert chunk.audio_bytes == b"12345"
