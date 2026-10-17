"""Transport unit tests: URL building, headers, envelope, error mapping."""

from __future__ import annotations

import httpx
import pytest
import respx

from conftest import API_KEY, BASE_URL, collect  # noqa: F401
from corvo_nfse import CorvoApiError
from corvo_nfse.transport import Transport, unwrap


def make_transport() -> Transport:
    return Transport(api_key=API_KEY, base_url=BASE_URL)


def test_base_url_includes_prefix() -> None:
    t = make_transport()
    assert t.base_url == "https://api.corvo.tech/v1"
    t2 = Transport(api_key=API_KEY, base_url="https://x.example.com/", prefix="/custom/")
    assert t2.base_url == "https://x.example.com/custom"


def test_unwrap_modes() -> None:
    assert unwrap({"data": {"id": "1"}}, "data") == {"id": "1"}
    assert unwrap({"data": None}, "data") is None
    assert unwrap({}, "data") is None
    body = {"data": [1, 2], "pagination": {"hasMore": False}}
    assert unwrap(body, "none") is body


@respx.mock
async def test_url_query_and_api_key_header() -> None:
    route = respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {"hasMore": False}})
    )
    t = make_transport()
    page, error = await t.list_page("/companies", {"limit": 10})
    assert error is None
    request = route.calls[0].request
    assert str(request.url) == f"{BASE_URL}/v1/companies?limit=10"
    assert request.headers["X-API-Key"] == API_KEY
    assert request.headers["Accept"] == "application/json"
    assert request.headers.get("Authorization") is None
    assert page == {"data": [], "pagination": {"hasMore": False}}


@respx.mock
async def test_none_query_params_are_dropped() -> None:
    route = respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(200, json={"data": [], "pagination": {}})
    )
    t = make_transport()
    await t.list_page("/companies", {"limit": None, "cursor": "abc"})
    assert str(route.calls[0].request.url) == f"{BASE_URL}/v1/companies?cursor=abc"


@respx.mock
async def test_idempotency_key_header() -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    t = make_transport()
    await t.request("POST", "/invoices", json={"a": 1}, idempotency_key="order-42")
    request = route.calls[0].request
    assert request.headers["Idempotency-Key"] == "order-42"
    assert request.headers["Content-Type"] == "application/json"


@respx.mock
async def test_json_body_pass_through_no_recasing() -> None:
    route = respx.post(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    t = make_transport()
    body = {"legalName": "ACME LTDA", "taxId": "52998224725", "taxRegime": "Simples Nacional"}
    await t.request("POST", "/companies", json=body)
    sent = route.calls[0].request.content
    assert b'"legalName"' in sent
    assert b'"taxRegime"' in sent
    assert b'"legal_name"' not in sent


@respx.mock
async def test_envelope_data() -> None:
    respx.get(f"{BASE_URL}/v1/companies/c_1").mock(
        return_value=httpx.Response(200, json={"data": {"id": "c_1"}})
    )
    t = make_transport()
    data, error = await t.request("GET", "/companies/c_1")
    assert error is None
    assert data == {"id": "c_1"}


@respx.mock
async def test_204_returns_none() -> None:
    respx.delete(f"{BASE_URL}/v1/companies/c_1").mock(return_value=httpx.Response(204))
    t = make_transport()
    data, error = await t.request("DELETE", "/companies/c_1")
    assert (data, error) == (None, None)


@respx.mock
async def test_empty_body_returns_none() -> None:
    respx.get(f"{BASE_URL}/v1/health/live").mock(
        return_value=httpx.Response(200, content=b"")
    )
    t = make_transport()
    data, error = await t.request("GET", "/health/live", unwrap="none")
    assert (data, error) == (None, None)


@respx.mock
async def test_rest_error_mapping_400() -> None:
    respx.post(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(
            400,
            json={
                "statusCode": 400,
                "code": "ERROR_VALIDATION",
                "message": "Invalid payload",
                "details": [{"field": "amount", "code": "invalid", "message": "must be > 0"}],
                "requestId": "req_abc",
            },
            headers={"X-Request-Id": "req_abc"},
        )
    )
    t = make_transport()
    data, error = await t.request("POST", "/invoices", json={})
    assert data is None
    assert isinstance(error, CorvoApiError)
    assert error.status == 400
    assert error.code == "ERROR_VALIDATION"
    assert error.message == "Invalid payload"
    assert error.details == [{"field": "amount", "code": "invalid", "message": "must be > 0"}]
    assert error.request_id == "req_abc"


@respx.mock
async def test_error_code_falls_back_to_http_status() -> None:
    respx.get(f"{BASE_URL}/v1/companies/x").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    t = make_transport()
    _, error = await t.request("GET", "/companies/x")
    assert error is not None
    assert error.code == "http_404"
    assert error.request_id is None


@respx.mock
async def test_error_request_id_from_header() -> None:
    respx.get(f"{BASE_URL}/v1/companies/x").mock(
        return_value=httpx.Response(500, json={}, headers={"X-Request-Id": "req_hdr"})
    )
    t = make_transport()
    _, error = await t.request("GET", "/companies/x")
    assert error is not None
    assert error.request_id == "req_hdr"
    assert error.code == "http_500"


@respx.mock
async def test_429_retry_after_from_header() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(429, json={"code": "ERROR_RATE_LIMITED"}, headers={"Retry-After": "12"})
    )
    t = make_transport()
    _, error = await t.request("GET", "/companies")
    assert error is not None
    assert error.status == 429
    assert error.retry_after == 12


@respx.mock
async def test_429_retry_after_from_body() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(429, json={"retryAfter": 7, "message": "slow down"})
    )
    t = make_transport()
    _, error = await t.request("GET", "/companies")
    assert error is not None
    assert error.retry_after == 7


@respx.mock
async def test_non_json_error_body() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(502, content=b"<html>bad gateway</html>")
    )
    t = make_transport()
    _, error = await t.request("GET", "/companies")
    assert error is not None
    assert error.status == 502
    assert error.code == "http_502"
    assert error.message == "Request failed with status 502"


@respx.mock
async def test_invalid_json_success_body() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(200, content=b"not json")
    )
    t = make_transport()
    data, error = await t.request("GET", "/companies")
    assert data is None
    assert error is not None
    assert error.code == "invalid_json"


@respx.mock
async def test_network_error_maps_to_tuple() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    t = make_transport()
    data, error = await t.request("GET", "/companies")
    assert data is None
    assert error is not None
    assert error.status == 0
    assert error.code == "network_error"


@respx.mock
async def test_timeout_maps_to_tuple() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(side_effect=httpx.ConnectTimeout("too slow"))
    t = make_transport()
    data, error = await t.request("GET", "/companies")
    assert data is None
    assert error is not None
    assert error.status == 0
    assert error.code == "timeout"


@respx.mock
async def test_iterate_walks_cursors() -> None:
    route = respx.get(f"{BASE_URL}/v1/companies").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "c_1"}],
                    "pagination": {"limit": 1, "hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"id": "c_2"}],
                    "pagination": {"limit": 1, "hasMore": False, "nextCursor": None},
                },
            ),
        ]
    )
    t = make_transport()
    items = await collect(t.iterate("/companies", {"limit": 1}))
    assert [item["id"] for item in items] == ["c_1", "c_2"]
    second_request_url = str(route.calls[1].request.url)
    assert "cursor=cur_2" in second_request_url


@respx.mock
async def test_iterate_honors_initial_cursor() -> None:
    route = respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(
            200,
            json={"data": [], "pagination": {"hasMore": False, "nextCursor": None}},
        )
    )
    t = make_transport()
    await collect(t.iterate("/companies", {"cursor": "start_here"}))
    assert "cursor=start_here" in str(route.calls[0].request.url)


@respx.mock
async def test_iterate_raises_on_failure() -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(400, json={"code": "ERROR_VALIDATION", "message": "bad"})
    )
    t = make_transport()
    with pytest.raises(CorvoApiError) as excinfo:
        await collect(t.iterate("/companies"))
    assert excinfo.value.code == "ERROR_VALIDATION"


@respx.mock
async def test_list_page_returns_the_items() -> None:
    respx.get(f"{BASE_URL}/v1/invoices").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "inv_1"}, {"id": "inv_2"}],
                "pagination": {"hasMore": False},
            },
        )
    )
    t = make_transport()
    page, error = await t.list_page("/invoices", {})
    assert error is None
    assert page["data"] == [{"id": "inv_1"}, {"id": "inv_2"}]


@respx.mock
async def test_request_raw_binary_download() -> None:
    respx.get(f"{BASE_URL}/v1/invoices/inv_1/pdf").mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF-1.4",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": 'attachment; filename="nfse-inv_1.pdf"',
            },
        )
    )
    t = make_transport()
    file, error = await t.request_raw("GET", "/invoices/inv_1/pdf")
    assert error is None
    assert file is not None
    assert file.content == b"%PDF-1.4"
    assert file.mime_type == "application/pdf"
    assert file.file_name == "nfse-inv_1.pdf"
