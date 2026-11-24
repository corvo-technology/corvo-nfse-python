"""Plans resource: the public price catalog (monthly cycle only)."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from ..error import Result
from ..transport import Transport, seg
from ..types.credits import PlanPrice, PlanRecommendation


class Plans:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        cycle: Optional[Literal["monthly", "annual"]] = None,
    ) -> Result[Dict[str, Any]]:
        """One page of public plan prices (``PlanPrice``). Needs no API key; ``cycle="annual"`` is discounted."""
        return await self._t.list_page("/plans", {"limit": limit, "cursor": cursor, "cycle": cycle})

    async def get(
        self, slug: str, *, cycle: Optional[Literal["monthly", "annual"]] = None
    ) -> Result[PlanPrice]:
        """The price of one paid plan (``solo``, ``equipe``, ``empresa`` or ``escala``). Needs no API key."""
        return await self._t.request("GET", f"/plans/{seg(slug)}", query={"cycle": cycle})

    async def quote(self, volume: int) -> Result[Optional[PlanRecommendation]]:
        """The plan recommended for ``volume`` invoices per month.

        ``data`` is ``None`` (no error) when the volume is missing or not positive.
        """
        return await self._t.request("GET", "/plans/quote", query={"volume": volume})
