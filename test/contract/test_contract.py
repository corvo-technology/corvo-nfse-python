"""Optional contract test — runs only with CORVO_API_KEY + CORVO_BASE_URL set.

Not part of default CI. Skips automatically otherwise.
"""

from __future__ import annotations

import os

import pytest

from corvo_nfse import Corvo

API_KEY = os.environ.get("CORVO_API_KEY")
BASE_URL = os.environ.get("CORVO_BASE_URL")

pytestmark = pytest.mark.skipif(
    not (API_KEY and BASE_URL),
    reason="contract test requires CORVO_API_KEY and CORVO_BASE_URL",
)


async def test_health_live_and_companies_list() -> None:
    assert API_KEY is not None
    assert BASE_URL is not None
    async with Corvo(api_key=API_KEY, base_url=BASE_URL) as corvo:
        live, live_error = await corvo.health.live()
        assert live_error is None
        assert live is not None

        page, list_error = await corvo.companies.list(limit=1)
        assert list_error is None
        assert page is not None
        assert "data" in page
        assert "pagination" in page
