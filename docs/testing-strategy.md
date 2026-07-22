# Copy Cat — Testing Strategy & Guidelines

## 1. Quality & Coverage Goals

Copy Cat relies on strict Test-Driven Development (TDD) and continuous testing alongside feature development.

### Core Metrics
- **Overall Minimum Coverage:** `>= 70%` total line/branch coverage enforced via `pytest-cov`.
- **Domain & Normalization Coverage Goal:** `>= 90%` statement/branch coverage.
- **Controller & State Machine Goal:** `>= 85%` statement/branch coverage.
- **UI & Presentation Goal:** `>= 75%` statement/branch coverage via `pytest-qt`.

---

## 2. Test Execution & Headless CI Environment Setup

### 2.1 Event Loop Integration (`qasync` + `pytest-qt`)
PySide6 operates on Qt's `QEventLoop` while `edge-tts` operates on Python `asyncio`. In tests, we utilize `qasync.QEventLoop` to integrate Qt events and async coroutines smoothly without deadlocks.

### 2.2 Hardware & Network Isolation (100% Offline Testing)
To enable fast, headless, offline automated test runs:
- **Headless Qt Platform:** `os.environ["QT_QPA_PLATFORM"] = "offscreen"` in `tests/conftest.py`.
- **Network Isolation:** Unit and UI tests use `MockSpeechProvider` (implementing `SpeechProvider` protocol) rather than hitting Microsoft Bing servers over WebSockets.
- **Audio Device Isolation:** Unit and UI tests use `MockAudioOutput` (implementing `AudioOutput` protocol) so test execution never fails on headless CI nodes missing physical sound cards.

---

## 3. Mandatory Test Requirement Matrix

For **every** function, module, or component implemented, the test suite MUST include:

| Test Type | Requirement | Phase 0 Concrete Examples |
|---|---|---|
| **Happy Path(s)** | Standard expected operation and correct output. | Valid input text -> Read clicked -> State transitions to PLAYING -> `MockAudioOutput` receives chunk -> Status label updated to "Playing". |
| **Bad Path 1** | Invalid, empty, or whitespace input handling. | Empty string `""` or `"   "` -> State transitions to `CAPTURE_FAILED` -> Error label shown -> Network synthesis skipped. |
| **Bad Path 2** | Network failure / Edge TTS exception. | `MockSpeechProvider` raises `RuntimeError` / `TimeoutError` -> State transitions to `SYNTHESIS_FAILED` -> User shown error banner -> App remains usable for retry. |
| **Bad Path 3** | Audio device hardware failure. | `MockAudioOutput` emits hardware error signal -> State transitions to `AUDIO_OUTPUT_FAILED` -> App safely handles error without crashing. |
| **Edge Case A** | Special symbols & control characters. | Text containing emojis `👋🐱‍👤`, null bytes `\x00`, math symbols `∀x ∈ ℝ`, or unescaped HTML tags cleaned by normalizer. |
| **Edge Case B** | Large input (50,000+ characters). | Very large string processed without UI thread freezing or high memory leaks. |
| **Edge Case C** | Rapid Stop button spamming. | Spamming Stop 10x rapidly during active synthesis cancels task cleanly and resets state to `IDLE` without tracebacks. |

---

## 4. Source Directory Structure for Clean Testability

```text
src/copycat/
├── domain/                  # Immutable Data Models & Enums (Pure Python, 100% Coverage Target)
│   ├── models.py
│   └── protocols.py         # Abstract Protocols (SpeechProvider, AudioOutput)
├── services/                # Concrete Hardware & Service Implementations
│   ├── edge_tts_provider.py
│   ├── qt_audio_output.py
│   └── speech_normalizer.py
├── controller/              # FSM Logic & qasync Workflow Orchestration
│   └── main_controller.py
└── ui/                      # PySide6 Presentation View Layer
    └── main_window.py
tests/
├── conftest.py              # Pytest fixtures, QApplication & qasync event loop setup
├── fixtures/                # Test text files & sample audio chunks
├── mocks/                   # Protocol Mocks (MockSpeechProvider, MockAudioOutput)
├── unit/                    # Unit tests for domain models, normalizer, FSM, services
└── ui/                      # UI / Integration tests using pytest-qt (qtbot)
```

---

## 5. Automated Test Commands

```bash
# Run all unit and UI tests with coverage report
pytest --cov=src/copycat --cov-report=term-missing

# Enforce minimum 70% coverage requirement
pytest --cov=src/copycat --cov-fail-under=70
```
