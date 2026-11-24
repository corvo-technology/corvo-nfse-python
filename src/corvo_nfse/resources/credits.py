"""Credits resource — balance, plans, history, iterate_history."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional

from ..error import Result
from ..transport import Transport
from ..types.credits import CreditBalance, CreditPurchasePreview, CreditTransaction


class Credits:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def balance(self) -> Result[CreditBalance]:
        """``balance`` is the plan notes left plus the loose notes bought separately."""
        return await self._t.request("GET", "/credits")

    async def plans(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page("/credits/plans", {"limit": limit, "cursor": cursor})

    async def history(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page("/credits/history", {"limit": limit, "cursor": cursor})

    def iterate_history(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> AsyncIterator[CreditTransaction]:
        """Yield every credit transaction across pages.

        Raises :class:`~corvo_nfse.CorvoApiError` on a page failure.
        """
        return self._t.iterate("/credits/history", {"limit": limit, "cursor": cursor})

    async def preview_purchase(self, units: int) -> Result[CreditPurchasePreview]:
        """Price a one-off purchase of ``units`` notes (R$ 0,99 each, at least 3, whole numbers).

        ``GET /credits/purchase/preview``. Buying is done in the dashboard.
        """
        return await self._t.request("GET", "/credits/purchase/preview", query={"units": units})
