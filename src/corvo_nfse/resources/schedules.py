"""Scheduled and recurring invoices (``options.type`` ``SCHEDULE`` / ``RECURRING``).

Schedules answer in snake_case: the keys are passed through as they are.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Literal, Optional

from ..error import Result
from ..transport import Transport, seg
from ..types.customer import Schedule, ScheduleRun, ScheduleUpdateParams

ScheduleStatus = Literal["active", "paused", "completed", "cancelled"]


class Schedules:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    @staticmethod
    def _query(
        status: Optional[ScheduleStatus],
        company_id: Optional[str],
        limit: Optional[int],
        cursor: Optional[str],
    ) -> Dict[str, Any]:
        return {"status": status, "companyId": company_id, "limit": limit, "cursor": cursor}

    async def list(
        self,
        *,
        status: Optional[ScheduleStatus] = None,
        company_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page("/schedules", self._query(status, company_id, limit, cursor))

    def iterate(
        self,
        *,
        status: Optional[ScheduleStatus] = None,
        company_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[Schedule]:
        """Yield every schedule across pages (raises on a page failure)."""
        return self._t.iterate("/schedules", self._query(status, company_id, limit, cursor))

    async def get(self, schedule_id: str) -> Result[Schedule]:
        return await self._t.request("GET", f"/schedules/{seg(schedule_id)}")

    async def update(self, schedule_id: str, params: ScheduleUpdateParams) -> Result[Schedule]:
        """Change a schedule; applies to the next runs only."""
        return await self._t.request("PATCH", f"/schedules/{seg(schedule_id)}", json=params)

    async def pause(self, schedule_id: str) -> Result[Schedule]:
        return await self._t.request("POST", f"/schedules/{seg(schedule_id)}/pause")

    async def resume(self, schedule_id: str) -> Result[Schedule]:
        """Resume a paused schedule at its next occurrence."""
        return await self._t.request("POST", f"/schedules/{seg(schedule_id)}/resume")

    async def cancel(self, schedule_id: str) -> Result[Schedule]:
        """Cancel a schedule (final)."""
        return await self._t.request("POST", f"/schedules/{seg(schedule_id)}/cancel")

    async def list_runs(
        self,
        schedule_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        """Log of every attempt to run the schedule, newest first."""
        return await self._t.list_page(
            f"/schedules/{seg(schedule_id)}/runs", {"limit": limit, "cursor": cursor}
        )

    def iterate_runs(
        self,
        schedule_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[ScheduleRun]:
        return self._t.iterate(
            f"/schedules/{seg(schedule_id)}/runs", {"limit": limit, "cursor": cursor}
        )
