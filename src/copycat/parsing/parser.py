import uuid
from typing import List, Optional, Tuple
from markdown_it import MarkdownIt
from copycat.domain.models import (
    BlockType,
    SourceSnapshot,
    DocumentBlock,
    ReadableDocument,
)
from copycat.protocols.parser import DocumentParser

def _get_char_offsets(raw_text: str, line_map: Optional[List[int]]) -> Tuple[Optional[int], Optional[int]]:
    if not line_map or len(line_map) < 2:
        return (None, None)
    start_line, end_line = line_map[0], line_map[1]
    lines = raw_text.splitlines(keepends=True)
    if not lines or start_line < 0 or start_line >= len(lines):
        return (None, None)
    start_char = sum(len(lines[j]) for j in range(start_line))
    end_char = sum(len(lines[j]) for j in range(min(end_line, len(lines))))
    return (start_char, end_char)

class MarkdownDocumentParser(DocumentParser):
    """AST-based Markdown parser implementing DocumentParser protocol using markdown-it-py."""

    def __init__(self):
        self.md = MarkdownIt("commonmark", {"html": True})

    def parse(self, snapshot: SourceSnapshot) -> ReadableDocument:
        raw_text = snapshot.raw_text or ""
        tokens = self.md.parse(raw_text)

        blocks: List[DocumentBlock] = []
        outline: List[str] = []
        doc_title: Optional[str] = None

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                level = int(token.tag[1]) if len(token.tag) > 1 and token.tag[1].isdigit() else 1
                inline_token = tokens[i + 1] if i + 1 < len(tokens) else None
                heading_text = inline_token.content if inline_token and inline_token.type == "inline" else ""

                if not doc_title and level == 1:
                    doc_title = heading_text

                s_start, s_end = _get_char_offsets(raw_text, token.map)

                outline.append(heading_text)
                blocks.append(
                    DocumentBlock(
                        block_id=str(uuid.uuid4()),
                        block_type=BlockType.HEADING,
                        text=heading_text,
                        level=level,
                        source_start=s_start,
                        source_end=s_end,
                    )
                )
                i += 2

            elif token.type == "paragraph_open":
                inline_token = tokens[i + 1] if i + 1 < len(tokens) else None
                para_text = inline_token.content if inline_token and inline_token.type == "inline" else ""
                s_start, s_end = _get_char_offsets(raw_text, token.map)
                if para_text.strip():
                    blocks.append(
                        DocumentBlock(
                            block_id=str(uuid.uuid4()),
                            block_type=BlockType.PARAGRAPH,
                            text=para_text,
                            source_start=s_start,
                            source_end=s_end,
                        )
                    )
                i += 2

            elif token.type == "fence" or token.type == "code_block":
                code_text = token.content
                lang = token.info.strip() if token.info else None
                s_start, s_end = _get_char_offsets(raw_text, token.map)
                blocks.append(
                    DocumentBlock(
                        block_id=str(uuid.uuid4()),
                        block_type=BlockType.CODE,
                        text=code_text,
                        language=lang,
                        source_start=s_start,
                        source_end=s_end,
                    )
                )

            elif token.type == "list_item_open":
                s_start, s_end = _get_char_offsets(raw_text, token.map)
                i += 1
                item_text = ""
                while i < len(tokens) and tokens[i].type != "list_item_close":
                    if tokens[i].type == "inline":
                        item_text += tokens[i].content
                    elif tokens[i].type == "list_item_open":
                        break
                    i += 1
                if item_text.strip():
                    blocks.append(
                        DocumentBlock(
                            block_id=str(uuid.uuid4()),
                            block_type=BlockType.LIST_ITEM,
                            text=item_text.strip(),
                            source_start=s_start,
                            source_end=s_end,
                        )
                    )
                continue

            elif token.type == "blockquote_open":
                s_start, s_end = _get_char_offsets(raw_text, token.map)
                i += 1
                quote_text = ""
                while i < len(tokens) and tokens[i].type != "blockquote_close":
                    if tokens[i].type == "inline":
                        quote_text += tokens[i].content
                    i += 1
                if quote_text.strip():
                    blocks.append(
                        DocumentBlock(
                            block_id=str(uuid.uuid4()),
                            block_type=BlockType.QUOTE,
                            text=quote_text,
                            source_start=s_start,
                            source_end=s_end,
                        )
                    )

            i += 1

        # Fallback if raw text produced no blocks
        if not blocks and raw_text.strip():
            blocks.append(
                DocumentBlock(
                    block_id=str(uuid.uuid4()),
                    block_type=BlockType.PARAGRAPH,
                    text=raw_text.strip(),
                    source_start=0,
                    source_end=len(raw_text),
                )
            )

        return ReadableDocument(
            document_id=str(uuid.uuid4()),
            snapshot=snapshot,
            title=doc_title or (outline[0] if outline else None),
            blocks=blocks,
            outline=outline,
        )
