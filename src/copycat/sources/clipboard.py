import asyncio
from typing import Optional
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from copycat.domain.models import SourceSnapshot

class ClipboardSource(QObject):
    """Text source implementation for capturing raw text from the Windows Clipboard.
    
    Implements TextSource protocol structurally.
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    async def capture(self) -> SourceSnapshot:
        clipboard = QApplication.clipboard()
        if not clipboard:
            raise RuntimeError("QApplication clipboard is unavailable.")

        raw_text = ""
        # Retry up to 3 attempts with 50ms pause to handle transient Windows OpenClipboard locks
        for _ in range(3):
            raw_text = clipboard.text()
            if raw_text and raw_text.strip():
                break
            await asyncio.sleep(0.05)

        if not raw_text or not raw_text.strip():
            raise ValueError("Clipboard is empty or does not contain text.")

        return SourceSnapshot(
            raw_text=raw_text,
            source_application="Clipboard",
            source_id="clipboard",
        )
