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
    QComboBox,
    QStatusBar,
)
from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState
from copycat.services.settings_service import SettingsService, UserSettings, AVAILABLE_VOICES, AVAILABLE_RATES

class MainWindow(QMainWindow):
    """Phase 1 PySide6 MainWindow for Copy Cat."""

    def __init__(
        self,
        controller: MainController,
        settings_service: Optional[SettingsService] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.controller = controller
        self.settings_service = settings_service or SettingsService()
        self.setWindowTitle("Copy Cat — Auditory Document Reader")
        self.resize(700, 520)

        self._init_ui()
        self._load_saved_settings()
        self._connect_signals()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Settings Toolbar Layout
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("Voice:", self))
        self.voice_combo = QComboBox(self)
        for voice_id, label in AVAILABLE_VOICES:
            self.voice_combo.addItem(label, userData=voice_id)
        settings_layout.addWidget(self.voice_combo, stretch=2)

        settings_layout.addWidget(QLabel("Speed:", self))
        self.rate_combo = QComboBox(self)
        for rate in AVAILABLE_RATES:
            self.rate_combo.addItem(rate, userData=rate)
        settings_layout.addWidget(self.rate_combo, stretch=1)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # Text input preview area
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Paste clipboard or Markdown text here, or click 'Read Clipboard'...")
        layout.addWidget(self.text_edit)

        # Controls Layout
        controls_layout = QHBoxLayout()

        self.read_clipboard_button = QPushButton("Read Clipboard", self)
        self.read_clipboard_button.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 7px 16px;")
        controls_layout.addWidget(self.read_clipboard_button)

        self.read_button = QPushButton("Read Text", self)
        self.read_button.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 7px 16px;")
        controls_layout.addWidget(self.read_button)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 7px 16px;")
        controls_layout.addWidget(self.stop_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready", self)
        self.status_bar.addWidget(self.status_label)

    def _load_saved_settings(self) -> None:
        settings = self.settings_service.settings

        # Match voice
        idx = self.voice_combo.findData(settings.voice)
        if idx >= 0:
            self.voice_combo.setCurrentIndex(idx)

        # Match rate
        idx = self.rate_combo.findData(settings.rate)
        if idx >= 0:
            self.rate_combo.setCurrentIndex(idx)

    def get_selected_voice(self) -> str:
        return str(self.voice_combo.currentData() or "en-US-JennyNeural")

    def get_selected_rate(self) -> str:
        return str(self.rate_combo.currentData() or "+0%")

    def _save_current_settings(self) -> None:
        new_settings = UserSettings(
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
        )
        self.settings_service.save_settings(new_settings)

    def _connect_signals(self) -> None:
        self.read_button.clicked.connect(self._on_read_clicked)
        self.read_clipboard_button.clicked.connect(self._on_read_clipboard_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        self.voice_combo.currentIndexChanged.connect(self._save_current_settings)
        self.rate_combo.currentIndexChanged.connect(self._save_current_settings)

        self.controller.state_changed.connect(self._on_state_changed)
        self.controller.status_message_changed.connect(self.status_label.setText)

    @qasync.asyncSlot()
    async def _on_read_clicked(self) -> None:
        raw_text = self.text_edit.toPlainText()
        await self.controller.read_text(
            raw_text,
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
        )

    @qasync.asyncSlot()
    async def _on_read_clipboard_clicked(self) -> None:
        await self.controller.read_clipboard(
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
        )

    @Slot()
    def _on_stop_clicked(self) -> None:
        self.controller.stop()

    @Slot(object)
    def _on_state_changed(self, state: PlaybackState) -> None:
        if state in (PlaybackState.CAPTURING, PlaybackState.PARSING, PlaybackState.BUFFERING, PlaybackState.PLAYING):
            self.read_button.setEnabled(False)
            self.read_clipboard_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.read_button.setEnabled(True)
            self.read_clipboard_button.setEnabled(True)
            self.stop_button.setEnabled(True)
