"""Corvo client: construction, validation, and resource namespaces."""

from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse

import httpx

from .resources.billing import Billing
from .resources.certificates import Certificates
from .resources.companies import Companies
from .resources.credits import Credits
from .resources.health import Health
from .resources.invoices import Invoices
from .resources.webhooks import Webhooks
from .transport import DEFAULT_BASE_URL, DEFAULT_PREFIX, DEFAULT_TIMEOUT, Transport, is_private_host

_ENV_API_KEY = "CORVO_API_KEY"
_ENV_BASE_URL = "CORVO_BASE_URL"


class Corvo:
    """Entry point for the Corvo NFS-e API.

    ::

        corvo = Corvo(api_key="corvo_live_xxx")  # or CORVO_API_KEY env
        companies, error = await corvo.companies.list(limit=10)

    Usage as an async context manager closes the underlying HTTP client::

        async with Corvo(api_key="...") as corvo:
            ...
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        prefix: str = DEFAULT_PREFIX,
        timeout: float = DEFAULT_TIMEOUT,
        allow_insecure_http: bool = False,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        resolved_key = api_key or os.environ.get(_ENV_API_KEY)
        if not resolved_key:
            raise ValueError(
                f"Corvo: api_key is required — pass api_key or set {_ENV_API_KEY}"
            )
        resolved_base = (
            base_url or os.environ.get(_ENV_BASE_URL) or DEFAULT_BASE_URL
        ).rstrip("/")
        parsed = urlparse(resolved_base)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError(f"Corvo: invalid base_url: {resolved_base}")
        if (
            parsed.scheme == "http"
            and not allow_insecure_http
            and not is_private_host(parsed.hostname)
        ):
            raise ValueError(
                "Corvo: http:// is only allowed for loopback/private hosts "
                f"(got {parsed.hostname}). Use https:// or pass allow_insecure_http=True."
            )
        self._transport = Transport(
            api_key=resolved_key,
            base_url=resolved_base,
            prefix=prefix,
            timeout=timeout,
            client=http_client,
        )
        self.billing = Billing(self._transport)
        self.certificates = Certificates(self._transport)
        self.companies = Companies(self._transport)
        self.credits = Credits(self._transport)
        self.health = Health(self._transport)
        self.invoices = Invoices(self._transport)
        self.webhooks = Webhooks(self._transport)

    @property
    def base_url(self) -> str:
        """Effective API root including the version prefix."""
        return self._transport.base_url

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool (unless one was injected)."""
        await self._transport.aclose()

    async def __aenter__(self) -> "Corvo":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
