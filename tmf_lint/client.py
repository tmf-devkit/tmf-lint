"""
tmf-lint — LintClient.

A thin async wrapper around ``httpx.AsyncClient`` that carries the base URL
so individual rules only need to supply the path.  Keeping this wrapper
minimal means tests can patch ``httpx.AsyncClient`` directly (via respx)
without any extra indirection.
"""
from __future__ import annotations

import httpx


class LintClient:
    """Async HTTP client bound to a single base URL."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
        )

    async def __aenter__(self) -> LintClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    # ── HTTP verbs ───────────────────────────────────────────────────────────

    async def post(self, path: str, json: dict) -> httpx.Response:
        """Send a POST request and return the full response."""
        return await self._client.post(path, json=json)

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        """Send a GET request with optional query parameters."""
        return await self._client.get(path, params=params or {})

    async def patch(self, path: str, json: dict) -> httpx.Response:
        """Send a PATCH request and return the full response."""
        return await self._client.patch(path, json=json)

    async def delete(self, path: str) -> httpx.Response:
        """Send a DELETE request and return the full response."""
        return await self._client.delete(path)

    @property
    def base_url(self) -> str:
        """The base URL this client is bound to."""
        return self._base_url
