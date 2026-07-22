import re
import uuid
from typing import List, Optional
from copycat.domain.models import (
    BlockType,
    DocumentBlock,
    ReadableDocument,
    SpeechRequest,
    ReadingPolicy,
)
from copycat.services.speech_normalizer import normalize_text

class SpeechPlanner:
    """Converts DocumentBlock AST items into speakable SpeechRequests adhering to ReadingPolicy."""

    def __init__(self, policy: Optional[ReadingPolicy] = None):
        self.policy = policy or ReadingPolicy()

    def format_block_text(self, block: DocumentBlock) -> str:
        """Applies reading policy rules to a single DocumentBlock."""
        if block.block_type == BlockType.CODE:
            return self._format_code_block(block)
        elif block.block_type == BlockType.HEADING:
            prefix = f"Heading level {block.level}, " if self.policy.announce_heading_levels and block.level else ""
            return f"{prefix}{block.text}."
        elif block.block_type == BlockType.LINK:
            return self._format_link_block(block.text)
        else:
            cleaned = self._format_links_in_text(block.text)
            return normalize_text(cleaned)

    def _format_code_block(self, block: DocumentBlock) -> str:
        if self.policy.code_mode == "omit":
            return ""

        lines = [line for line in block.text.strip().splitlines() if line.strip()]
        line_count = len(lines) if lines else 1
        line_str = "1 line" if line_count == 1 else f"{line_count} lines"

        lang_str = f"{block.language.capitalize()} " if block.language else ""

        if self.policy.code_mode == "announce_and_skip":
            return f"{lang_str}code block, {line_str}, skipped."
        elif self.policy.code_mode == "read_all":
            return f"{lang_str}code block: {block.text}"
        return f"{lang_str}code block, {line_str}, skipped."

    def _format_links_in_text(self, text: str) -> str:
        if self.policy.link_mode == "text_only" or self.policy.link_mode == "text_only_clean":
            # Replace [Text](url) with Text
            return re.sub(r'\[([^\]]+)\]\((?:https?://\S+|[^)]+)\)', r'\1', text)
        elif self.policy.link_mode == "text_with_announcement":
            return re.sub(r'\[([^\]]+)\]\((?:https?://\S+|[^)]+)\)', r'\1, link omitted', text)
        elif self.policy.link_mode == "omit":
            return re.sub(r'\[([^\]]+)\]\((?:https?://\S+|[^)]+)\)', '', text)
        return text

    def plan_document(
        self,
        doc: ReadableDocument,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
    ) -> List[SpeechRequest]:
        requests: List[SpeechRequest] = []

        for block in doc.blocks:
            spoken_text = self.format_block_text(block)
            if spoken_text and spoken_text.strip():
                requests.append(
                    SpeechRequest(
                        request_id=str(uuid.uuid4()),
                        text=spoken_text,
                        voice=voice,
                        rate=rate,
                        block_id=block.block_id,
                    )
                )

        return requests
