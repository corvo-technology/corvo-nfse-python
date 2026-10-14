"""Certificates resource — upload (multipart), list, remove."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..error import Result
from ..transport import Transport
from ..types.certificate import Certificate


class Certificates:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def upload(
        self,
        company_id: str,
        file: bytes,
        password: str,
        file_name: str = "certificate.p12",
    ) -> Result[Certificate]:
        """Upload a PKCS#12 certificate (max 50 KiB). The SDK builds the form."""
        files = {"file": (file_name, file, "application/x-pkcs12")}
        data = {"password": password}
        return await self._t.request_form(
            "POST", f"/companies/{company_id}/certificates", files=files, data=data
        )

    async def list(
        self,
        company_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        query: Dict[str, Any] = {"limit": limit, "cursor": cursor}
        return await self._t.list_page(f"/companies/{company_id}/certificates", query)

    async def remove(self, company_id: str, certificate_id: str) -> Result[None]:
        return await self._t.request(
            "DELETE", f"/companies/{company_id}/certificates/{certificate_id}"
        )
