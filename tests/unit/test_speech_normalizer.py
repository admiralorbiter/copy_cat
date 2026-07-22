import pytest
from copycat.services.speech_normalizer import normalize_text

def test_normalize_text_happy_path():
    raw = "  Hello   world!  \n\nThis is   a   test.  "
    expected = "Hello world!\n\nThis is a test."
    assert normalize_text(raw) == expected

def test_normalize_text_empty_and_whitespace():
    assert normalize_text("") == ""
    assert normalize_text("   ") == ""
    assert normalize_text("\t\n  \r\n") == ""

def test_normalize_text_control_characters_and_null_bytes():
    raw = "Hello\x00 world\x07 with\x1f control\x7f chars!"
    cleaned = normalize_text(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\x1f" not in cleaned
    assert cleaned == "Hello world with control chars!"

def test_normalize_text_zero_width_spaces():
    raw = "\u200b\u200cZero width\u200d spaces\ufeff"
    cleaned = normalize_text(raw)
    assert cleaned == "Zero width spaces"

def test_normalize_text_emojis_tables_and_copied_ui_artifacts():
    copied_text = """Phase 1 (Clipboard MVP) Complete 🚀
Phase 1 development and testing are complete! All 40 test cases passed in 3.77 seconds with 89.58% overall code coverage.

Key Deliverables Implemented
markdown-it-py Document Parser (
parser.py
)
TOTAL PROJECT\t89.58%\t40 passed in 3.77s"""

    cleaned = normalize_text(copied_text)

    # Verify rocket emoji 🚀 is removed
    assert "🚀" not in cleaned
    # Verify broken UI link linebreaks are joined: Document Parser (parser.py)
    assert "Document Parser (parser.py)" in cleaned
    # Verify tab-separated columns convert cleanly
    assert "TOTAL PROJECT 89.58% 40 passed in 3.77s" in cleaned

def test_normalize_text_large_input_50k_chars():
    large_text = "Sample sentence with normal words. " * 1500
    assert len(large_text) > 50000
    cleaned = normalize_text(large_text)
    assert len(cleaned) > 0
    assert "Sample sentence" in cleaned
