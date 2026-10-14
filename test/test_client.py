"""Client construction: validation, env fallbacks, health passthrough."""

from __future__ import annotations

import httpx
import pytest
import respx

from conftest import API_KEY, BASE_URL
from corvo_nfse import Corvo


def test_missing_api_key_raises() -> None:
    with pytest.raises(ValueError, match="api_key is required"):
        Corvo(api_key=None)


def test_env_api_key_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORVO_API_KEY", API_KEY)
    client = Corvo()
    assert client.base_url == "https://api.corvo.tech/v1"


def test_env_base_url_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORVO_API_KEY", API_KEY)
    monkeypatch.setenv("CORVO_BASE_URL", "https://corvo.internal.example/")
    client = Corvo()
    assert client.base_url == "https://corvo.internal.example/v1"


def test_default_base_url() -> None:
    client = Corvo(api_key=API_KEY)
    assert client.base_url == "https://api.corvo.tech/v1"


def test_prefix_option() -> None:
    client = Corvo(api_key=API_KEY, base_url="https://corvo.example.com", prefix="api/v2")
    assert client.base_url == "https://corvo.example.com/api/v2"


def test_http_public_host_rejected() -> None:
    with pytest.raises(ValueError, match="http://"):
        Corvo(api_key=API_KEY, base_url="http://api.corvo.tech")


def test_http_private_host_allowed() -> None:
    client = Corvo(api_key=API_KEY, base_url="http://10.0.0.5")
    assert client.base_url == "http://10.0.0.5/v1"
    client2 = Corvo(api_key=API_KEY, base_url="http://localhost:3000")
    assert client2.base_url == "http://localhost:3000/v1"


def test_http_public_host_allowed_with_flag() -> None:
    client = Corvo(api_key=API_KEY, base_url="http://api.corvo.tech", allow_insecure_http=True)
    assert client.base_url == "http://api.corvo.tech/v1"


def test_invalid_base_url() -> None:
    with pytest.raises(ValueError, match="invalid base_url"):
        Corvo(api_key=API_KEY, base_url="not-a-url")


def test_namespaces_mounted() -> None:
    client = Corvo(api_key=API_KEY)
    for name in ("billing", "certificates", "companies", "credits", "health", "invoices", "webhooks"):
        assert hasattr(client, name)
    assert hasattr(client.webhooks, "deliveries")


@respx.mock
async def test_health_live_raw_passthrough() -> None:
    respx.get(f"{BASE_URL}/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = Corvo(api_key=API_KEY)
    data, error = await client.health.live()
    assert error is None
    assert data == {"status": "ok"}


@respx.mock
async def test_health_ready_raw_passthrough() -> None:
    respx.get(f"{BASE_URL}/v1/health/ready").mock(
        return_value=httpx.Response(200, json={"status": "ready", "checks": ["db"]})
    )
    client = Corvo(api_key=API_KEY)
    data, error = await client.health.ready()
    assert error is None
    assert data == {"status": "ready", "checks": ["db"]}


async def test_context_manager_closes() -> None:
    async with Corvo(api_key=API_KEY) as client:
        assert isinstance(client._transport.client, httpx.AsyncClient)
