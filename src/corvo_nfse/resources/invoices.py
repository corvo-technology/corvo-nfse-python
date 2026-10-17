"""Invoices resource: create, calculate, get, list, iterate, events, pdf, xml, download_url, send_email."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Literal, Optional

from ..error import Result
from ..transport import DownloadedFile, Transport
from ..types.invoice import (
    Invoice,
    InvoiceCalculation,
    InvoiceCreateParams,
    InvoiceDownloadUrl,
    InvoiceEmailResult,
    InvoiceEvent,
    InvoiceStatus,
)


class Invoices:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def create(
        self,
        params: InvoiceCreateParams,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Result[Invoice]:
        return await self._t.request(
            "POST", "/invoices", json=params, idempotency_key=idempotency_key
        )

    async def calculate(self, params: InvoiceCreateParams) -> Result[InvoiceCalculation]:
        """Estimate the taxes of an invoice without issuing, storing or charging anything.

        A fiscal gap is not an error: the result has ``status == "blocked"``.
        """
        return await self._t.request("POST", "/invoices/calculate", json=params)

    async def get(self, invoice_id: str) -> Result[Invoice]:
        return await self._t.request("GET", f"/invoices/{invoice_id}")

    async def list(
        self,
        *,
        companyId: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        externalId: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page(
            "/invoices",
            self._list_query(
                companyId=companyId,
                status=status,
                from_=from_,
                to=to,
                externalId=externalId,
                limit=limit,
                cursor=cursor,
            ),
        )

    def iterate(
        self,
        *,
        companyId: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        externalId: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[Invoice]:
        """Yield every invoice across pages.

        Raises :class:`~corvo_nfse.CorvoApiError` on a page failure.
        """
        return self._t.iterate(
            "/invoices",
            self._list_query(
                companyId=companyId,
                status=status,
                from_=from_,
                to=to,
                externalId=externalId,
                limit=limit,
                cursor=cursor,
            ),
        )

    async def events(
        self,
        invoice_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        return await self._t.list_page(
            f"/invoices/{invoice_id}/events",
            {"limit": limit, "cursor": cursor},
        )

    async def pdf(self, invoice_id: str) -> Result[DownloadedFile]:
        return await self._t.request_raw("GET", f"/invoices/{invoice_id}/pdf")

    async def xml(self, invoice_id: str) -> Result[DownloadedFile]:
        return await self._t.request_raw("GET", f"/invoices/{invoice_id}/xml")

    async def download_url(
        self, invoice_id: str, format: Literal["pdf", "xml"] = "pdf"
    ) -> Result[InvoiceDownloadUrl]:
        return await self._t.request(
            "POST", f"/invoices/{invoice_id}/download-url", json={"format": format}
        )

    async def send_email(
        self, invoice_id: str, *, idempotency_key: Optional[str] = None
    ) -> Result[InvoiceEmailResult]:
        return await self._t.request(
            "POST", f"/invoices/{invoice_id}/email", idempotency_key=idempotency_key
        )

    @staticmethod
    def _list_query(
        *,
        companyId: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        externalId: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "companyId": companyId,
            "status": status,
            "from": from_,
            "to": to,
            "externalId": externalId,
            "limit": limit,
            "cursor": cursor,
        }
