from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

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

class PlaybackState(Enum):
    IDLE = "idle"
    CAPTURING = "capturing"
    PARSING = "parsing"
    BUFFERING = "buffering"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    CAPTURE_FAILED = "capture_failed"
    PARSE_FAILED = "parse_failed"
    SYNTHESIS_FAILED = "synthesis_failed"
    AUDIO_OUTPUT_FAILED = "audio_output_failed"

@dataclass
class ReadingPolicy:
    verbosity: str = "natural"
    code_mode: str = "announce_and_skip"  # "announce_and_skip", "read_all", "omit"
    link_mode: str = "text_only_clean"    # "text_only_clean", "text_with_announcement", "omit"
    table_mode: str = "summary"
    announce_heading_levels: bool = False
    repeat_context_on_resume: bool = True
    # Phase 3.5 AI Transformation Settings
    ai_mode: str = "off"                  # "off", "code_summary", "data_summary", "gist"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"
    ollama_timeout: float = 3.0           # 3.0s SLA timeout circuit breaker

@dataclass(frozen=True)
class SourceSnapshot:
    raw_text: str
    source_application: Optional[str] = None
    captured_at: datetime = field(default_factory=datetime.now)
    source_id: str = "clipboard"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentBlock:
    block_id: str
    block_type: BlockType
    text: str
    level: Optional[int] = None
    language: Optional[str] = None
    children: List["DocumentBlock"] = field(default_factory=list)
    source_start: Optional[int] = None
    source_end: Optional[int] = None

@dataclass
class ReadableDocument:
    document_id: str
    snapshot: SourceSnapshot
    title: Optional[str]
    blocks: List[DocumentBlock]
    outline: List[str] = field(default_factory=list)

@dataclass
class ReadingPosition:
    block_index: int = 0
    sentence_index: int = 0
    heading_path: List[str] = field(default_factory=list)

@dataclass
class SpeechRequest:
    request_id: str
    text: str
    voice: str = "en-US-JennyNeural"
    rate: str = "+0%"
    block_id: str = "block-0"

@dataclass
class AudioChunk:
    chunk_id: str
    request_id: str
    audio_bytes: bytes
    format: str = "mp3"
    duration_ms: int = 0
    block_id: str = "block-0"

class ReadingSession:
    """Encapsulates document state, semantic reading cursor, and generation token for Phase 2 & 3.5."""

    def __init__(self, document: ReadableDocument, policy: Optional[ReadingPolicy] = None):
        self.document = document
        self.policy = policy or ReadingPolicy()
        self.position = ReadingPosition()
        self.generation: int = 0

    @property
    def current_block(self) -> Optional[DocumentBlock]:
        if 0 <= self.position.block_index < len(self.document.blocks):
            return self.document.blocks[self.position.block_index]
        return None

    @property
    def total_blocks(self) -> int:
        return len(self.document.blocks)

    def can_skip_next(self) -> bool:
        return self.position.block_index + 1 < self.total_blocks

    def can_skip_prev(self) -> bool:
        return self.position.block_index > 0

    def advance_next(self) -> Optional[DocumentBlock]:
        """Advances naturally to the next block without invalidating the generation token."""
        if self.can_skip_next():
            self.position.block_index += 1
            self.position.sentence_index = 0
            return self.current_block
        return None

    def skip_next(self) -> Optional[DocumentBlock]:
        """Manual user skip to next block; increments generation token to invalidate background pre-fetches."""
        if self.can_skip_next():
            self.position.block_index += 1
            self.position.sentence_index = 0
            self.generation += 1
            return self.current_block
        return None

    def skip_prev(self) -> Optional[DocumentBlock]:
        """Manual user skip to previous block; increments generation token."""
        if self.can_skip_prev():
            self.position.block_index -= 1
            self.position.sentence_index = 0
            self.generation += 1
            return self.current_block
        return None

    def seek_to_block(self, index: int) -> Optional[DocumentBlock]:
        """Manual user seek to specific block index; increments generation token."""
        if 0 <= index < self.total_blocks:
            self.position.block_index = index
            self.position.sentence_index = 0
            self.generation += 1
            return self.current_block
        return None
