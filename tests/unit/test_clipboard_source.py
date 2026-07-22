import pytest
from PySide6.QtWidgets import QApplication
from copycat.sources.clipboard import ClipboardSource

@pytest.mark.asyncio
async def test_clipboard_source_success(qapp):
    clipboard = QApplication.clipboard()
    clipboard.setText("Copied test text from clipboard")

    source = ClipboardSource()
    snapshot = await source.capture()

    assert snapshot.raw_text == "Copied test text from clipboard"
    assert snapshot.source_id == "clipboard"

@pytest.mark.asyncio
async def test_clipboard_source_empty(qapp):
    clipboard = QApplication.clipboard()
    clipboard.clear()

    source = ClipboardSource()
    with pytest.raises(ValueError, match="empty or does not contain text"):
        await source.capture()
