import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

from copycat.domain.models import DocumentBlock, BlockType
from copycat.protocols.transformer import DocumentTransformer

logger = logging.getLogger(__name__)

PROMPTS: Dict[str, str] = {
    "code_summary": (
        "Summarize what the following code does in 1-2 spoken English sentences for read-aloud. "
        "Do not include raw syntax, code blocks, or formatting:\n\n<user_content>\n{text}\n</user_content>"
    ),
    "data_summary": (
        "Summarize the key trends, columns, and values in this table or data block into 1-2 natural spoken sentences:\n\n<user_content>\n{text}\n</user_content>"
    ),
    "gist": (
        "Condense the following paragraph into a crisp 1-2 sentence auditory summary for listening:\n\n<user_content>\n{text}\n</user_content>"
    ),
    "document_summary": (
        "You are an expert summarizer. Provide a comprehensive, easy-to-listen-to Executive Summary of the following document. "
        "Highlight the main ideas, key arguments, and any critical conclusions. "
        "Write in a natural, spoken-English style suitable for text-to-speech. Do not use complex markdown formatting or lists.\n\n<user_content>\n{text}\n</user_content>"
    ),
}

class OllamaTransformer(DocumentTransformer):
    """Local LLM document transformer implementing DocumentTransformer protocol using Ollama.
    
    Default endpoint: http://127.0.0.1:11434/api/generate
    Default model: gemma3:12b
    Features: Strict 3.0s timeout, circuit-breaker fallback to deterministic reading, and health checks.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        model: str = "gemma3:12b",
        timeout: float = 3.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        # Prefer 127.0.0.1 over localhost to prevent Windows IPv6 resolution latency
        cleaned = endpoint.rstrip("/")
        if "localhost" in cleaned:
            cleaned = cleaned.replace("localhost", "127.0.0.1")
        self.endpoint = cleaned
        self.model = model
        self.timeout = timeout
        self.transport = transport
        self._consecutive_failures: int = 0
        self._circuit_open: bool = False

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=1.0),
            transport=self.transport,
        )

    async def check_health(self) -> bool:
        """Checks if local Ollama API is reachable."""
        try:
            async with self._get_client() as client:
                res = await client.get(f"{self.endpoint}/api/version")
                if res.status_code == 200:
                    self._circuit_open = False
                    self._consecutive_failures = 0
                    return True
        except Exception:
            pass
        return False

    async def transform_block(self, block: DocumentBlock, mode: str) -> Optional[str]:
        """Transforms a DocumentBlock into an auditory AI summary string using Gemma 3 12B.
        
        Returns None on timeout, connection refusal, or invalid mode to trigger transparent fallback.
        """
        if not mode or mode == "off" or mode not in PROMPTS:
            return None

        # Fast-fail if circuit breaker tripped (3 consecutive failures)
        if self._circuit_open:
            return None

        # Filter mode applicability based on block type
        if mode == "code_summary" and block.block_type != BlockType.CODE:
            return None
        if mode == "data_summary" and block.block_type != BlockType.TABLE:
            return None
        if mode == "gist" and len(block.text.strip()) < 150:
            return None  # Block is too short to summarize; bypass AI and read naturally

        prompt_template = PROMPTS[mode]
        prompt = prompt_template.format(text=block.text)

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 120},
        }

        try:
            async with self._get_client() as client:
                res = await client.post(f"{self.endpoint}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    summary = data.get("response", "").strip()
                    if summary:
                        self._consecutive_failures = 0
                        return f"AI summary: {summary}"
        except Exception as err:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._circuit_open = True
            logger.warning(f"Ollama transformation request failed ({err}). Transparent fallback activated.")

        return None

    async def summarize_document(self, raw_text: str) -> Optional[str]:
        """Generates a full-document summary. Truncates input to 25,000 characters to protect context limits."""
        if not raw_text or not raw_text.strip():
            return None

        # Fast-fail if circuit breaker tripped
        if self._circuit_open:
            return None

        # Truncate to ~25,000 characters to prevent context window overflow (8K tokens)
        truncated_text = raw_text[:25000]
        prompt = PROMPTS["document_summary"].format(text=truncated_text)

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 500},  # Allow longer output for full summary
        }

        # Use a much longer timeout (5 minutes) for full document summarization since 8K context takes time
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=1.0),
            transport=self.transport,
        )

        try:
            async with client:
                res = await client.post(f"{self.endpoint}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    summary = data.get("response", "").strip()
                    if summary:
                        self._consecutive_failures = 0
                        return f"Executive Summary: {summary}"
        except Exception as err:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._circuit_open = True
            logger.warning(f"Ollama document summarization failed ({type(err).__name__}: {err}).")

        return None
