"""National NFS-e portal status."""

from __future__ import annotations

from ..error import Result
from ..transport import Transport
from ..types.invoice import FiscalPortalStatus


class FiscalPortal:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def status(self) -> Result[FiscalPortalStatus]:
        """Whether the national portal is answering for this key's environment."""
        return await self._t.request("GET", "/fiscal-portal/status")
