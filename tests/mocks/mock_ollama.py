import json
import httpx
from typing import Optional

class MockOllamaTransport(httpx.AsyncBaseTransport):
    """Offline httpx MockTransport for testing OllamaTransformer without a running daemon."""

    def __init__(
        self,
        response_text: str = "Python function that returns the sum of a and b.",
        status_code: int = 200,
        should_timeout: bool = False,
        should_fail_connection: bool = False,
    ):
        self.response_text = response_text
        self.status_code = status_code
        self.should_timeout = should_timeout
        self.should_fail_connection = should_fail_connection
        self.requests = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)

        if self.should_fail_connection:
            raise httpx.ConnectError("Connection refused by mock Ollama server", request=request)

        if self.should_timeout:
            raise httpx.TimeoutException("Mock 3s timeout exceeded", request=request)

        if request.url.path == "/api/version":
            return httpx.Response(self.status_code, json={"version": "0.1.30"})

        if self.status_code != 200:
            return httpx.Response(self.status_code, json={"error": "Internal server error"})

        body = json.loads(request.content.decode("utf-8"))
        payload = {
            "model": body.get("model", "gemma3:12b"),
            "response": self.response_text,
            "done": True,
        }
        return httpx.Response(200, json=payload)
