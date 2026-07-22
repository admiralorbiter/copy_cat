# Copy Cat — Development Roadmap & Phase Breakdown

## Phase 0: Technical Spike (Disposable Prototype)

### Objectives
Verify basic interoperability of Python 3.12, PySide6 GUI, Edge TTS synthesis, and QtMultimedia (`QMediaPlayer`) audio output.

### Key Deliverables
- Minimal PySide6 main window with text input area.
- **Read** button triggering async Edge TTS synthesis.
- Audio playback via `PySide6.QtMultimedia.QMediaPlayer`.
- **Stop** button that halts playback cleanly.
- Unit tests covering basic pipeline setup (Happy path, empty text bad path, network error bad path, unusual characters edge case).

### Acceptance Criteria
- Paste text -> Press Read -> Hear Edge TTS voice -> Press Stop -> Clean audio cancellation without hanging threads or locked temporary audio files.

---

## Phase 1: Clipboard MVP

### Objectives
Build a stable, usable personal reader application consuming text from the Windows Clipboard.

### Key Deliverables
- `SourceSnapshot` creation from `QClipboard`.
- Markdown block detection using `markdown-it-py`.
- Settings window for Voice selection (`en-US-JennyNeural`, `en-US-GuyNeural`, etc.) and Speed control (`-50%` to `+100%`).
- Deterministic text normalization (removing raw URLs, handling code blocks).
- UI with current-block preview and settings persistence via `platformdirs` / Qt settings.
- Comprehensive test suite (>=70% coverage requirement).

---

## Phase 2: Auditory Document Engine

### Objectives
Transform basic read-aloud into a navigable auditory document.

### Key Deliverables
- `ReadableDocument` model & `ReadingSession` state machine.
- Semantic reading cursor (block index, sentence index, heading path).
- Bounded playback queue (pre-fetching 1–2 upcoming blocks).
- **Pause** and **Resume** maintaining precise semantic position.
- **Previous Block** and **Next Block** navigation.
- Real-time current-block visual text highlighting.

---

## Phase 3: Screen-Reader-Inspired Navigation

### Objectives
Enable rapid skimming and structural navigation of long documents.

### Key Deliverables
- Sentence-level movement (Next/Prev Sentence).
- Heading-level movement (Next/Prev Heading).
- Interactive Document Outline panel.
- **"Where am I?"** status query (announces current heading context & progress).
- Configurable verbosity profiles (`natural`, `literal`, `selective`).

---

## Phase 4: Convenience & Desktop Integration

### Objectives
Seamless global desktop interaction without manual app context switching.

### Key Deliverables
- System tray minimization and background operation.
- Windows global hotkey integration (`RegisterHotKey` / `WM_HOTKEY`).
- Selection auto-copy (`Ctrl+C` trigger) with clipboard preservation.
- Non-focus-stealth playback notification overlay.

---

## Phase 5: Direct Application Extraction

### Objectives
Extract responses directly from Antigravity and browsers without relying on clipboard.

### Key Deliverables
- Windows UI Automation (`TextPattern`) reader module.
- Dedicated Antigravity response adapter.
- Diagnostic visual element highlight showing extracted boundary.
- Fallback chain: UI Automation -> Selection -> Clipboard.

---

## Phase 6: Advanced Auditory Browsing

### Objectives
Intelligent reading assistance, local TTS, and advanced structural navigation.

### Key Deliverables
- Local offline TTS provider (e.g. Kokoro / Piper / Windows SAPI fallback).
- Gist / Executive summary reading modes.
- Structured table navigation.
