"""Invoices resource tests: flat resources, idempotency, pagination, binaries."""

from __future__ import annotations

import json

import httpx
import respx

from conftest import BASE_URL, collect, corvo
from corvo_nfse import Corvo

INVOICE_PROPS = {
    "id": "inv_1",
    "companyId": "c_1",
    "tenantId": "t_1",
    "environment": "test",
    "documentKeyVersion": 1,
    "emailSnapshot": {"send": True},
    "externalId": "order-42",
    "idempotencyKey": "order-42",
    "status": "authorized",
    "customerSnapshot": {"name": "Customer"},
    "serviceSnapshot": {"code": "010101"},
    "taxSnapshot": {},
    "amount": 150.5,
    "currency": "BRL",
    "competenceDate": "2026-10-12",
    "dpsId": None,
    "dpsSeries": None,
    "dpsNumber": None,
    "accessKey": "3526",
    "nfseNumber": 1,
    "fiscalProvider": "provider",
    "fiscalSchemaVersion": "1.00",
    "issuedAt": None,
    "authorizedAt": None,
    "lastErrorCode": None,
    "lastErrorMessage": None,
    "lastErrorProvider": None,
    "documentsReadyAt": None,
    "lastEmailStatus": None,
    "lastEmailSentAt": None,
    "createdAt": "2026-10-12T00:00:00Z",
    "updatedAt": "2026-10-12T00:00:00Z",
    "documentsStatus": "ready",
    "emailStatus": None,
    "stage": "authorized",
}


@respx.mock
async def test_create_sends_idempotency_key_and_returns_the_invoice(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(201, json={"data": INVOICE_PROPS})
    )
    data, error = await corvo.invoices.create(
        {
            "companyId": "c_1",
            "customer": {"name": "Customer", "taxId": "52998224725"},
            "service": {"code": "010101", "municipalityCode": "3170206", "description": "Services"},
            "amount": 150.5,
            "competenceDate": "2026-10-12",
        },
        idempotency_key="order-42",
    )
    assert error is None
    # The resource comes straight in `data`.
    assert data["id"] == "inv_1"
    assert "props" not in data
    request = route.calls[0].request
    assert request.headers["Idempotency-Key"] == "order-42"
    assert b'"competenceDate"' in request.content


@respx.mock
async def test_get_returns_the_invoice(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1").mock(
        return_value=httpx.Response(200, json={"data": INVOICE_PROPS})
    )
    data, error = await corvo.invoices.get("inv_1")
    assert error is None
    assert data["nfseNumber"] == 1


@respx.mock
async def test_list_returns_the_items(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [INVOICE_PROPS],
                "pagination": {"limit": 1, "hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.invoices.list(companyId="c_1", status="authorized", limit=1)
    assert error is None
    assert page["data"] == [INVOICE_PROPS]
    url = str(route.calls[0].request.url)
    assert "companyId=c_1" in url
    assert "status=authorized" in url


@respx.mock
async def test_list_from_param_maps_to_wire_from(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(
            200, json={"data": [], "pagination": {"hasMore": False}}
        )
    )
    await corvo.invoices.list(from_="2026-10-01", to="2026-10-31")
    url = str(route.calls[0].request.url)
    assert "from=2026-10-01" in url
    assert "to=2026-10-31" in url


@respx.mock
async def test_iterate_walks_pages(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/invoices").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [INVOICE_PROPS],
                    "pagination": {"hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**INVOICE_PROPS, "id": "inv_2"}],
                    "pagination": {"hasMore": False, "nextCursor": None},
                },
            ),
        ]
    )
    items = await collect(corvo.invoices.iterate(companyId="c_1"))
    assert [item["id"] for item in items] == ["inv_1", "inv_2"]
    assert "cursor=cur_2" in str(route.calls[1].request.url)


@respx.mock
async def test_events(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/invoices/inv_1/events").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                            "id": "evt_1",
                            "invoiceId": "inv_1",
                            "fromStatus": "queued",
                            "toStatus": "authorized",
                            "reason": None,
                            "createdAt": "2026-10-12T00:00:00Z",
                        }
                ],
                "pagination": {"hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.invoices.events("inv_1", limit=10)
    assert error is None
    assert page["data"][0]["toStatus"] == "authorized"
    assert "limit=10" in str(route.calls[0].request.url)


@respx.mock
async def test_pdf_download(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1/pdf").mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF-1.4",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": 'attachment; filename="nfse.pdf"',
            },
        )
    )
    file, error = await corvo.invoices.pdf("inv_1")
    assert error is None
    assert file.content == b"%PDF-1.4"
    assert file.mime_type == "application/pdf"
    assert file.file_name == "nfse.pdf"


@respx.mock
async def test_xml_download(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1/xml").mock(
        return_value=httpx.Response(
            200,
            content=b"<NFe/>",
            headers={
                "Content-Type": "application/xml",
                "Content-Disposition": 'attachment; filename="nfse.xml"',
            },
        )
    )
    file, error = await corvo.invoices.xml("inv_1")
    assert error is None
    assert file.content == b"<NFe/>"


@respx.mock
async def test_download_url(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices/inv_1/download-url").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "downloadUrl": "https://cdn/x.pdf",
                    "expiresAt": "2026-10-12T01:00:00Z",
                    "fileName": "x.pdf",
                    "mimeType": "application/pdf",
                }
            },
        )
    )
    data, error = await corvo.invoices.download_url("inv_1", "pdf")
    assert error is None
    assert data["fileName"] == "x.pdf"
    assert json.loads(route.calls[0].request.content) == {"format": "pdf"}


@respx.mock
async def test_send_email_with_idempotency_key(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices/inv_1/email").mock(
        return_value=httpx.Response(
            200, json={"data": {"emailId": "em_1", "status": "queued"}}
        )
    )
    data, error = await corvo.invoices.send_email("inv_1", idempotency_key="mail-1")
    assert error is None
    assert data["status"] == "queued"
    assert route.calls[0].request.headers["Idempotency-Key"] == "mail-1"


CANCELLED_INVOICE = {
    **INVOICE_PROPS,
    "status": "cancelled",
    "cancellationReason": "issue_error",
    "cancellationDescription": "Wrong amount on the invoice",
    "cancelledAt": "2026-10-13T10:00:00Z",
    "cancellationRequestedAt": "2026-10-13T09:59:00Z",
}

CANCELLING_INVOICE = {
    **INVOICE_PROPS,
    "status": "cancelling",
    "cancellationReason": "service_not_provided",
    "cancellationDescription": "The service was never provided",
    "cancelledAt": None,
    "cancellationRequestedAt": "2026-10-13T09:59:00Z",
}


@respx.mock
async def test_cancel_sends_reason_and_description_and_returns_cancelled_invoice(
    corvo: Corvo,
) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices/inv_1/cancel").mock(
        return_value=httpx.Response(200, json={"data": CANCELLED_INVOICE})
    )
    data, error = await corvo.invoices.cancel(
        "inv_1", reason="issue_error", description="Wrong amount on the invoice"
    )
    assert error is None
    assert data["status"] == "cancelled"
    assert data["cancelledAt"] == "2026-10-13T10:00:00Z"
    assert data["cancellationReason"] == "issue_error"
    request = route.calls[0].request
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "reason": "issue_error",
        "description": "Wrong amount on the invoice",
    }


@respx.mock
async def test_cancel_omits_description_when_not_given(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices/inv_1/cancel").mock(
        return_value=httpx.Response(200, json={"data": CANCELLED_INVOICE})
    )
    _, error = await corvo.invoices.cancel("inv_1", reason="other")
    assert error is None
    assert json.loads(route.calls[0].request.content) == {"reason": "other"}


@respx.mock
async def test_cancel_202_returns_cancelling_invoice(corvo: Corvo) -> None:
    respx.post(f"{BASE_URL}/v1/invoices/inv_1/cancel").mock(
        return_value=httpx.Response(202, json={"data": CANCELLING_INVOICE})
    )
    data, error = await corvo.invoices.cancel(
        "inv_1",
        reason="service_not_provided",
        description="The service was never provided",
    )
    assert error is None
    assert data["status"] == "cancelling"
    assert data["cancelledAt"] is None
    assert data["cancellationRequestedAt"] == "2026-10-13T09:59:00Z"


@respx.mock
async def test_cancel_409_returns_not_cancellable_error(corvo: Corvo) -> None:
    respx.post(f"{BASE_URL}/v1/invoices/inv_1/cancel").mock(
        return_value=httpx.Response(
            409,
            json={
                "code": "ERROR_INVOICE_NOT_CANCELLABLE",
                "message": "Invoice cannot be cancelled in status manual_review",
            },
        )
    )
    data, error = await corvo.invoices.cancel("inv_1", reason="other")
    assert data is None
    assert error is not None
    assert error.status == 409
    assert error.code == "ERROR_INVOICE_NOT_CANCELLABLE"


@respx.mock
async def test_cancel_422_returns_validation_error(corvo: Corvo) -> None:
    respx.post(f"{BASE_URL}/v1/invoices/inv_1/cancel").mock(
        return_value=httpx.Response(
            422, json={"code": "ERROR_VALIDATION", "message": "description is too short"}
        )
    )
    data, error = await corvo.invoices.cancel(
        "inv_1", reason="issue_error", description="short"
    )
    assert data is None
    assert error is not None
    assert error.status == 422
    assert error.code == "ERROR_VALIDATION"


@respx.mock
async def test_get_parses_a_cancelled_invoice(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1").mock(
        return_value=httpx.Response(200, json={"data": CANCELLED_INVOICE})
    )
    data, error = await corvo.invoices.get("inv_1")
    assert error is None
    assert data["status"] == "cancelled"
    assert data["cancellationReason"] == "issue_error"
    assert data["cancellationDescription"] == "Wrong amount on the invoice"
    assert data["cancelledAt"] == "2026-10-13T10:00:00Z"
    assert data["cancellationRequestedAt"] == "2026-10-13T09:59:00Z"


@respx.mock
async def test_get_parses_a_cancelling_invoice(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1").mock(
        return_value=httpx.Response(200, json={"data": CANCELLING_INVOICE})
    )
    data, error = await corvo.invoices.get("inv_1")
    assert error is None
    assert data["status"] == "cancelling"
    assert data["cancellationReason"] == "service_not_provided"
    assert data["cancelledAt"] is None


def test_invoice_types_include_cancellation() -> None:
    from typing import get_args

    from corvo_nfse import Invoice, InvoiceCancellationReason, InvoiceStatus

    assert "cancelling" in get_args(InvoiceStatus)
    assert "cancelled" in get_args(InvoiceStatus)
    assert set(get_args(InvoiceCancellationReason)) == {
        "issue_error",
        "service_not_provided",
        "other",
    }
    for field in (
        "cancellationReason",
        "cancellationDescription",
        "cancelledAt",
        "cancellationRequestedAt",
    ):
        assert field in Invoice.__annotations__
