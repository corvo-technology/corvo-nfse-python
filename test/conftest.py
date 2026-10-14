"""Shared fixtures and helpers for the corvo-nfse test suite."""

from __future__ import annotations

from typing import Any, AsyncIterator, List

import pytest

from corvo_nfse import Corvo

API_KEY = "corvo_test_0123456789abcdef0123456789abcdef01234567"
BASE_URL = "https://api.corvo.tech"


@pytest.fixture
def corvo() -> Corvo:
    return Corvo(api_key=API_KEY, base_url=BASE_URL)


async def collect(iterator: AsyncIterator[Any]) -> List[Any]:
    """Drain an async generator into a list."""
    return [item async for item in iterator]
