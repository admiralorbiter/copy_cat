from typing import Protocol, Optional
from copycat.domain.models import DocumentBlock

class DocumentTransformer(Protocol):
    """Protocol for AI-assisted auditory text transformation services."""

    async def transform_block(self, block: DocumentBlock, mode: str) -> Optional[str]:
        """Transforms a document block into an auditory-optimized string summary.
        
        Returns None if transformation fails or is skipped, triggering deterministic fallback.
        """
        ...

    async def check_health(self) -> bool:
        """Returns True if local transformation service (e.g. Ollama) is reachable."""
        ...
