import uuid
from typing import List, Optional
from markdown_it import MarkdownIt
from copycat.domain.models import (
    BlockType,
    SourceSnapshot,
    DocumentBlock,
    ReadableDocument,
)
from copycat.protocols.parser import DocumentParser

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

                outline.append(heading_text)
                blocks.append(
                    DocumentBlock(
                        block_id=str(uuid.uuid4()),
                        block_type=BlockType.HEADING,
                        text=heading_text,
                        level=level,
                    )
                )
                i += 2

            elif token.type == "paragraph_open":
                # Check if paragraph is inside a list item
                inline_token = tokens[i + 1] if i + 1 < len(tokens) else None
                para_text = inline_token.content if inline_token and inline_token.type == "inline" else ""
                if para_text.strip():
                    blocks.append(
                        DocumentBlock(
                            block_id=str(uuid.uuid4()),
                            block_type=BlockType.PARAGRAPH,
                            text=para_text,
                        )
                    )
                i += 2

            elif token.type == "fence" or token.type == "code_block":
                code_text = token.content
                lang = token.info.strip() if token.info else None
                blocks.append(
                    DocumentBlock(
                        block_id=str(uuid.uuid4()),
                        block_type=BlockType.CODE,
                        text=code_text,
                        language=lang,
                    )
                )

            elif token.type == "list_item_open":
                # Extract inline text for this list item
                i += 1
                item_text = ""
                while i < len(tokens) and tokens[i].type != "list_item_close":
                    if tokens[i].type == "inline":
                        item_text += tokens[i].content
                    elif tokens[i].type == "list_item_open":
                        # Sub-item encountered, handle recursively by breaking back to main loop
                        break
                    i += 1
                if item_text.strip():
                    blocks.append(
                        DocumentBlock(
                            block_id=str(uuid.uuid4()),
                            block_type=BlockType.LIST_ITEM,
                            text=item_text.strip(),
                        )
                    )
                continue

            elif token.type == "blockquote_open":
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
                )
            )

        return ReadableDocument(
            document_id=str(uuid.uuid4()),
            snapshot=snapshot,
            title=doc_title or (outline[0] if outline else None),
            blocks=blocks,
            outline=outline,
        )
