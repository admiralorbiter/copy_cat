from typing import Protocol
from copycat.domain.models import SourceSnapshot, ReadableDocument

class DocumentParser(Protocol):
    def parse(self, snapshot: SourceSnapshot) -> ReadableDocument:
        ...
