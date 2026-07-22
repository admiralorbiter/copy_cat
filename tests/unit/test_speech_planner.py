from copycat.domain.models import BlockType, DocumentBlock, SourceSnapshot, ReadingPolicy
from copycat.parsing.parser import MarkdownDocumentParser
from copycat.speech.planner import SpeechPlanner

def test_speech_planner_code_block_announce_and_skip():
    planner = SpeechPlanner(policy=ReadingPolicy(code_mode="announce_and_skip"))
    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.CODE,
        text="print('hello')\nfoo()\nbar()\n",
        language="python",
    )
    formatted = planner.format_block_text(block)
    assert formatted == "Python code block, 3 lines, skipped."

def test_speech_planner_code_block_omit():
    planner = SpeechPlanner(policy=ReadingPolicy(code_mode="omit"))
    block = DocumentBlock(
        block_id="b1",
        block_type=BlockType.CODE,
        text="print('hello')",
        language="python",
    )
    assert planner.format_block_text(block) == ""

def test_speech_planner_links_formatting():
    planner = SpeechPlanner(policy=ReadingPolicy(link_mode="text_only"))
    block = DocumentBlock(
        block_id="b2",
        block_type=BlockType.PARAGRAPH,
        text="Check [the documentation](https://example.com/docs) now.",
    )
    formatted = planner.format_block_text(block)
    assert formatted == "Check the documentation now."

def test_speech_planner_plan_document():
    parser = MarkdownDocumentParser()
    planner = SpeechPlanner()
    snapshot = SourceSnapshot(raw_text="# Overview\n\nThis is a test paragraph.\n\n```python\nx = 1\n```")

    doc = parser.parse(snapshot)
    requests = planner.plan_document(doc, voice="en-US-GuyNeural", rate="+25%")

    assert len(requests) == 3
    assert requests[0].text == "Overview."
    assert requests[0].voice == "en-US-GuyNeural"
    assert requests[0].rate == "+25%"
    assert requests[1].text == "This is a test paragraph."
    assert requests[2].text == "Python code block, 1 line, skipped."
