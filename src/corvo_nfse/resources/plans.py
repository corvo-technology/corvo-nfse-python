"""Plans resource: the public price catalog (monthly cycle only)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..error import Result
from ..transport import Transport
from ..types.credits import PlanQuote, PlanRecommendation


class Plans:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Result[Dict[str, Any]]:
        """One page of plan prices, from the smallest to the largest allowance."""
        return await self._t.list_page("/plans", {"limit": limit, "cursor": cursor})

    async def get(self, slug: str) -> Result[PlanQuote]:
        """The price of one plan (``free``, ``developer``, ``growth``, ``scale`` or ``volume``)."""
        return await self._t.request("GET", f"/plans/{slug}")

    async def quote(self, volume: int) -> Result[Optional[PlanRecommendation]]:
        """The plan recommended for ``volume`` invoices per month.

        ``data`` is ``None`` (no error) when the volume is missing or not positive.
        """
        return await self._t.request("GET", "/plans/quote", query={"volume": volume})
