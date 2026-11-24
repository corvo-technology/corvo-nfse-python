"""Favorite services of a company."""

from __future__ import annotations

from typing import Any, Dict, List

from ..error import Result
from ..transport import Transport, seg
from ..types.company import ServiceFavorite, ServiceFavoriteCreateParams


class ServiceFavorites:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self, company_id: str) -> Result[List[ServiceFavorite]]:
        return await self._t.request("GET", f"/companies/{seg(company_id)}/service-favorites")

    async def create(
        self, company_id: str, params: ServiceFavoriteCreateParams
    ) -> Result[ServiceFavorite]:
        return await self._t.request(
            "POST", f"/companies/{seg(company_id)}/service-favorites", json=params
        )

    async def remove(self, company_id: str, favorite_id: str) -> Result[Dict[str, Any]]:
        return await self._t.request(
            "DELETE", f"/companies/{seg(company_id)}/service-favorites/{seg(favorite_id)}"
        )
