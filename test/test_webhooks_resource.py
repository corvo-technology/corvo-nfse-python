"""Webhooks resource tests (configs + nested deliveries) and credits/billing."""

from __future__ import annotations

import httpx
import respx

from conftest import BASE_URL, collect, corvo
from corvo_nfse import Corvo

WEBHOOK = {
    "id": "wh_1",
    "url": "https://example.com/hook",
    "events": ["nfse.invoice.authorized"],
    "active": True,
    "createdAt": "2026-10-12T00:00:00Z",
    "updatedAt": "2026-10-12T00:00:00Z",
}


@respx.mock
async def test_list(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/webhooks").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [WEBHOOK],
                "pagination": {"hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.webhooks.list()
    assert error is None
    assert page["data"] == [WEBHOOK]


@respx.mock
async def test_create_returns_secret_once(corvo: Corvo) -> None:
    route = respx.post(f"{BASE_URL}/v1/webhooks").mock(
        return_value=httpx.Response(
            201, json={"data": {**WEBHOOK, "secret": "whsec_test_123"}}
        )
    )
    data, error = await corvo.webhooks.create(
        {"url": "https://example.com/hook", "events": ["nfse.invoice.authorized"]}
    )
    assert error is None
    assert data["secret"] == "whsec_test_123"
    assert b'"events"' in route.calls[0].request.content


@respx.mock
async def test_remove_and_test(corvo: Corvo) -> None:
    respx.delete(f"{BASE_URL}/v1/webhooks/wh_1").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )
    respx.post(f"{BASE_URL}/v1/webhooks/wh_1/test").mock(
        return_value=httpx.Response(200, json={"data": {"sent": True}})
    )
    deleted, delete_error = await corvo.webhooks.remove("wh_1")
    assert delete_error is None
    assert deleted == {"deleted": True}
    sent, send_error = await corvo.webhooks.test("wh_1")
    assert send_error is None
    assert sent == {"sent": True}


@respx.mock
async def test_deliveries_list_and_iterate(corvo: Corvo) -> None:
    delivery = {
        "id": "dlv_1",
        "tenantId": "t_1",
        "webhookConfigId": "wh_1",
        "eventType": "nfse.invoice.authorized",
        "environment": "test",
        "url": "https://example.com/hook",
        "payload": {},
        "statusCode": 204,
        "responseBody": None,
        "errorMessage": None,
        "status": "delivered",
        "durationMs": 12,
        "retryCount": 0,
        "nextRetryAt": None,
        "lastError": None,
        "createdAt": "2026-10-12T00:00:00Z",
    }
    route = respx.get(f"{BASE_URL}/v1/webhooks/deliveries").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [delivery],
                    "pagination": {"hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [delivery],
                    "pagination": {"hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**delivery, "id": "dlv_2"}],
                    "pagination": {"hasMore": False, "nextCursor": None},
                },
            ),
        ]
    )
    page, error = await corvo.webhooks.deliveries.list(hours=24, environment="test")
    assert error is None
    assert page["data"][0]["id"] == "dlv_1"
    items = await collect(corvo.webhooks.deliveries.iterate(hours=24, environment="test"))
    assert [item["id"] for item in items] == ["dlv_1", "dlv_2"]
    for call in route.calls:
        url = str(call.request.url)
        assert "hours=24" in url
        assert "environment=test" in url


@respx.mock
async def test_deliveries_stats(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/webhooks/deliveries/stats").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "total": 5,
                    "sent": 4,
                    "failed": 1,
                    "pending": 0,
                    "delayed": 0,
                }
            },
        )
    )
    data, error = await corvo.webhooks.deliveries.stats(hours=24)
    assert error is None
    assert data["sent"] == 4
    assert "hours=24" in str(route.calls[0].request.url)


@respx.mock
async def test_deliveries_retry(corvo: Corvo) -> None:
    respx.post(f"{BASE_URL}/v1/webhooks/deliveries/dlv_1/retry").mock(
        return_value=httpx.Response(200, json={"data": {"retried": True}})
    )
    data, error = await corvo.webhooks.deliveries.retry("dlv_1")
    assert error is None
    assert data == {"retried": True}


@respx.mock
async def test_credits_balance(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/credits").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "tenantId": "t_1",
                    "balance": 100,
                    "overageUnits": 0,
                    "overageAmountCents": 0,
                    "hardLimit": None,
                }
            },
        )
    )
    data, error = await corvo.credits.balance()
    assert error is None
    assert data["balance"] == 100


@respx.mock
async def test_credits_plans_unwrap_props(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/credits/plans").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"props": {"id": "plan_1", "slug": "pro"}}],
                "pagination": {"hasMore": False, "nextCursor": None},
            },
        )
    )
    page, error = await corvo.credits.plans()
    assert error is None
    assert page["data"] == [{"id": "plan_1", "slug": "pro"}]


@respx.mock
async def test_credits_history_and_iterate(corvo: Corvo) -> None:
    route = respx.get(f"{BASE_URL}/v1/credits/history").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"props": {"id": "tx_1"}}],
                    "pagination": {"hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"props": {"id": "tx_1"}}],
                    "pagination": {"hasMore": True, "nextCursor": "cur_2"},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"props": {"id": "tx_2"}}],
                    "pagination": {"hasMore": False, "nextCursor": None},
                },
            ),
        ]
    )
    page, error = await corvo.credits.history(limit=1)
    assert error is None
    assert page["data"] == [{"id": "tx_1"}]
    items = await collect(corvo.credits.iterate_history(limit=1))
    assert [item["id"] for item in items] == ["tx_1", "tx_2"]
    assert "cursor=cur_2" in str(route.calls[2].request.url)


@respx.mock
async def test_billing_plan_keeps_server_snake_case(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/billing/plan").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "plan": {
                        "slug": "pro",
                        "name": "Pro",
                        "monthly_allowance": 1000,
                        "daily_limit": None,
                        "max_active_companies": 5,
                        "monthly_price_cents": 4900,
                    },
                    "subscription": {
                        "status": "active",
                        "paid_until": None,
                        "cancel_at_period_end": False,
                        "scheduled_plan": None,
                        "blocked": False,
                    },
                    "usage": {
                        "overage_units": 0,
                        "overage_amount_cents": 0,
                        "hard_limit": None,
                        "credits_used": 1,
                        "credits_reserved": 0,
                        "credits_remaining": 999,
                        "monthly_allowance": 1000,
                        "daily_usage": 0,
                        "daily_limit": None,
                        "active_companies": 1,
                        "max_active_companies": 5,
                        "period_start": None,
                        "period_end": None,
                    },
                }
            },
        )
    )
    data, error = await corvo.billing.plan()
    assert error is None
    assert data["plan"]["monthly_allowance"] == 1000
    assert data["subscription"]["cancel_at_period_end"] is False


@respx.mock
async def test_billing_usage(corvo: Corvo) -> None:
    respx.get(f"{BASE_URL}/v1/billing/usage").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "canEmit": True,
                    "creditsRemaining": 999,
                    "creditsUsed": 1,
                    "creditsReserved": 0,
                    "monthlyAllowance": 1000,
                    "dailyUsage": 0,
                    "dailyLimit": None,
                    "activeCompanies": 1,
                    "maxActiveCompanies": 5,
                    "periodStart": None,
                    "periodEnd": None,
                }
            },
        )
    )
    data, error = await corvo.billing.usage()
    assert error is None
    assert data["canEmit"] is True
