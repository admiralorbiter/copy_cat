from typing import Optional
import qasync
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QStatusBar,
)
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState

class MainWindow(QMainWindow):
    """Phase 0 PySide6 MainWindow for Copy Cat."""

    def __init__(self, controller: MainController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Copy Cat — Auditory Reader (Phase 0 Spike)")
        self.resize(640, 480)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Title Label
        self.header_label = QLabel("Paste text below and click Read to synthesize speech:", self)
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.header_label)

        # Text input area
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Paste clipboard or document text here...")
        layout.addWidget(self.text_edit)

        # Controls layout
        controls_layout = QHBoxLayout()

        self.read_button = QPushButton("Read", self)
        self.read_button.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px;")
        controls_layout.addWidget(self.read_button)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 6px 16px;")
        controls_layout.addWidget(self.stop_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready", self)
        self.status_bar.addWidget(self.status_label)

    def _connect_signals(self) -> None:
        self.read_button.clicked.connect(self._on_read_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        self.controller.state_changed.connect(self._on_state_changed)
        self.controller.status_message_changed.connect(self.status_label.setText)

    @qasync.asyncSlot()
    async def _on_read_clicked(self) -> None:
        raw_text = self.text_edit.toPlainText()
        await self.controller.read_text(raw_text)

    @Slot()
    def _on_stop_clicked(self) -> None:
        self.controller.stop()

    @Slot(object)
    def _on_state_changed(self, state: PlaybackState) -> None:
        if state == PlaybackState.BUFFERING:
            self.read_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        elif state == PlaybackState.PLAYING:
            self.read_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.read_button.setEnabled(True)
            self.stop_button.setEnabled(True)
