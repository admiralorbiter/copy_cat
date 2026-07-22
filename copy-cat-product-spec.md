# Copy Cat

## Product, Research, and Implementation Specification

**Status:** Working design specification  
**Version:** 0.1  
**Date:** July 21, 2026  
**Primary platform:** Windows  
**Initial implementation:** Python, PySide6, Edge TTS

---

## 1. Executive summary

**Copy Cat** is a Windows desktop application that turns selected or copied text from any application into a navigable, natural-sounding auditory document.

The immediate use case is simple:

1. Highlight or copy a long response in Antigravity, ChatGPT, a browser, a document, or another application.
2. Open Copy Cat or press a command.
3. Listen to the text using a high-quality Edge TTS voice.
4. Pause, repeat, skip, or stop without needing to keep reading visually.

The larger product is not merely a clipboard-to-speech wrapper. It is an **eyes-reduced document reader**: a tool for people who can use a screen and mouse but find sustained visual reading difficult, tiring, or inconvenient.

Copy Cat should preserve document structure, create a stable reading snapshot, maintain a semantic reading position, and support movement by sentence, paragraph, heading, list, code block, and eventually other content types. This direction draws heavily from research on auditory skimming and lessons learned from mature screen readers.

The first version will intentionally remain small:

- Windows desktop application
- Python and PySide6
- Edge TTS
- Read clipboard text
- Basic Markdown-aware parsing
- Paragraph-based playback
- Play, pause, stop, next, and previous controls
- Current-block highlighting
- Voice and speed settings

Later versions can add automatic selection capture, global hotkeys, a system tray, Windows UI Automation, Antigravity-specific extraction, auditory skimming modes, local TTS providers, and adaptive pacing.

---

## 2. Problem statement

Much modern knowledge work now involves generating and receiving long passages of text:

- AI-agent responses
- technical plans
- code reviews
- research summaries
- documentation
- email threads
- reports
- web articles
- Markdown knowledge bases

Short visual reading bursts are manageable, but sustained reading can be tiring. Existing Windows accessibility tools can often retrieve and speak on-screen text, but their voices and interaction patterns are not optimized for this use case. Browser readers sound better but do not work consistently across desktop applications. General screen readers are powerful, but they solve a broader problem and can introduce excessive interface narration, multiple modes, and a substantial learning curve.

The desired interaction is closer to:

> Select the useful text, press one button, and listen in a good voice. Retain enough structure and navigation to pause, recover, skip, and understand long responses.

---

## 3. Product definition

### 3.1 Core product

Copy Cat is a **tool-agnostic, eyes-reduced reading application** for Windows.

It captures text from another application, converts it into a structured internal document, plans how that document should be spoken, generates audio through a configurable speech provider, and gives the user direct control over playback and navigation.

### 3.2 Primary user

The initial user:

- works primarily on Windows;
- can navigate with a mouse and keyboard;
- can read visually in short bursts;
- prefers listening for longer passages;
- frequently uses Antigravity, ChatGPT, browsers, Markdown, documents, and technical tools;
- does not need a complete replacement for visual interaction;
- values natural speech more than exhaustive accessibility metadata;
- is comfortable copying or selecting text during the initial prototype.

### 3.3 Product category

Copy Cat is **not initially a full screen reader**.

A useful description is:

> A personal auditory document browser that sits between a basic read-aloud tool and a full screen reader.

### 3.4 Initial scope

The first usable version will:

- read plain text and Markdown-like text from the clipboard;
- recognize common structural elements;
- synthesize speech with Edge TTS;
- read one paragraph or short block at a time;
- display and highlight the current block;
- maintain a semantic reading cursor;
- allow the user to move forward and backward;
- preserve the original captured text;
- provide deterministic cleanup policies for code, links, and Markdown.

### 3.5 Explicit non-goals for the first version

The first version will not:

- replace NVDA, Narrator, or another full screen reader;
- automatically understand every desktop application;
- use OCR;
- read continuously changing AI output token by token;
- summarize or rewrite content with an LLM;
- provide full code or mathematics navigation;
- operate fully hands-free;
- support every operating system;
- package a local neural voice model;
- depend on an Antigravity plugin API.

---

## 4. Finalized decisions

### 4.1 Product and platform

- The product name is **Copy Cat**.
- It will begin as a **Windows desktop application**.
- It will be tool-agnostic rather than Antigravity-only.
- Antigravity is an important target application, but not the architectural center of the product.
- The first input method will be the **Windows clipboard**.
- Manual copy is acceptable for the prototype.
- Automatic selection capture will be added after the reading experience is validated.

### 4.2 Language and framework

- The initial language will be **Python**.
- The desktop UI will use **PySide6**, the official Qt bindings for Python.[R10]
- Flask will not be used for the initial application because this is a native tray-and-audio utility rather than a local web application.
- The architecture will use small interfaces so components can later be replaced or moved to Rust or another language if Windows integration or packaging warrants it.
- A Rust rewrite is not currently necessary.

### 4.3 Text-to-speech

- **Edge TTS** will be the initial speech provider.
- The `edge-tts` Python package provides access to Microsoft Edge's online speech service and supports use from Python without requiring an API key.[R9]
- Edge TTS is an online service; captured text may leave the local computer.
- A `SpeechProvider` interface will be created from the beginning so local or commercial providers can be added later.
- Potential later providers include Kokoro, Piper, Azure Speech, Windows SAPI, and other local models.
- Copy Cat will not be designed around Whisper because Whisper is speech-to-text, not text-to-speech.

### 4.4 Internal representation

- The application will not treat input as only one raw string.
- Every capture will create a stable **source snapshot**.
- The snapshot will be parsed into a structured **auditory document**.
- The auditory document will contain blocks such as headings, paragraphs, lists, code blocks, links, quotes, and tables.
- The original text will always be preserved.
- Deterministic transformations will never overwrite the source.

### 4.5 Playback

- The long-term playback model will synthesize sentence- or paragraph-sized chunks rather than one large audio file.
- A whole-passage audio file is acceptable only for an initial technical spike.
- Playback position will be stored semantically, not only as milliseconds into an audio file.
- The default reading unit will be a paragraph or short block.
- Sentence-level movement will be supported.
- The reader should continue playing when the user switches applications.
- The reader should not steal focus during playback.

### 4.6 Content policies

Initial defaults:

- **Headings:** speak naturally with a pause.
- **Paragraphs:** read normally.
- **Lists:** preserve item boundaries; avoid announcing excessive markup.
- **Code blocks:** announce language and approximate length, then skip.
- **Inline code:** convert identifiers into a more pronounceable form where practical.
- **Links:** read link text and omit raw URLs unless requested.
- **Tables:** announce that a table is present and provide a basic summary; structured table navigation comes later.
- **Markdown syntax:** remove syntax while retaining meaning.
- **Boilerplate and interface labels:** omit when confidently classified as non-content.
- **Dynamic updates:** do not interrupt playback by default.

### 4.7 User control

- Playback is manually initiated by default.
- New AI text will not automatically interrupt existing speech.
- Streaming AI output will not be read token by token.
- A future mode may start after a complete paragraph or after generation finishes, but it will be opt-in.
- A single obvious Stop action must always work.
- The reader will include a “Where am I?” capability later.

---

## 5. Research synthesis

## 5.1 Eyes-reduced reading

The most accurate research framing is **eyes-reduced reading**, not completely eyes-free computing.

Eyes-reduced systems allow the listener to combine audio with occasional glances, mouse interaction, and visual confirmation. The Skimmer research found that auditory reading benefits from non-linear navigation and auditory or haptic cues rather than relying only on continuous playback.[R1]

This aligns with Copy Cat's intended user:

- visual reading is available but costly over long periods;
- the mouse and screen remain useful;
- audio carries most long-form content;
- visual UI can show progress and structure without requiring continuous attention.

### Design consequence

Copy Cat should not imitate every behavior of a complete screen reader. It should use the visual channel strategically:

- highlight the current block;
- show the outline;
- display progress;
- expose large, clear controls;
- show what will be skipped;
- preserve the original text for quick visual checking.

---

## 5.2 Auditory skimming

SpeechSkimmer demonstrated that listening tools can support multiple levels of detail and interactive control over speed rather than requiring the user to hear everything linearly.[R2]

This introduces a major long-term distinction:

- **Playback speed** controls how quickly content is spoken.
- **Detail level** controls how much content is spoken.

These should remain separate.

### Future reading modes

- **Full:** read nearly all content.
- **Natural:** remove formatting noise but preserve content.
- **Structured:** emphasize headings, lists, and transitions.
- **Outline:** read headings and document shape.
- **Gist:** read or generate a concise representation of each section.
- **Actions:** focus on decisions, questions, tasks, and recommendations.
- **No code:** omit code while preserving explanations.
- **Changes:** read content added since an earlier snapshot.

The first three can be deterministic. Interpretive modes such as Gist or Actions may eventually use an LLM, but must be clearly distinguished from the source.

---

## 5.3 Screen-reader browse mode

Mature screen readers such as NVDA create a browsable representation of complex documents. Browse mode lets users move through headings, links, lists, tables, form fields, landmarks, and other structures without tying document review directly to application focus.[R3]

Copy Cat should borrow this concept without copying the full complexity.

### Copy Cat equivalent

A reading session should operate on a stable snapshot:

1. Capture source text.
2. Parse it into semantic blocks.
3. create an independent reading cursor;
4. let the user move through the snapshot;
5. refresh only when explicitly requested.

The reading cursor must be separate from:

- the source application's caret;
- the mouse;
- the source application's selection;
- the currently focused window;
- the generated audio timestamp.

---

## 5.4 Headings and landmarks

W3C guidance emphasizes headings as essential mechanisms for orientation and navigation, particularly for assistive-technology users.[R4] ARIA landmarks similarly identify major page regions.[R5]

### Design consequence

Headings must be first-class objects, not merely bold text.

Copy Cat should eventually provide:

- next and previous heading;
- current heading;
- outline view;
- jump to heading;
- heading path during resumption;
- optional heading-level announcements.

Example:

> Resuming in “Implementation Plan,” subsection “Phase Two: Auditory Document Engine.”

---

## 5.5 Accessible names are not always visible text

Screen readers use accessible names, roles, descriptions, values, and text patterns. W3C guidance warns that incorrect accessible naming can block or replace the information assistive technology receives.[R6]

When Copy Cat later uses Windows UI Automation, it cannot assume that one property is always the desired content.

An extracted element may provide:

- visible text;
- accessible name;
- accessible description;
- value;
- `TextPattern` content;
- child elements;
- role or control type.

The extraction layer should preserve these candidates. Source-specific policy can then decide which representation is authoritative.

---

## 5.6 Windows UI Automation

Microsoft UI Automation exposes text controls through `TextPattern`, representing content as a text stream with ranges and attributes.[R8] This is the likely foundation for reading directly from Antigravity and other desktop applications later.

Because Windows Magnifier can already speak Antigravity responses, there is practical evidence that Antigravity exposes at least some usable accessibility information. That does not guarantee clean message boundaries, but it makes UI Automation preferable to OCR as the first direct-extraction approach.

### Planned extraction priority

1. Explicit clipboard text
2. Automatic copy of selected text
3. UI Automation selection
4. UI Automation focused control
5. UI Automation text near the mouse
6. Application-specific extraction
7. OCR fallback only if necessary

Clipboard capture remains a permanent fallback even after richer extraction exists.

---

## 5.7 Dynamic content and interruption policy

ARIA live regions classify updates using levels such as `off`, `polite`, and `assertive`. Polite updates wait for an appropriate pause, while assertive updates may interrupt current speech and should be used sparingly.[R7]

Copy Cat should adopt a similar event policy.

### Silent events

- a background chunk finishes synthesis;
- the clipboard changes;
- a newer source version is available;
- a window changes focus;
- playback progress updates.

### Polite notifications

- end of document;
- a refresh is available;
- connection was lost but buffered audio remains;
- the queue is running low;
- a bookmark was saved.

### Interrupting events

- the user pressed Stop;
- audio output failed;
- the requested source disappeared before capture;
- a critical error prevents continued playback.

Normal application events should not interrupt spoken content.

---

## 5.8 Tables

Tables are inherently two-dimensional. W3C guidance notes that screen readers preserve context by associating each cell with its row and column headers.[R11]

Flattening a table into plain text destroys these relationships.

The document model should therefore preserve:

- caption or title;
- headers;
- rows;
- columns;
- cell coordinates;
- header relationships.

Initial behavior can remain simple:

> Table: four columns and eight data rows. Columns are task, owner, status, and deadline. Table skipped.

Later modes can provide:

- row reading;
- column reading;
- cell navigation;
- table summary;
- header-aware movement.

---

## 5.9 Long-form voice quality

Long-form TTS should be evaluated differently from isolated demo sentences. Research comparing sentence and paragraph evaluation found that judgments can change when a voice is heard in longer context.[R12] Other work specifically evaluates whether voices remain pleasant, clear, and comprehensible over several minutes.[R13]

### Design consequence

Voice selection should be tested using actual Copy Cat material:

- a normal AI response;
- a bulleted plan;
- technical documentation;
- acronyms and file names;
- at least one five- to ten-minute passage.

Evaluation should record:

- listening comfort;
- clarity;
- attention drift;
- pronunciation failures;
- comfortable speed;
- paragraph-boundary clarity.

A voice that sounds impressive for ten seconds may become tiring during a long response.

---

## 6. Design principles

### 6.1 Structure before speech

Capture and parse the document before deciding how to speak it.

### 6.2 Source fidelity

Always retain the original captured text. Transformations must be inspectable and reversible.

### 6.3 Semantic position

Track location by document block and sentence, not only by audio time.

### 6.4 User-controlled interruption

Background events should rarely interrupt speech.

### 6.5 Natural by default

Do not announce accessibility jargon, control roles, punctuation, or formatting unless it improves understanding.

### 6.6 Navigation is a core feature

Continuous read-aloud is necessary but insufficient. Users must be able to recover, repeat, skip, and orient themselves.

### 6.7 Stable snapshots

A reading session should not mutate simply because the source application changes.

### 6.8 Deterministic core

The trusted core should use deterministic parsing and speech rules. LLM-assisted summarization should be optional and visibly labeled.

### 6.9 Provider independence

Edge TTS is the first provider, not the permanent architecture.

### 6.10 Progressive integration

Begin with the clipboard. Add automatic copy and UI Automation only after the auditory document experience works.

---

## 7. Core user workflows

## 7.1 MVP workflow

1. User highlights text in Antigravity, ChatGPT, a browser, or another application.
2. User copies it.
3. User opens Copy Cat.
4. Copy Cat previews the clipboard text.
5. User presses **Read**.
6. Copy Cat parses the text and begins reading the first block.
7. The current block is highlighted.
8. User can pause, stop, move forward, or move backward.

## 7.2 Near-term hotkey workflow

1. User highlights text.
2. User presses the Copy Cat global hotkey.
3. Copy Cat preserves the existing clipboard.
4. Copy Cat issues Copy.
5. Copy Cat captures the selected text.
6. Copy Cat restores the prior clipboard where practical.
7. Playback begins.

Windows provides `RegisterHotKey` and the `WM_HOTKEY` message for application-level global shortcuts.[R14]

## 7.3 Future direct-reading workflow

1. User places the cursor over or focuses an Antigravity response.
2. User presses **Read Current Response**.
3. Copy Cat asks the Antigravity adapter to find the nearest assistant-message container through UI Automation.
4. The response is captured as a stable snapshot.
5. Copy Cat parses and reads it.

## 7.4 Resume workflow

1. User pauses or stops.
2. The semantic cursor is retained.
3. On resume, Copy Cat optionally:
   - announces the current heading;
   - replays the previous sentence;
   - continues from the current paragraph.

---

## 8. Proposed architecture

```text
Source adapters
    Clipboard
    Automatic copy
    Windows UI Automation
    Antigravity
    Browser
          |
          v
Source snapshot
    Raw text
    Source application
    Capture timestamp
    Source identity
    Optional accessibility metadata
          |
          v
Document parser
    Headings
    Paragraphs
    Lists
    Code blocks
    Quotes
    Links
    Tables
          |
          v
Auditory document
    Stable semantic blocks
    Source mappings
    Outline
          |
          v
Reading session
    Virtual reading cursor
    History
    Bookmarks
    Current context
          |
          v
Speech planner
    Verbosity policy
    Code policy
    Link policy
    Pronunciation rules
    Chunk boundaries
          |
          v
TTS provider
    Edge TTS initially
    Local and commercial providers later
          |
          v
Playback scheduler
    Ordered queue
    Buffering
    Pause and resume
    Skip
    Cancellation
          |
          v
PySide6 interface
    Main window
    Tray
    Hotkeys
    Progress
    Outline
```

---

## 9. Core domain models

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol


class BlockType(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    CODE = "code"
    QUOTE = "quote"
    LINK = "link"
    TABLE = "table"
    METADATA = "metadata"
    BOILERPLATE = "boilerplate"


@dataclass(frozen=True)
class SourceSnapshot:
    raw_text: str
    source_application: str | None
    captured_at: datetime
    source_id: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class DocumentBlock:
    block_id: str
    block_type: BlockType
    text: str
    level: int | None = None
    language: str | None = None
    children: list["DocumentBlock"] = field(default_factory=list)
    source_start: int | None = None
    source_end: int | None = None


@dataclass
class ReadableDocument:
    document_id: str
    snapshot: SourceSnapshot
    title: str | None
    blocks: list[DocumentBlock]
    outline: list[str]


@dataclass
class ReadingPosition:
    block_index: int = 0
    sentence_index: int = 0
    heading_path: list[str] = field(default_factory=list)


@dataclass
class ReadingSession:
    document: ReadableDocument
    position: ReadingPosition
    voice: str
    rate: str
    is_paused: bool = False
```

### Provider interfaces

```python
class TextSource(Protocol):
    async def capture(self) -> SourceSnapshot:
        ...


class DocumentParser(Protocol):
    def parse(self, snapshot: SourceSnapshot) -> ReadableDocument:
        ...


class SpeechProvider(Protocol):
    async def synthesize(self, request: "SpeechRequest") -> "AudioChunk":
        ...


class AudioOutput(Protocol):
    async def play(self, chunk: "AudioChunk") -> None:
        ...

    def pause(self) -> None:
        ...

    def resume(self) -> None:
        ...

    def stop(self) -> None:
        ...
```

---

## 10. Playback state machine

Playback should use an explicit state machine.

```text
IDLE
  |
  v
CAPTURING
  |
  v
PARSING
  |
  v
BUFFERING
  |
  v
PLAYING <------> PAUSED
  |                 |
  v                 |
STOPPING ------------ 
  |
  v
IDLE
```

Error states may include:

- `CAPTURE_FAILED`
- `PARSE_FAILED`
- `SYNTHESIS_FAILED`
- `NETWORK_UNAVAILABLE`
- `AUDIO_OUTPUT_FAILED`

### State rules

- Only one reading session may own the audio output.
- Stop cancels current playback and queued synthesis.
- Pause prevents playback but may permit limited buffering.
- A new Read command should either replace the current session or require an explicit queue policy.
- State transitions should be logged for debugging.
- UI buttons should derive enabled states from the playback state rather than managing their own independent logic.

---

## 11. Producer-consumer pipeline

The mature playback system should use a bounded queue.

```text
Document blocks
      |
      v
Speech planner
      |
      v
Synthesis request queue
      |
      v
Edge TTS worker
      |
      v
Ordered audio buffer
      |
      v
Audio output
```

### Why bounded queues matter

Copy Cat should not synthesize an entire thirty-minute document when the user may stop after one minute.

Suggested behavior:

- synthesize the current block;
- buffer one or two upcoming blocks;
- stop producing when the queue reaches its limit;
- cancel pending work immediately on Stop;
- discard or cache chunks according to a defined policy.

---

## 12. Chunking strategy

Chunk size creates a tradeoff:

- smaller chunks improve responsiveness and navigation;
- larger chunks may produce smoother prosody;
- very small chunks sound fragmented;
- very large chunks are harder to cancel or regenerate.

A conceptual optimization objective is:

\[
\max_C \left(
\alpha \cdot \text{coherence}(C)
+ \beta \cdot \text{structural completeness}(C)
- \gamma \cdot \text{startup latency}(C)
- \delta \cdot \text{navigation cost}(C)
\right)
\]

Initial rule-based hierarchy:

1. Split at headings.
2. Split at paragraph boundaries.
3. Split long paragraphs at sentence boundaries.
4. Keep list items distinct.
5. Never merge code with surrounding prose.
6. Merge extremely short neighboring prose sentences.
7. Target roughly 5–25 seconds of speech per chunk.
8. Preserve source block and sentence identifiers in every chunk.

---

## 13. Speech planning and text normalization

The speech planner converts document blocks into speakable chunks.

### 13.1 Deterministic transformations

Examples:

- Remove Markdown heading markers while retaining the heading.
- Convert repeated blank lines into one structural pause.
- Convert bullet markers into item boundaries.
- Remove raw URL destinations.
- Replace code blocks with a description.
- Convert snake_case and kebab-case into spaced words where useful.
- Expand a small configurable dictionary of technical abbreviations.
- Normalize dates and punctuation carefully.
- Avoid speaking decorative Unicode characters.
- Preserve numbers, units, and meaningful symbols.

### 13.2 Example

Source:

```markdown
## Recommended architecture

Use `TextPattern` to retrieve the response.

```python
element.get_current_pattern(...)
```

See https://example.com/docs.
```

Default spoken form:

> Recommended architecture. Use Text Pattern to retrieve the response. Python code block, one line, skipped. Documentation link omitted.

### 13.3 Policy object

```python
@dataclass
class ReadingPolicy:
    verbosity: str = "natural"
    code_mode: str = "announce_and_skip"
    link_mode: str = "text_only"
    table_mode: str = "summary"
    announce_heading_levels: bool = False
    announce_list_positions: bool = False
    repeat_context_on_resume: bool = True
```

---

## 14. User interface

## 14.1 Initial window

```text
+--------------------------------------------------+
| Copy Cat                                         |
+--------------------------------------------------+
| Source: Clipboard                                |
| Voice: [Jenny Neural             v]              |
| Speed: [ +10%                    v]              |
|                                                  |
| [ Read ] [ Pause ] [ Stop ] [ Previous ] [ Next ]|
|                                                  |
| Progress: Paragraph 3 of 12                      |
| Section: Architecture > Text Extraction          |
|                                                  |
| Current text:                                    |
| ------------------------------------------------ |
| The current paragraph appears here and is        |
| highlighted while it is spoken.                  |
| ------------------------------------------------ |
|                                                  |
| [ ] Read code     [x] Omit raw URLs              |
+--------------------------------------------------+
```

### Initial controls

- Read Clipboard
- Pause or Resume
- Stop
- Previous block
- Next block
- Voice
- Speed
- Text preview
- Current position
- Code preference
- Link preference

### Later interface elements

- System tray
- Global hotkey settings
- Document outline
- Heading navigation
- Bookmarks
- Reading history
- Source refresh
- “Where am I?”
- Provider selection
- Online-service privacy indicator
- Extraction diagnostics

---

## 15. Suggested commands

### Initial application commands

| Action | Initial control |
|---|---|
| Read clipboard | Button |
| Pause or resume | Button / Space when app focused |
| Stop | Button / Escape when app focused |
| Previous block | Button |
| Next block | Button |
| Change voice | Dropdown |
| Change rate | Dropdown or slider |

### Later global commands

| Action | Suggested default |
|---|---|
| Capture selection and read | `Ctrl+Alt+Space` |
| Pause or resume | `Ctrl+Alt+P` |
| Stop | `Ctrl+Alt+Escape` |
| Previous sentence | `Ctrl+Alt+Left` |
| Next sentence | `Ctrl+Alt+Right` |
| Previous heading | Configurable |
| Next heading | Configurable |
| Where am I? | Configurable |

Hotkeys must be configurable because system-wide combinations can conflict with other applications.

---

## 16. Implementation plan

## Phase 0: Technical spike

### Goal

Confirm that Python, PySide6, Edge TTS, and audio playback work together.

### Deliverables

- minimal PySide6 window;
- text box;
- Read button;
- Stop button;
- hard-coded Edge TTS voice;
- temporary MP3 generation;
- audio playback;
- basic exception reporting.

### Acceptance criteria

- paste text into the app;
- press Read;
- hear Edge TTS;
- press Stop;
- close without leaving orphaned processes or locked files.

### Important constraint

This phase may synthesize the whole passage. That implementation should be treated as disposable.

---

## Phase 1: Clipboard MVP

### Goal

Create a useful personal tool for copied text.

### Deliverables

- read current clipboard text;
- preserve raw source snapshot;
- voice selection;
- speed selection;
- basic Markdown cleanup;
- detect paragraphs, headings, lists, links, and fenced code;
- current-block preview;
- settings saved locally;
- clear error states;
- Windows executable packaging experiment.

### Acceptance criteria

- copy an Antigravity response;
- open Copy Cat;
- press Read;
- hear a clean, understandable version;
- code is announced and skipped;
- URLs are not read verbatim;
- settings survive restart.

---

## Phase 2: Auditory document engine

### Goal

Move from “speak a string” to a navigable document.

### Deliverables

- `ReadableDocument` model;
- block parser;
- sentence segmentation;
- semantic reading cursor;
- paragraph-based synthesis;
- bounded playback queue;
- pause and resume;
- previous and next block;
- correct Stop cancellation;
- heading path tracking;
- current-block highlighting.

### Acceptance criteria

- playback starts after the first chunk is ready;
- next and previous move predictably;
- pause retains semantic position;
- changing voice or speed does not lose the current block;
- Stop prevents queued chunks from playing;
- long text does not require complete pre-generation.

---

## Phase 3: Screen-reader-inspired navigation

### Goal

Make long responses browsable rather than merely playable.

### Deliverables

- next and previous sentence;
- next and previous heading;
- outline view;
- “Where am I?”;
- resume with heading plus previous sentence;
- verbosity profiles;
- bookmarks;
- list-item navigation;
- optional structural earcons;
- document progress.

### Acceptance criteria

- user can find a section without hearing the full document;
- user can recover after an interruption;
- structural announcements are useful but not noisy;
- outline and cursor stay synchronized.

---

## Phase 4: Convenience and desktop integration

### Goal

Remove the need to open the app and manually press Copy.

### Deliverables

- system tray;
- launch at startup;
- global hotkeys;
- automatic copy of selected text;
- clipboard preservation and restoration where reliable;
- compact playback overlay;
- source application metadata.

### Acceptance criteria

- highlight text in an arbitrary application;
- press one hotkey;
- playback begins;
- the prior clipboard is not unnecessarily destroyed;
- Copy Cat does not steal focus.

---

## Phase 5: Direct application extraction

### Goal

Read content without requiring selection.

### Deliverables

- UI Automation inspection utility;
- `TextPattern` extraction;
- focused-control extraction;
- text-near-pointer extraction;
- extraction candidate model;
- Antigravity adapter;
- browser adapter;
- diagnostics showing which accessibility properties were used;
- clipboard fallback.

### Acceptance criteria

- Copy Cat can capture a complete Antigravity response in common cases;
- buttons and surrounding interface labels are excluded;
- a failed extractor falls back gracefully;
- source changes do not mutate an active snapshot.

---

## Phase 6: Advanced auditory browsing

### Potential features

- full, structured, outline, and gist modes;
- action-item mode;
- code summaries;
- table navigation;
- mathematics-aware speech;
- pronunciation dictionaries;
- user-defined text substitutions;
- adaptive speech rate by content complexity;
- reading-history search;
- source version comparison;
- local TTS provider;
- optional LLM-assisted spoken transformation.

---

## 17. Initial repository structure

```text
copy-cat/
├── README.md
├── pyproject.toml
├── src/
│   └── copycat/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── logging_config.py
│       ├── domain/
│       │   ├── documents.py
│       │   ├── playback.py
│       │   ├── policies.py
│       │   └── speech.py
│       ├── sources/
│       │   ├── base.py
│       │   └── clipboard.py
│       ├── parsing/
│       │   ├── parser.py
│       │   ├── markdown_blocks.py
│       │   └── sentences.py
│       ├── speech/
│       │   ├── provider.py
│       │   ├── edge_provider.py
│       │   ├── planner.py
│       │   └── normalization.py
│       ├── audio/
│       │   ├── output.py
│       │   ├── queue.py
│       │   └── cache.py
│       ├── sessions/
│       │   ├── reading_session.py
│       │   └── state_machine.py
│       └── ui/
│           ├── main_window.py
│           ├── view_models.py
│           └── resources/
├── tests/
│   ├── parsing/
│   ├── speech/
│   ├── sessions/
│   └── fixtures/
└── docs/
    ├── product-spec.md
    ├── architecture.md
    └── research-notes.md
```

The MVP can begin with fewer files, but domain logic should not be placed directly in button handlers.

---

## 18. Initial dependency candidates

The exact audio library should be validated during Phase 0.

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "PySide6",
    "edge-tts",
    "platformdirs",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
    "mypy",
]
```

Potential additions:

- `miniaudio` or another playback library;
- `markdown-it-py` for Markdown parsing;
- `pywin32` for Windows APIs;
- `platformdirs` for settings and cache locations;
- `pydantic` only if configuration validation becomes complex;
- `pyinstaller` or `nuitka` for packaging.

Avoid adding dependencies until their role is clear.

---

## 19. Testing strategy

## 19.1 Unit tests

Test:

- Markdown block detection;
- sentence segmentation;
- URL removal;
- code-block policies;
- list handling;
- identifier pronunciation;
- reading cursor movement;
- state transitions;
- cancellation behavior;
- chunk ordering;
- provider failures.

## 19.2 Fixture documents

Maintain representative samples:

- Antigravity response;
- ChatGPT response;
- technical README;
- nested bullet list;
- code-heavy answer;
- table-heavy answer;
- research summary;
- email thread;
- malformed Markdown;
- very long paragraph;
- abbreviations and acronyms.

## 19.3 Listening tests

Evaluate with real passages rather than synthetic demo sentences.

Record:

- time to first audio;
- listening comfort after five and ten minutes;
- pronunciation errors;
- number of skips;
- number of rewinds;
- attention loss;
- preferred speed;
- success resuming after interruption;
- whether structure was clear.

## 19.4 Usability questions

- Can the user start playback without thinking?
- Does Stop always work?
- Is the current location obvious?
- Are headings helpful or intrusive?
- Does skipped code create confusion?
- Is paragraph navigation enough?
- Is the voice pleasant for long sessions?
- Does the application improve completion of long responses?

---

## 20. Risks and mitigations

### Edge TTS availability

**Risk:** The package relies on an online service that could change.

**Mitigation:** Use a provider interface; add a local fallback later.

### Privacy

**Risk:** Sensitive text may be transmitted to an online speech service.

**Mitigation:** Display an online-provider indicator, document the behavior, and add a local provider.

### Audio latency

**Risk:** Long text may take too long before playback begins.

**Mitigation:** Paragraph chunking, bounded prefetch, and early playback.

### Poor segmentation

**Risk:** Technical text may be split awkwardly.

**Mitigation:** Structural parsing before sentence splitting and a fixture-based test suite.

### Excessive narration

**Risk:** Screen-reader-inspired structure could make Copy Cat noisy.

**Mitigation:** Natural defaults, verbosity profiles, and visual status rather than spoken status.

### Application inconsistency

**Risk:** UI Automation exposes different information in different applications.

**Mitigation:** Preserve multiple candidate properties, use source adapters, and keep clipboard fallback.

### Scope expansion

**Risk:** The project drifts into building a complete screen reader.

**Mitigation:** Keep the product centered on captured content and eyes-reduced reading.

### Packaging complexity

**Risk:** Qt, audio codecs, and asynchronous TTS can complicate distribution.

**Mitigation:** Validate packaging in Phase 1 rather than after the application is large.

---

## 21. Open product questions

These questions do not block Phase 0, but should be tracked.

### 21.1 Transformation level

How much should Copy Cat change text before speaking it?

Recommended model:

1. **Literal:** minimal normalization.
2. **Natural:** remove formatting noise.
3. **Selective:** omit code, raw URLs, metadata, and boilerplate.
4. **Interpretive:** summarize or rewrite using an LLM.

Levels 1–3 should be deterministic. Level 4 must be explicit and labeled.

### 21.2 Default reading unit

Current recommendation:

- paragraph-sized synthesis;
- sentence-level navigation;
- block-level visual highlighting.

This should be validated through actual use.

### 21.3 Pause behavior

Options:

- pause audio immediately and preserve queued chunks;
- pause and suspend further synthesis;
- pause audio but continue buffering.

Current recommendation: pause playback, permit only limited prefetch, and preserve semantic position.

### 21.4 New reading request during playback

Options:

- replace current document;
- queue new document;
- ask;
- create tabs or history.

Current recommendation for MVP: replace after a brief confirmation only when unsaved position would be lost; otherwise retain prior sessions in history later.

### 21.5 Code behavior

Current recommendation: announce and skip by default.

Later options:

- read line by line;
- read identifiers only;
- summarize;
- copy;
- open externally.

### 21.6 Online-service privacy

Should Copy Cat detect potentially sensitive content or rely on explicit provider choice?

Current recommendation: clear provider indicator and user-controlled local mode later; do not attempt unreliable automatic sensitivity classification initially.

### 21.7 Source freshness

Should Copy Cat automatically refresh a changing Antigravity response?

Current recommendation: no. Notify that a newer version exists and let the user refresh explicitly.

### 21.8 Learning behavior

Should Copy Cat learn preferences automatically?

Current recommendation: begin with explicit settings and usage logs. Consider adaptive behavior only after enough data exists and only with transparent controls.

---

## 22. Future mathematical and adaptive models

These are research directions, not MVP requirements.

### 22.1 Difficulty-sensitive rate

A transparent difficulty score could use:

\[
D = w_1L_s + w_2L_w + w_3N + w_4C + w_5S
\]

Where:

- \(L_s\): sentence length;
- \(L_w\): word complexity;
- \(N\): numeric density;
- \(C\): code and symbol density;
- \(S\): syntactic-complexity proxy.

Speech rate:

\[
r = \operatorname{clamp}(r_0 - kD,\ r_{\min},\ r_{\max})
\]

This could slow dense technical passages and speed familiar boilerplate.

### 22.2 Contextual-bandit personalization

A much later version could choose reading policies based on:

- application;
- content type;
- time of day;
- length;
- code density;
- previous rewinds;
- completion behavior.

Actions might include:

- rate;
- chunk size;
- voice;
- verbosity;
- code policy;
- pause length.

This should not be implemented before stable explicit controls and meaningful usage data exist.

### 22.3 Reading-session metrics

Potential metrics:

- completion rate;
- early-stop rate;
- rewinds per thousand words;
- speed changes;
- average uninterrupted listening duration;
- resume success;
- time to first audio;
- extraction success by application.

These metrics should support personal improvement and product debugging, not become intrusive surveillance.

---

## 23. Recommended immediate work sequence

1. Create the repository and Python environment.
2. Build the smallest PySide6 window.
3. Integrate Edge TTS with a hard-coded voice.
4. Validate Stop and application shutdown.
5. Read text directly from `QClipboard`.
6. Add voice and speed settings.
7. Create `SourceSnapshot`.
8. Implement a minimal block parser.
9. Display parsed blocks.
10. Add paragraph-by-paragraph playback.
11. Implement the semantic reading cursor.
12. Add Previous and Next.
13. Add settings persistence.
14. Test with five real Antigravity responses.
15. Revise the parser and speech policies based on listening experience.
16. Only then add global hotkeys and automatic copy.

### First milestone definition

The first milestone is complete when:

> A copied Antigravity response can be opened in Copy Cat, read aloud in a pleasant Edge voice, stopped reliably, and navigated paragraph by paragraph without losing the original text.

---

## 24. Research references

- **[R1]** [Designing an Eyes-Reduced Document Skimming App for Situational Impairments](https://www.cs.ubc.ca/labs/socius/files/papers/chi2020-skimmer.pdf)
- **[R2]** [SpeechSkimmer: Interactively Skimming Recorded Speech](https://www.cs.columbia.edu/~smaskey/candidacy/cand_papers/arons93speechskimmer.pdf)
- **[R3]** [NVDA User Guide](https://download.nvaccess.org/documentation/userGuide.html)
- **[R4]** [WCAG: Understanding Guideline 2.4 — Navigable](https://www.w3.org/WAI/WCAG21/Understanding/navigable)
- **[R5]** [WAI-ARIA Landmarks Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/landmarks/)
- **[R6]** [WAI-ARIA: Providing Accessible Names and Descriptions](https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/)
- **[R7]** [MDN: ARIA Live Regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)
- **[R8]** [Microsoft UI Automation TextPattern Overview](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-ui-automation-textpattern-overview)
- **[R9]** [edge-tts Python Project](https://github.com/rany2/edge-tts)
- **[R10]** [Qt for Python / PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- **[R11]** [W3C Tables Tutorial](https://www.w3.org/WAI/tutorials/tables/)
- **[R12]** [Evaluating Long-form Text-to-Speech: Comparing the Ratings of Sentences and Paragraphs](https://arxiv.org/abs/1909.03965)
- **[R13]** [Choice of Voices: A Large-Scale Evaluation of Text-to-Speech Voice Quality for Long-Form Content](https://dl.acm.org/doi/fullHtml/10.1145/3313831.3376789)
- **[R14]** [Microsoft RegisterHotKey Documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)

---

## 25. Final product principle

> Copy Cat should not merely turn visible text into audio. It should turn captured content into a stable, navigable auditory document while preserving the original source and keeping the user in control.
