"""Companies resource — create, get, update, remove, list, iterate."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional

from ..error import Result
from ..transport import Transport
from ..types.company import Company, CompanyCreateParams, CompanyUpdateParams


def _query(limit: Optional[int], cursor: Optional[str]) -> Dict[str, Any]:
    return {"limit": limit, "cursor": cursor}


class Companies:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def create(self, params: CompanyCreateParams) -> Result[Company]:
        return await self._t.request("POST", "/companies", json=params)

    async def list(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page("/companies", _query(limit, cursor))

    def iterate(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> AsyncIterator[Company]:
        """Yield every company across pages.

        Raises :class:`~corvo_nfse.CorvoApiError` on a page failure — the one
        documented exception to the never-raise rule.
        """
        return self._t.iterate("/companies", _query(limit, cursor))

    async def get(self, company_id: str) -> Result[Company]:
        return await self._t.request("GET", f"/companies/{company_id}")

    async def update(self, company_id: str, params: CompanyUpdateParams) -> Result[Company]:
        return await self._t.request("PATCH", f"/companies/{company_id}", json=params)

    async def remove(self, company_id: str) -> Result[None]:
        return await self._t.request("DELETE", f"/companies/{company_id}")
