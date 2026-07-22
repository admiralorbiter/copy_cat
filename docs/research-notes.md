# Copy Cat — Research Synthesis, References & Advanced Models

## 1. Research Synthesis & UX Foundations

### 1.1 Eyes-Reduced Reading
Research framing: **eyes-reduced reading**, not completely eyes-free computing.
Eyes-reduced systems allow the listener to combine audio with occasional glances, mouse interaction, and visual confirmation. The Skimmer research (*CHI 2020*) found that auditory reading benefits from non-linear navigation and auditory or haptic cues rather than relying only on continuous playback.[R1]

#### Design Consequence
Copy Cat uses the visual channel strategically:
- Highlight the current active block.
- Show the document outline.
- Display progress visually.
- Expose large, clear playback controls.
- Show skipped code/formatting markers.
- Preserve original source text for visual reference.

---

### 1.2 Auditory Skimming
SpeechSkimmer (*Arons 1993*) demonstrated that listening tools can support multiple levels of detail and interactive control over speed rather than requiring linear listening.[R2]

- **Playback Speed:** controls how fast text is spoken.
- **Detail Level:** controls how much content is spoken (Full, Natural, Structured, Outline, Gist, Actions, No Code).

---

### 1.3 Screen-Reader Browse Mode
Mature screen readers (e.g., NVDA) create a browsable representation of complex documents (*NVDA User Guide*).[R3]
Copy Cat borrows this concept by taking a **stable source snapshot** and creating an independent **virtual reading cursor** that can navigate without stealing system focus or mutating source selection.

---

### 1.4 Headings, Landmarks & Accessibility
- **Headings & Landmarks (WCAG 2.1 / ARIA):** W3C guidance emphasizes headings as essential mechanisms for orientation and navigation.[R4][R5]
- **Accessible Names (W3C ARIA):** Accessible names are not always visible text; extraction layers must handle visible text vs accessible names vs control roles.[R6]
- **ARIA Live Regions:** Dynamic event management (Silent, Polite, Interrupting events).[R7]
- **Windows UI Automation (`TextPattern`):** Microsoft UI Automation exposes text streams with ranges and attributes.[R8]
- **Tables (W3C):** Preserving table caption, headers, rows, columns, and header relationships rather than destroying 2D context.[R11]

---

### 1.5 Long-Form Voice Quality
Long-form TTS should be evaluated using actual multi-paragraph passages rather than isolated demo sentences (*ACM / arXiv TTS evaluations*).[R12][R13]
Evaluation metrics for long sessions:
- Listening comfort & clarity over 5–10 minutes.
- Attention drift rate.
- Pronunciation failures on technical acronyms and identifiers.
- Paragraph-boundary pause clarity.

---

## 2. Advanced Mathematical & Adaptive Models (Future Research)

### 2.1 Difficulty-Sensitive Speech Rate
A transparent difficulty score \( D \):

\[
D = w_1 L_s + w_2 L_w + w_3 N + w_4 C + w_5 S
\]

Where:
- \( L_s \): sentence length
- \( L_w \): word complexity
- \( N \): numeric density
- \( C \): code and symbol density
- \( S \): syntactic complexity proxy

Dynamic Speech Rate \( r \):

\[
r = \operatorname{clamp}(r_0 - kD,\ r_{\min},\ r_{\max})
\]

This automatically slows down for dense technical passages and speeds up through familiar prose.

---

### 2.2 Personalization via Contextual Bandits
Future adaptive reading policy selection based on context (application type, length, code density, past rewind rates) to optimize rate, chunk size, verbosity, and pause lengths.

---

## 3. Research References

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
