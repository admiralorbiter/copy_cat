import os
import sys
import pytest
import asyncio
from PySide6.QtWidgets import QApplication
import qasync

os.environ["QT_QPA_PLATFORM"] = "offscreen"

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def event_loop(qapp):
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
