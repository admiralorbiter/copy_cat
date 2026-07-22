# Copy Cat — Testing Strategy & Guidelines

## 1. Quality & Coverage Goals

Copy Cat relies on strict Test-Driven Development (TDD) and continuous testing alongside feature development.

### Core Metrics
- **Overall Minimum Coverage:** `>= 70%` total line/branch coverage enforced via `pytest-cov`.
- **Domain & Parsing Coverage Goal:** `>= 85%` statement/branch coverage.
- **Speech & Session State Machine Goal:** `>= 80%` statement/branch coverage.

---

## 2. Mandatory Test Requirement Matrix

For **every** function, module, or component implemented, the test suite MUST include:

| Test Type | Requirement | Examples |
|---|---|---|
| **Happy Path(s)** | Test standard expected operation and correct output. | Valid Markdown parsed into blocks; valid clipboard text converted to AudioChunk; Play -> Pause -> Resume transitions. |
| **Bad Path 1** | Invalid, empty, or corrupted input handling. | Empty clipboard; malformed/unclosed Markdown code fence; invalid rate string `+abc%`. |
| **Bad Path 2** | System failure, network loss, or resource errors. | Edge TTS network failure / connection timeout; QtMultimedia audio device unavailable; process termination during synthesis. |
| **Edge Cases** | Unusual, boundary, or rare inputs. | Text with 0 sentences; text with only emojis/Unicode math symbols; raw URLs only; 10,000-word single paragraph without punctuation. |

---

## 3. Module Test Matrix & Fixtures

### 3.1 Unit Testing Strategy (`tests/unit/`)

#### Document Parser (`tests/unit/test_parser.py`)
- **Happy Paths**: Standard Markdown (headings `#`, lists `-`, paragraphs, code ```).
- **Bad Path 1**: Empty string or whitespace-only input.
- **Bad Path 2**: Malformed Markdown (unclosed brackets `[link](`, mismatched formatting, raw HTML tags).
- **Edge Cases**: Only numbers; text containing special control characters (`\x00`, `\r`, `\t`); nested list items up to 5 levels deep.

#### Speech Planner & Normalizer (`tests/unit/test_speech_planner.py`)
- **Happy Paths**: Natural verbosity, URL stripping (`https://example.com` -> "link omitted"), snake_case expansion (`my_variable_name` -> "my variable name").
- **Bad Path 1**: Invalid `ReadingPolicy` configuration option passed.
- **Bad Path 2**: Unrecognized speech rate parameter format.
- **Edge Cases**: Text consisting strictly of punctuation `!...???`; long single identifier `a_b_c_d_e_f_g_h_i_j`.

#### Playback State Machine (`tests/unit/test_state_machine.py`)
- **Happy Paths**: IDLE -> CAPTURING -> PARSING -> BUFFERING -> PLAYING -> STOPPING -> IDLE.
- **Bad Path 1**: Triggering `Resume` when session is in `IDLE` state.
- **Bad Path 2**: Triggering `Play` when TTS synthesis raises `SYNTHESIS_FAILED`.
- **Edge Cases**: Rapid double-click on `Stop` or `Play/Pause`; calling `Skip Next` on the last block of a document.

### 3.2 Fixture Documents (`tests/fixtures/`)

We maintain standard test document fixtures:
- `antigravity_response.md`: Realistic Antigravity coding answer with Markdown, code snippets, and lists.
- `chatgpt_summary.md`: Standard conversational summary with bolding and bullet points.
- `code_heavy.md`: Document dominated by Python/C++ code blocks.
- `malformed.md`: Broken Markdown syntax, unclosed quotes, broken links.
- `urls_and_tables.md`: Table markdown and embedded URLs.

---

## 4. Test Execution & Automated Commands

### Running Tests Locally
```bash
# Run all tests with coverage report
pytest --cov=src/copycat --cov-report=term-missing

# Enforce minimum 70% coverage requirement
pytest --cov=src/copycat --cov-fail-under=70
```
