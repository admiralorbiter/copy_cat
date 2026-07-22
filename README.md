# Copy Cat

**Copy Cat** is a Windows desktop application that turns selected or copied text into a navigable, natural-sounding auditory document.

## Overview
Copy Cat sits between a simple read-aloud utility and a complete screen reader. It preserves document structure, maintains a semantic reading cursor, and allows users to navigate by sentence, paragraph, heading, list, and code block using natural neural voices (Edge TTS).

## Documentation
All project documentation is modularized in the [`docs/`](./docs) directory:
- [Product Specification](./docs/product-spec.md)
- [Architecture & Domain Models](./docs/architecture.md)
- [Testing Strategy & TDD Guidelines](./docs/testing-strategy.md)
- [Development Roadmap](./docs/roadmap.md)
- [Research Synthesis & References](./docs/research-notes.md)

## Development Setup
```bash
# Install package and development dependencies
pip install -e .[dev]

# Run automated tests with mandatory 70%+ coverage check
pytest
```
