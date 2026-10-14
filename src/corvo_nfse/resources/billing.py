"""Billing resource — plan, usage."""

from __future__ import annotations

from ..error import Result
from ..transport import Transport
from ..types.billing import BillingPlanResponse, QuotaStatus


class Billing:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def plan(self) -> Result[BillingPlanResponse]:
        return await self._t.request("GET", "/billing/plan")

    async def usage(self) -> Result[QuotaStatus]:
        return await self._t.request("GET", "/billing/usage")
