"""Webhooks resource — list, create, remove, test + nested deliveries."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Literal, Optional

from ..error import Result
from ..transport import Transport
from ..types.webhook import (
    Webhook,
    WebhookCreateParams,
    WebhookDelivery,
    WebhookDeliveryStats,
    WebhookWithSecret,
)


class Deliveries:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        hours: Optional[int] = None,
        environment: Optional[Literal["test", "live"]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page(
            "/webhooks/deliveries",
            self._query(
                hours=hours, environment=environment, limit=limit, cursor=cursor
            ),
        )

    def iterate(
        self,
        *,
        hours: Optional[int] = None,
        environment: Optional[Literal["test", "live"]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[WebhookDelivery]:
        """Yield every delivery across pages.

        Raises :class:`~corvo_nfse.CorvoApiError` on a page failure.
        """
        return self._t.iterate(
            "/webhooks/deliveries",
            self._query(
                hours=hours, environment=environment, limit=limit, cursor=cursor
            ),
        )

    async def stats(
        self,
        *,
        hours: Optional[int] = None,
        environment: Optional[Literal["test", "live"]] = None,
    ) -> Result[WebhookDeliveryStats]:
        query: Dict[str, Any] = {"hours": hours, "environment": environment}
        return await self._t.request("GET", "/webhooks/deliveries/stats", query=query)

    async def retry(self, delivery_id: str) -> Result[Dict[str, bool]]:
        return await self._t.request("POST", f"/webhooks/deliveries/{delivery_id}/retry")

    @staticmethod
    def _query(
        *,
        hours: Optional[int] = None,
        environment: Optional[Literal["test", "live"]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "hours": hours,
            "environment": environment,
            "limit": limit,
            "cursor": cursor,
        }


class Webhooks:
    def __init__(self, transport: Transport) -> None:
        self._t = transport
        self.deliveries = Deliveries(transport)

    async def list(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page("/webhooks", {"limit": limit, "cursor": cursor})

    def iterate(
        self, *, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> AsyncIterator[Webhook]:
        """Yield every webhook config across pages.

        Raises :class:`~corvo_nfse.CorvoApiError` on a page failure.
        """
        return self._t.iterate("/webhooks", {"limit": limit, "cursor": cursor})

    async def create(self, params: WebhookCreateParams) -> Result[WebhookWithSecret]:
        """Create a webhook. The ``secret`` is returned once, at creation."""
        return await self._t.request("POST", "/webhooks", json=params)

    async def remove(self, webhook_id: str) -> Result[Dict[str, bool]]:
        return await self._t.request("DELETE", f"/webhooks/{webhook_id}")

    async def test(self, webhook_id: str) -> Result[Dict[str, bool]]:
        return await self._t.request("POST", f"/webhooks/{webhook_id}/test")
