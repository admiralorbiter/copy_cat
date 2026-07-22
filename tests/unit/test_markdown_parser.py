from pathlib import Path
from copycat.domain.models import BlockType, SourceSnapshot
from copycat.parsing.parser import MarkdownDocumentParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

def test_parse_antigravity_response_fixture():
    parser = MarkdownDocumentParser()
    fixture_path = FIXTURES_DIR / "antigravity_response.md"
    raw_text = fixture_path.read_text(encoding="utf-8")

    snapshot = SourceSnapshot(raw_text=raw_text)
    doc = parser.parse(snapshot)

    assert doc.title == "Antigravity Architecture Plan"
    assert len(doc.outline) == 2
    assert "Core Features" in doc.outline

    # Find code block
    code_blocks = [b for b in doc.blocks if b.block_type == BlockType.CODE]
    assert len(code_blocks) == 1
    assert code_blocks[0].language == "python"
    assert "extract_text" in code_blocks[0].text

def test_parse_chatgpt_response_fixture():
    parser = MarkdownDocumentParser()
    fixture_path = FIXTURES_DIR / "chatgpt_response.md"
    raw_text = fixture_path.read_text(encoding="utf-8")

    doc = parser.parse(SourceSnapshot(raw_text=raw_text))

    assert doc.title == "Recommendations"
    list_items = [b for b in doc.blocks if b.block_type == BlockType.LIST_ITEM]
    assert len(list_items) >= 4

def test_parse_malformed_markdown_fixture():
    parser = MarkdownDocumentParser()
    fixture_path = FIXTURES_DIR / "malformed_markdown.md"
    raw_text = fixture_path.read_text(encoding="utf-8")

    doc = parser.parse(SourceSnapshot(raw_text=raw_text))
    assert doc is not None
    assert len(doc.blocks) >= 1

def test_parse_unclosed_code_fences_fixture():
    parser = MarkdownDocumentParser()
    fixture_path = FIXTURES_DIR / "unclosed_code_fences.md"
    raw_text = fixture_path.read_text(encoding="utf-8")

    doc = parser.parse(SourceSnapshot(raw_text=raw_text))
    code_blocks = [b for b in doc.blocks if b.block_type == BlockType.CODE]
    assert len(code_blocks) == 1
    assert "print(x + y)" in code_blocks[0].text

def test_parse_nested_bullet_lists_fixture():
    parser = MarkdownDocumentParser()
    fixture_path = FIXTURES_DIR / "nested_bullet_lists.md"
    raw_text = fixture_path.read_text(encoding="utf-8")

    doc = parser.parse(SourceSnapshot(raw_text=raw_text))
    list_items = [b for b in doc.blocks if b.block_type == BlockType.LIST_ITEM]
    assert len(list_items) == 4
