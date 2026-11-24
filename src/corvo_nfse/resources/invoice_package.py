"""Monthly invoice package of a company: summary and ZIP download."""

from __future__ import annotations

from typing import Literal, Optional

from ..error import Result
from ..transport import DownloadedFile, Transport, seg
from ..types.invoice import InvoicePackageSummary


class InvoicePackage:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def summary(self, company_id: str, month: str) -> Result[InvoicePackageSummary]:
        """Count and total of the package of ``month`` (``YYYY-MM``), without building it."""
        return await self._t.request(
            "GET",
            f"/companies/{seg(company_id)}/invoice-package/summary",
            query={"month": month},
        )

    async def download(
        self,
        company_id: str,
        month: str,
        *,
        include: Optional[Literal["xml", "pdf", "xml,pdf", "pdf,xml"]] = None,
    ) -> Result[DownloadedFile]:
        """The ZIP (``xml/``, ``pdf/`` and ``resumo.csv``) as bytes. ``include`` picks the parts."""
        return await self._t.request_raw(
            "GET",
            f"/companies/{seg(company_id)}/invoice-package",
            query={"month": month, "include": include},
        )
