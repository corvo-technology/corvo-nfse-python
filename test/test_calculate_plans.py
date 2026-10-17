"""invoices.calculate and the public plans catalog."""

from __future__ import annotations

import json

import httpx
import respx

from conftest import BASE_URL
from corvo_nfse import Corvo


@respx.mock
async def test_calculate_returns_the_estimate_without_issuing(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/invoices/calculate").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "preEmission": True,
                    "status": "ready",
                    "taxes": {
                        "iss": {"base": "15000.00", "rate": "3", "amount": "450.00"},
                        "ibsTotal": {"base": "14550.00", "amount": "14.55"},
                    },
                    "netReceivableAmount": "15000.00",
                    "blocking": None,
                }
            },
        )
    )
    data, error = await corvo.invoices.calculate(
        {
            "companyTaxId": "11222333000181",
            "service": {},
            "amount": 15000,
            "competenceDate": "2026-10-16",
        }
    )
    assert error is None
    assert data is not None
    assert data["status"] == "ready"
    assert data["taxes"]["iss"]["amount"] == "450.00"
    assert "rate" not in data["taxes"]["ibsTotal"]
    body = json.loads(route.calls.last.request.content)
    assert "customer" not in body  # the customer is optional


@respx.mock
async def test_calculate_blocked_is_data_not_an_error(corvo: Corvo) -> None:
    respx.post(f"{BASE_URL}/v1/invoices/calculate").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "status": "blocked",
                    "blocking": {"code": "TAX_RATE_NOT_FOUND", "message": "x", "step": "s"},
                    "pendingFields": [{"field": "iss.rate", "reason": "missing"}],
                }
            },
        )
    )
    data, error = await corvo.invoices.calculate(
        {"service": {}, "amount": 10, "competenceDate": "2026-10-16"}
    )
    assert error is None
    assert data is not None and data["blocking"]["code"] == "TAX_RATE_NOT_FOUND"


@respx.mock
async def test_plans_catalog(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/plans", params={"limit": "5"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"slug": "developer", "monthlyAllowance": 200}],
                "pagination": {"limit": 5, "hasMore": False, "nextCursor": None},
            },
        )
    )
    respx.get(f"{BASE_URL}/v1/plans/growth").mock(
        return_value=httpx.Response(200, json={"data": {"slug": "growth", "monthlyTotalCents": 8990}})
    )
    respx.get(f"{BASE_URL}/v1/plans/quote", params={"volume": "20000"}).mock(
        return_value=httpx.Response(200, json={"data": {"recommended_plan": "volume"}})
    )

    page, error = await corvo.plans.list(limit=5)
    assert error is None and page is not None
    assert page["data"][0]["slug"] == "developer"
    plan, error = await corvo.plans.get("growth")
    assert error is None and plan is not None and plan["monthlyTotalCents"] == 8990
    quote, error = await corvo.plans.quote(20000)
    assert error is None and quote is not None and quote["recommended_plan"] == "volume"


@respx.mock
async def test_plans_quote_is_none_for_an_invalid_volume(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/plans/quote").mock(return_value=httpx.Response(200, json={"data": None}))
    quote, error = await corvo.plans.quote(0)
    assert error is None
    assert quote is None
