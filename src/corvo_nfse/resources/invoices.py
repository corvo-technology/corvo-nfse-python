"""Invoices resource: create, create_batch, calculate, get, list, iterate, events, pdf, xml, download_url, send_email, cancel, substitute, overview, review."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Literal, Optional

from ..error import Result
from ..transport import DownloadedFile, Transport, seg
from ..types.invoice import (
    Invoice,
    InvoiceBatchItem,
    InvoiceBatchSummary,
    InvoiceCalculation,
    InvoiceCancelParams,
    InvoiceCreateParams,
    InvoiceCreateResult,
    InvoiceDownloadUrl,
    InvoiceEmailResult,
    InvoiceOverview,
    InvoiceReviewParams,
    InvoiceReviewResult,
    InvoiceStatus,
    InvoiceSubstituteParams,
)


class Invoices:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def create(
        self,
        params: InvoiceCreateParams,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Result[InvoiceCreateResult]:
        """Issue an invoice, or schedule one. Answers ``202``.

        ``data`` is an :class:`Invoice` (``queued``) for ``options.type`` ``IMMEDIATE`` (the default)
        and a :class:`~corvo_nfse.types.models.Schedule` (snake_case fields) for ``SCHEDULE`` and
        ``RECURRING``: the note only exists when the schedule runs. Follow it with
        ``corvo.schedules.list_runs()``. Check ``"kind" in data`` (or ``"status" in data`` with
        ``"company_id" in data``) to tell them apart.
        """
        return await self._t.request(
            "POST", "/invoices", json=params, idempotency_key=idempotency_key
        )

    async def create_batch(self, invoices: List[InvoiceBatchItem]) -> Result[InvoiceBatchSummary]:
        """Issue 1 to 50 invoices in one call, for one company or several.

        Items are checked one by one: valid ones are saved together, invalid ones come back
        ``rejected`` and are not saved. Match ``results[i]["index"]`` to the item you sent, fix only
        the rejected ones and send them again. Send an ``idempotencyKey`` per item: the
        ``Idempotency-Key`` header is not used by this route.
        """
        return await self._t.request("POST", "/invoices/batches", json={"invoices": invoices})

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
        customerTaxId: Optional[str] = None,
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
                customerTaxId=customerTaxId,
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
        customerTaxId: Optional[str] = None,
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
                customerTaxId=customerTaxId,
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
        self,
        invoice_id: str,
        *,
        email: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Result[InvoiceEmailResult]:
        """Request the invoice e-mail. ``email`` sends to another address than the customer's."""
        return await self._t.request(
            "POST",
            f"/invoices/{invoice_id}/email",
            json={"email": email} if email else None,
            idempotency_key=idempotency_key,
        )

    async def substitute(
        self,
        invoice_id: str,
        params: InvoiceSubstituteParams,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Result[Invoice]:
        """Replace an authorized invoice with a corrected one. Answers ``202`` with the new invoice.

        Only ``description`` (why), ``service.description``, ``purchaseOrder`` and ``notes`` can
        change. Error ``ERROR_INVOICE_NOT_SUBSTITUTABLE`` when the invoice cannot be replaced.
        """
        return await self._t.request(
            "POST",
            f"/invoices/{seg(invoice_id)}/substitute",
            json=params,
            idempotency_key=idempotency_key,
        )

    async def overview(
        self, *, period: Optional[Literal["7d", "30d"]] = None
    ) -> Result[InvoiceOverview]:
        """Counts and daily activity for the key's environment (``7d`` by default)."""
        return await self._t.request("GET", "/invoices/overview", query={"period": period})

    async def review(self, params: InvoiceReviewParams) -> Result[InvoiceReviewResult]:
        """Resolve invoices in ``manual_review`` (up to 100): retry or discard. Answers ``202``."""
        return await self._t.request("POST", "/invoices/review", json=params)

    async def cancel(self, invoice_id: str, params: InvoiceCancelParams) -> Result[Invoice]:
        """Cancel an invoice.

        A queued invoice is cancelled at once (``status == "cancelled"``); an authorized one moves to
        ``cancelling`` while the cancellation is processed, and a processing one stays ``processing``
        with ``cancellationRequestedAt`` set. Call :meth:`get` later: ``cancelled`` when done, or back
        to ``authorized`` with ``lastErrorCode`` when the cancellation was rejected.
        """
        return await self._t.request("POST", f"/invoices/{invoice_id}/cancel", json=params)

    @staticmethod
    def _list_query(
        *,
        companyId: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        externalId: Optional[str] = None,
        customerTaxId: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "companyId": companyId,
            "status": status,
            "from": from_,
            "to": to,
            "externalId": externalId,
            "customerTaxId": customerTaxId,
            "limit": limit,
            "cursor": cursor,
        }
