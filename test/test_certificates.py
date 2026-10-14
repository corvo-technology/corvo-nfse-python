"""Certificates resource tests: multipart upload, list, remove."""

from __future__ import annotations

import httpx
import respx

from conftest import BASE_URL, corvo
from corvo_nfse import Corvo

CERT = {
    "id": "cert_1",
    "companyId": "c_1",
    "serialNumber": "01",
    "issuer": "ACME",
    "subject": "ACME",
    "fingerprint": "ab:cd",
    "validFrom": "2026-01-01",
    "validUntil": "2027-01-01",
    "status": "active",
    "createdAt": "2026-10-12T00:00:00Z",
}


@respx.mock
async def test_upload_builds_multipart(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/companies/c_1/certificates").mock(
        return_value=httpx.Response(201, json={"data": CERT})
    )
    data, error = await corvo.certificates.upload("c_1", b"\x30\x82fake-p12", "secret-pw")
    assert error is None
    assert data["id"] == "cert_1"
    request = route.calls[0].request
    content_type = request.headers["Content-Type"]
    # httpx sets the multipart boundary itself; the SDK must not force it.
    assert content_type.startswith("multipart/form-data; boundary=")
    body = request.content
    assert b"secret-pw" in body
    assert b"certificate.p12" in body
    assert b"\x30\x82fake-p12" in body


@respx.mock
async def test_upload_custom_file_name(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/companies/c_1/certificates").mock(
        return_value=httpx.Response(201, json={"data": CERT})
    )
    _, error = await corvo.certificates.upload(
        "c_1", b"bytes", "pw", file_name="cert-brazil.pfx"
    )
    assert error is None
    assert b"cert-brazil.pfx" in route.calls[0].request.content


@respx.mock
async def test_list(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/companies/c_1/certificates").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [CERT],
                "pagination": {"limit": 50, "hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.certificates.list("c_1", limit=50)
    assert error is None
    assert page["data"] == [CERT]
    assert "limit=50" in str(route.calls[0].request.url)


@respx.mock
async def test_remove(corvo: Corvo) -> None:
    respx.delete(f"{BASE_URL}/v1/companies/c_1/certificates/cert_1").mock(
        return_value=httpx.Response(204)
    )
    data, error = await corvo.certificates.remove("c_1", "cert_1")
    assert (data, error) == (None, None)
