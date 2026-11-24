"""Corvo client: construction, validation, and resource namespaces."""

from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse

import httpx

from .resources import (
    AccountantPackage,
    Billing,
    Certificates,
    Cnpj,
    Companies,
    Credits,
    Customers,
    DpsSequences,
    FiscalPortal,
    FiscalProfiles,
    Health,
    Imports,
    IntegrationConnections,
    IntegrationOperations,
    Integrations,
    InvoicePackage,
    Invoices,
    Plans,
    Schedules,
    ServiceFavorites,
    ServiceTaxProfiles,
    Webhooks,
)
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
            raise ValueError(f"Corvo: api_key is required — pass api_key or set {_ENV_API_KEY}")
        resolved_base = (base_url or os.environ.get(_ENV_BASE_URL) or DEFAULT_BASE_URL).rstrip("/")
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
        t = self._transport
        self.accountant_package = AccountantPackage(t)
        self.billing = Billing(t)
        self.certificates = Certificates(t)
        self.cnpj = Cnpj(t)
        self.companies = Companies(t)
        self.credits = Credits(t)
        self.customers = Customers(t)
        self.dps_sequence = DpsSequences(t)
        self.fiscal_portal = FiscalPortal(t)
        self.fiscal_profiles = FiscalProfiles(t)
        self.health = Health(t)
        self.imports = Imports(t)
        self.integration_connections = IntegrationConnections(t)
        self.integration_operations = IntegrationOperations(t)
        self.integrations = Integrations(t)
        self.invoice_package = InvoicePackage(t)
        self.invoices = Invoices(t)
        self.plans = Plans(t)
        self.schedules = Schedules(t)
        self.service_favorites = ServiceFavorites(t)
        self.service_tax_profiles = ServiceTaxProfiles(t)
        self.webhooks = Webhooks(t)

    @property
    def base_url(self) -> str:
        """Effective API root including the version prefix."""
        return self._transport.base_url

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool (unless one was injected)."""
        await self._transport.aclose()

    async def __aenter__(self) -> Corvo:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
