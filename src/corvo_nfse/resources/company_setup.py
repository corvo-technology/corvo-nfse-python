"""Company setup: DPS numbering, fiscal profiles and service tax profiles."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..error import Result
from ..transport import Transport, seg
from ..types.company import (
    DpsSequence,
    DpsSequenceSetParams,
    FiscalProfile,
    FiscalProfileUpsertParams,
    ServiceTaxProfile,
    ServiceTaxProfileCreateParams,
    ServiceTaxProfileUpdateParams,
)


class DpsSequences:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def get(self, company_id: str) -> Result[DpsSequence]:
        return await self._t.request("GET", f"/companies/{seg(company_id)}/dps-sequence")

    async def set(self, company_id: str, params: DpsSequenceSetParams) -> Result[DpsSequence]:
        """Continue the DPS numbering from the last note issued elsewhere.

        Error ``DPS_NUMBER_BELOW_CURRENT`` when the number is lower than the current one.
        """
        return await self._t.request(
            "PUT", f"/companies/{seg(company_id)}/dps-sequence", json=params
        )


class FiscalProfiles:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self, company_id: str) -> Result[List[FiscalProfile]]:
        """The fiscal profile history of the company."""
        return await self._t.request("GET", f"/companies/{seg(company_id)}/fiscal-profile")

    async def upsert(
        self, company_id: str, params: FiscalProfileUpsertParams
    ) -> Result[FiscalProfile]:
        """Create a validity period (idempotent for an identical desired state)."""
        return await self._t.request(
            "PUT", f"/companies/{seg(company_id)}/fiscal-profile", json=params
        )

    async def approve(self, company_id: str, profile_id: str) -> Result[FiscalProfile]:
        return await self._t.request(
            "POST", f"/companies/{seg(company_id)}/fiscal-profile/{seg(profile_id)}/approve"
        )


class ServiceTaxProfiles:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(
        self, company_id: str, *, date: Optional[str] = None
    ) -> Result[List[ServiceTaxProfile]]:
        """Profiles effective on ``date`` (``YYYY-MM-DD``; today by default)."""
        return await self._t.request(
            "GET", f"/companies/{seg(company_id)}/service-tax-profiles", query={"date": date}
        )

    async def create(
        self, company_id: str, params: ServiceTaxProfileCreateParams
    ) -> Result[ServiceTaxProfile]:
        return await self._t.request(
            "POST", f"/companies/{seg(company_id)}/service-tax-profiles", json=params
        )

    async def update(
        self, company_id: str, service_id: str, params: ServiceTaxProfileUpdateParams
    ) -> Result[ServiceTaxProfile]:
        return await self._t.request(
            "PATCH",
            f"/companies/{seg(company_id)}/service-tax-profiles/{seg(service_id)}",
            json=params,
        )

    async def remove(self, company_id: str, service_id: str) -> Result[Dict[str, Any]]:
        """Delete an expired profile that was not approved yet."""
        return await self._t.request(
            "DELETE", f"/companies/{seg(company_id)}/service-tax-profiles/{seg(service_id)}"
        )

    async def approve(self, company_id: str, service_id: str) -> Result[ServiceTaxProfile]:
        return await self._t.request(
            "POST",
            f"/companies/{seg(company_id)}/service-tax-profiles/{seg(service_id)}/approve",
        )
