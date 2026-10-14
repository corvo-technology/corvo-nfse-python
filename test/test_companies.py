"""Companies resource tests."""

from __future__ import annotations

import httpx
import respx

from conftest import BASE_URL, collect, corvo
from corvo_nfse import Corvo

COMPANY = {
    "id": "c_1",
    "tenantId": "t_1",
    "legalName": "ACME LTDA",
    "tradeName": "ACME",
    "taxId": "52998224725",
    "municipalReg": None,
    "municipalityCode": "3170206",
    "taxRegime": "Simples Nacional",
    "simpleNational": True,
    "specialRegime": None,
    "addressStreet": "Rua A",
    "addressNumber": "1",
    "addressComplement": None,
    "addressDistrict": "Centro",
    "addressCity": "Belo Horizonte",
    "addressState": "MG",
    "addressZip": "30000-000",
    "fiscalSchemaVersion": "1.00",
    "environment": "test",
    "status": "active",
    "createdAt": "2026-10-12T00:00:00Z",
    "updatedAt": "2026-10-12T00:00:00Z",
    "deletedAt": None,
    "setupGaps": [],
}


@respx.mock
async def test_create_posts_camelcase_body(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(201, json={"data": COMPANY})
    )
    data, error = await corvo.companies.create(
        {"legalName": "ACME LTDA", "taxId": "52998224725", "taxRegime": "Simples Nacional"}
    )
    assert error is None
    assert data["id"] == "c_1"
    sent = route.calls[0].request.content
    assert b'"legalName"' in sent
    assert b'"taxId"' in sent


@respx.mock
async def test_list_returns_page_envelope(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/companies").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [COMPANY],
                "pagination": {"limit": 1, "hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.companies.list(limit=1)
    assert error is None
    assert page["data"] == [COMPANY]
    assert page["pagination"]["hasMore"] is False


@respx.mock
async def test_get_update(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/companies/c_1").mock(
        return_value=httpx.Response(200, json={"data": COMPANY})
    )
    respx.patch(f"{BASE_URL}/v1/companies/c_1").mock(
        return_value=httpx.Response(200, json={"data": {**COMPANY, "tradeName": "NEW"}})
    )
    data, error = await corvo.companies.get("c_1")
    assert error is None
    assert data["id"] == "c_1"
    updated, update_error = await corvo.companies.update("c_1", {"tradeName": "NEW"})
    assert update_error is None
    assert updated["tradeName"] == "NEW"


@respx.mock
async def test_remove_204(corvo: Corvo) -> None:
    respx.delete(f"{BASE_URL}/v1/companies/c_1").mock(return_value=httpx.Response(204))
    data, error = await corvo.companies.remove("c_1")
    assert (data, error) == (None, None)


@respx.mock
async def test_iterate_walks_two_pages(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/companies").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [COMPANY],
                    "pagination": {"limit": 1, "hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**COMPANY, "id": "c_2"}],
                    "pagination": {"limit": 1, "hasMore": False, "nextCursor": None},
                },
            ),
        ]
    )
    items = await collect(corvo.companies.iterate(limit=1))
    assert [item["id"] for item in items] == ["c_1", "c_2"]
    assert "cursor=cur_2" in str(route.calls[1].request.url)
