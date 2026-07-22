# Copy Cat — Product Specification

**Status:** Active product specification  
**Version:** 0.1  
**Primary platform:** Windows  
**Initial implementation:** Python, PySide6, Edge TTS, QtMultimedia  

---

## 1. Executive Summary

**Copy Cat** is a Windows desktop application that transforms selected or copied text from any application into a navigable, natural-sounding auditory document.

### Primary Use Case
1. Highlight or copy text in Antigravity, ChatGPT, a browser, IDE, or document.
2. Open Copy Cat or invoke a shortcut.
3. Listen to high-quality audio using Edge TTS.
4. Pause, repeat, skip, or navigate structure without requiring continuous visual focus.

### Product Positioning
Copy Cat is an **eyes-reduced document reader** sitting between a simple read-aloud tool and a full screen reader. It preserves document structure, maintains a semantic reading cursor, and enables non-linear auditory skimming.

---

## 2. Scope & Non-Goals

### Initial Scope (MVP / Phase 1 & 2)
- Read plain text and Markdown text captured from the Windows clipboard.
- Parse text into structured semantic blocks (headings, paragraphs, lists, code blocks, links, tables).
- Synthesize speech using `edge-tts`.
- Play audio via `PySide6.QtMultimedia`.
- Display and visually highlight the active spoken block.
- Maintain an independent semantic reading position.
- Provide playback controls: Play, Pause, Stop, Next Block, Previous Block.
- Configurable voice, speech rate, code handling, and link policies.

### Explicit Non-Goals (First Versions)
- Fully replacing screen readers like NVDA or Narrator.
- Token-by-token streaming AI reading during generation.
- OCR text extraction.
- Automatic LLM summarization (unless explicitly selected in later advanced modes).
- Full hands-free voice control.
- Cross-platform support (Windows-first target).

---

## 3. Core User Workflows

### 3.1 Clipboard MVP Workflow
1. User highlights text in any application (e.g., Antigravity response).
2. User copies text (`Ctrl+C`).
3. User opens Copy Cat.
4. Copy Cat captures and previews clipboard contents.
5. User clicks **Read**.
6. Copy Cat parses structure and begins speaking block by block.
7. Active block is visually highlighted in the UI.
8. User controls playback via UI buttons or hotkeys.

### 3.2 Near-Term Global Hotkey Workflow
1. User highlights text anywhere on Windows.
2. User triggers global hotkey (e.g. `Ctrl+Alt+Space`).
3. Copy Cat captures selection via clipboard, restores prior clipboard content, and begins playback immediately without stealing focus.

### 3.3 Semantic Navigation & Resume Workflow
1. User pauses or stops playback.
2. The semantic cursor (block index, sentence index, current heading path) is saved.
3. On resume, Copy Cat optionally replays heading context or previous sentence before continuing smoothly.

---

## 4. Finalized Design Choices

| Area | Decision | Rationale |
|---|---|---|
| **OS Platform** | Windows | Primary target desktop environment. |
| **Language & Framework** | Python 3.12+ & PySide6 (Qt) | Native GUI capabilities, official Qt bindings. |
| **Audio Playback** | `PySide6.QtMultimedia` | Native Qt multimedia player (`QMediaPlayer` / `QAudioOutput`), no extra binary C-extensions needed. |
| **TTS Engine** | Edge TTS (`edge-tts`) | Natural Microsoft Edge neural voices without API keys. Pluggable `SpeechProvider` interface. |
| **Markdown Parsing** | `markdown-it-py` | AST-based robust parsing for headings, lists, code fences, and links. |
| **Input Source** | Windows Clipboard (`QClipboard`) | Simple, reliable, application-agnostic baseline capture. |
