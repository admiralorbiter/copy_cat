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
    announce_heading_levels: bool = False

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
