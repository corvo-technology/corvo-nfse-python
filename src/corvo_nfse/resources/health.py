"""Health resource — live, ready (public, raw JSON pass-through)."""

from __future__ import annotations

from typing import Any

from ..error import Result
from ..transport import Transport


class Health:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def live(self) -> Result[Any]:
        """GET /health/live — raw JSON body, no envelope."""
        return await self._t.request("GET", "/health/live", unwrap="none")

    async def ready(self) -> Result[Any]:
        """GET /health/ready — raw JSON body, no envelope."""
        return await self._t.request("GET", "/health/ready", unwrap="none")
