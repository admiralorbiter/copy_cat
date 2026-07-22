from typing import Optional
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QStatusBar,
    QTextEdit,
)
import qasync

from copycat.controller.main_controller import MainController
from copycat.domain.models import PlaybackState, DocumentBlock
from copycat.services.settings_service import SettingsService, UserSettings

class MainWindow(QMainWindow):
    """Main application window featuring PySide6 UI controls, visual block highlighting, and AI Mode selector."""

    AVAILABLE_VOICES = [
        ("Jenny (US Female)", "en-US-JennyNeural"),
        ("Guy (US Male)", "en-US-GuyNeural"),
        ("Sonia (UK Female)", "en-GB-SoniaNeural"),
        ("Ryan (UK Male)", "en-GB-RyanNeural"),
        ("Natasha (AU Female)", "en-AU-NatashaNeural"),
    ]

    AVAILABLE_RATES = [
        ("-50%", "-50%"),
        ("-25%", "-25%"),
        ("Normal (+0%)", "+0%"),
        ("+25%", "+25%"),
        ("+50%", "+50%"),
        ("+75%", "+75%"),
        ("+100%", "+100%"),
    ]

    AVAILABLE_AI_MODES = [
        ("Off (Natural)", "off"),
        ("Code Explanation (Ollama)", "code_summary"),
        ("Data & Table Summary (Ollama)", "data_summary"),
        ("Section Gist (Gemma 3)", "gist"),
        ("Full Document Summary (Ollama)", "document_summary"),
    ]

    def __init__(
        self,
        controller: MainController,
        settings_service: Optional[SettingsService] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.controller = controller
        self.settings_service = settings_service or SettingsService()

        self.highlighted_block_index: int = -1

        self.setWindowTitle("Copy Cat — Auditory Document Reader (Phase 3.5 AI)")
        self.resize(780, 540)

        self._setup_ui()
        self._load_saved_settings()
        self._connect_signals()
        self._setup_shortcuts()
        self._check_ollama_health()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Configuration Bar (Row 1)
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        for label, val in self.AVAILABLE_VOICES:
            self.voice_combo.addItem(label, val)
        controls_layout.addWidget(self.voice_combo)

        controls_layout.addWidget(QLabel("Speed:"))
        self.rate_combo = QComboBox()
        for label, val in self.AVAILABLE_RATES:
            self.rate_combo.addItem(label, val)
        controls_layout.addWidget(self.rate_combo)

        controls_layout.addWidget(QLabel("AI Mode:"))
        self.ai_mode_combo = QComboBox()
        for label, val in self.AVAILABLE_AI_MODES:
            self.ai_mode_combo.addItem(label, val)
        controls_layout.addWidget(self.ai_mode_combo)

        layout.addLayout(controls_layout)

        # Main text preview editor using QPlainTextEdit
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Paste Markdown text here or click 'Read Clipboard'...")
        layout.addWidget(self.text_edit)

        # Playback Action Buttons Layout (Row 2)
        action_layout = QHBoxLayout()

        self.read_clipboard_button = QPushButton("📋 Read Clipboard")
        action_layout.addWidget(self.read_clipboard_button)

        self.read_button = QPushButton("▶ Read Text")
        action_layout.addWidget(self.read_button)

        self.prev_button = QPushButton("⏮ Prev Block")
        action_layout.addWidget(self.prev_button)

        self.pause_button = QPushButton("⏸ Pause")
        action_layout.addWidget(self.pause_button)

        self.next_button = QPushButton("⏭ Next Block")
        action_layout.addWidget(self.next_button)

        self.stop_button = QPushButton("⏹ Stop")
        action_layout.addWidget(self.stop_button)

        layout.addLayout(action_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Permanent Ollama Status Widget
        self.ollama_status_label = QLabel("⚪ Ollama: Checking...")
        self.status_bar.addPermanentWidget(self.ollama_status_label)

    def _setup_shortcuts(self) -> None:
        self.shortcut_prev = QShortcut(QKeySequence("Alt+Up"), self)
        self.shortcut_prev.activated.connect(self._on_prev_clicked)

        self.shortcut_next = QShortcut(QKeySequence("Alt+Down"), self)
        self.shortcut_next.activated.connect(self._on_next_clicked)

    def _load_saved_settings(self) -> None:
        saved = self.settings_service.settings
        voice_idx = self.voice_combo.findData(saved.voice)
        if voice_idx >= 0:
            self.voice_combo.setCurrentIndex(voice_idx)

        rate_idx = self.rate_combo.findData(saved.rate)
        if rate_idx >= 0:
            self.rate_combo.setCurrentIndex(rate_idx)

        ai_idx = self.ai_mode_combo.findData(saved.ai_mode)
        if ai_idx >= 0:
            self.ai_mode_combo.setCurrentIndex(ai_idx)

    def _save_current_settings(self) -> None:
        new_settings = UserSettings(
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
            ai_mode=self.get_selected_ai_mode(),
        )
        self.settings_service.save_settings(new_settings)

    def get_selected_voice(self) -> str:
        return self.voice_combo.currentData() or "en-US-JennyNeural"

    def get_selected_rate(self) -> str:
        return self.rate_combo.currentData() or "+0%"

    def get_selected_ai_mode(self) -> str:
        return self.ai_mode_combo.currentData() or "off"

    def _connect_signals(self) -> None:
        self.read_button.clicked.connect(self._on_read_text_clicked)
        self.read_clipboard_button.clicked.connect(self._on_read_clipboard_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.prev_button.clicked.connect(self._on_prev_clicked)
        self.next_button.clicked.connect(self._on_next_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        self.voice_combo.currentIndexChanged.connect(self._save_current_settings)
        self.rate_combo.currentIndexChanged.connect(self._save_current_settings)
        self.ai_mode_combo.currentIndexChanged.connect(self._on_ai_mode_changed)

        self.controller.state_changed.connect(self._on_state_changed)
        self.controller.status_message_changed.connect(self.status_label.setText)
        self.controller.block_changed.connect(self._on_block_changed)
        self.controller.transforming_block.connect(self._on_transforming_block)
        self.controller.boundary_reached.connect(self._on_boundary_reached)

    @Slot()
    @qasync.asyncSlot()
    async def _check_ollama_health(self) -> None:
        mode = self.get_selected_ai_mode()
        
        healthy = False
        if self.controller.transformer and hasattr(self.controller.transformer, "check_health"):
            healthy = await self.controller.transformer.check_health()

        if mode == "off":
            if healthy:
                self.ollama_status_label.setText("⚪ AI Mode: Off (Ollama Standby)")
            else:
                self.ollama_status_label.setText("⚪ AI Mode: Off")
        else:
            if healthy:
                self.ollama_status_label.setText("🟢 Ollama: Ready (gemma3:12b)")
            else:
                self.ollama_status_label.setText("🔴 Ollama: Offline (http://127.0.0.1:11434)")

    @Slot()
    def _on_ai_mode_changed(self) -> None:
        self._save_current_settings()
        self._check_ollama_health()

    @Slot()
    @qasync.asyncSlot()
    async def _on_read_text_clicked(self) -> None:
        text = self.text_edit.toPlainText()
        self._save_current_settings()
        await self.controller.read_text(
            text,
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
            ai_mode=self.get_selected_ai_mode(),
        )

    @Slot()
    @qasync.asyncSlot()
    async def _on_read_clipboard_clicked(self) -> None:
        self._save_current_settings()
        await self.controller.read_clipboard(
            voice=self.get_selected_voice(),
            rate=self.get_selected_rate(),
            ai_mode=self.get_selected_ai_mode(),
        )

    @Slot()
    def _on_pause_clicked(self) -> None:
        if self.controller.state == PlaybackState.PLAYING:
            self.controller.pause()
        elif self.controller.state == PlaybackState.PAUSED:
            self.controller.resume()

    @Slot()
    @qasync.asyncSlot()
    async def _on_prev_clicked(self) -> None:
        await self.controller.skip_prev()

    @Slot()
    @qasync.asyncSlot()
    async def _on_next_clicked(self) -> None:
        await self.controller.skip_next()

    @Slot()
    def _on_stop_clicked(self) -> None:
        self.controller.stop()
        self.clear_highlight()

    @Slot(int)
    def _on_transforming_block(self, current_1idx: int) -> None:
        """Visual highlight during LLM transformation phase in Soft Purple (#E1D5E7)."""
        self.ollama_status_label.setText("🟡 Ollama: Transforming block...")
        if self.controller.current_document and 0 <= current_1idx - 1 < len(self.controller.current_document.blocks):
            block = self.controller.current_document.blocks[current_1idx - 1]
            if block.source_start is not None and block.source_end is not None:
                self.highlight_range(block.source_start, block.source_end, color="#E1D5E7")

    @Slot(int, int, object)
    def _on_block_changed(self, current_1idx: int, total: int, block: DocumentBlock) -> None:
        """Visual highlight during TTS playback phase in Soft Blue (#D1E9FF)."""
        self.highlighted_block_index = current_1idx - 1
        if block and block.source_start is not None and block.source_end is not None:
            self.highlight_range(block.source_start, block.source_end, color="#D1E9FF")

    def highlight_range(self, start: int, end: int, color: str = "#D1E9FF") -> None:
        """Highlights character range [start, end] in the editor using QTextEdit.ExtraSelection."""
        doc = self.text_edit.document()
        if start < 0 or end > doc.characterCount():
            return

        cursor = QTextCursor(doc)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)

        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor

        fmt = QTextCharFormat()
        fmt.setBackground(QColor(color))
        selection.format = fmt

        self.text_edit.setExtraSelections([selection])

    def clear_highlight(self) -> None:
        self.highlighted_block_index = -1
        self.text_edit.setExtraSelections([])

    @Slot(str)
    def _on_boundary_reached(self, boundary: str) -> None:
        if boundary == "start":
            self.status_label.setText("Already at start of document.")
        elif boundary == "end":
            self.status_label.setText("Already at end of document.")

    @Slot(object)
    def _on_state_changed(self, state: PlaybackState) -> None:
        is_playing = state == PlaybackState.PLAYING
        is_paused = state == PlaybackState.PAUSED
        is_active = is_playing or is_paused

        self.pause_button.setEnabled(is_active)
        self.pause_button.setText("▶ Resume" if is_paused else "⏸ Pause")
        self.prev_button.setEnabled(is_active)
        self.next_button.setEnabled(is_active)
        self.stop_button.setEnabled(is_active or state == PlaybackState.BUFFERING)

        if state == PlaybackState.IDLE:
            self.clear_highlight()
            self._check_ollama_health()
        elif state == PlaybackState.PLAYING:
            self._check_ollama_health()
            if self.controller.current_document and 0 <= self.highlighted_block_index < len(self.controller.current_document.blocks):
                block = self.controller.current_document.blocks[self.highlighted_block_index]
                if block.source_start is not None and block.source_end is not None:
                    self.highlight_range(block.source_start, block.source_end, color="#D1E9FF")
