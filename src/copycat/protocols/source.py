from typing import Protocol
from copycat.domain.models import SourceSnapshot

class TextSource(Protocol):
    async def capture(self) -> SourceSnapshot:
        ...
