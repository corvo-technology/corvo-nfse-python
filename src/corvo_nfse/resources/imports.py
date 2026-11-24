"""Spreadsheet imports (CSV or Excel): upload, check, correct rows, emit.

Imports answer in snake_case: the keys are passed through as they are.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Literal, Optional

from ..error import Result
from ..transport import DownloadedFile, Transport, seg
from ..types.customer import (
    ImportEmitParams,
    ImportJob,
    ImportRow,
    ImportRowUpdateParams,
    ImportStart,
)

ImportRowStatus = Literal["valid", "invalid", "queued", "accepted", "rejected"]


class Imports:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def start(
        self,
        file: bytes,
        *,
        company_id: Optional[str] = None,
        file_name: str = "import.csv",
    ) -> Result[ImportStart]:
        """Upload a ``.csv`` or ``.xlsx`` file (up to 2,000 rows and 10 MB). Answers ``202``.

        ``company_id`` issues every row that has no CNPJ column value. ``duplicate_of`` is set when
        the same file was already imported.
        """
        files = {"file": (file_name, file, _content_type(file_name))}
        data = {"companyId": company_id} if company_id else None
        return await self._t.request_form("POST", "/imports", files=files, data=data)

    async def list(self, *, limit: Optional[int] = None) -> Result[List[ImportJob]]:
        """Recent imports with their counters (newest first, at most 20)."""
        return await self._t.request("GET", "/imports", query={"limit": limit})

    async def get(self, import_id: str) -> Result[ImportJob]:
        return await self._t.request("GET", f"/imports/{seg(import_id)}")

    async def emit(
        self, import_id: str, params: Optional[ImportEmitParams] = None
    ) -> Result[ImportJob]:
        """Emit every valid row of the import. Answers ``202``."""
        return await self._t.request(
            "POST", f"/imports/{seg(import_id)}/emit", json=params if params is not None else {}
        )

    async def list_rows(
        self,
        import_id: str,
        *,
        status: Optional[ImportRowStatus] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        """Rows of an import, one page at a time (default 50, at most 200)."""
        return await self._t.list_page(
            f"/imports/{seg(import_id)}/rows",
            {"status": status, "limit": limit, "cursor": cursor},
        )

    def iterate_rows(
        self,
        import_id: str,
        *,
        status: Optional[ImportRowStatus] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[ImportRow]:
        return self._t.iterate(
            f"/imports/{seg(import_id)}/rows",
            {"status": status, "limit": limit, "cursor": cursor},
        )

    async def update_row(
        self, import_id: str, line: int, params: ImportRowUpdateParams
    ) -> Result[ImportRow]:
        """Correct one row and check it again (only while the import is ``ready``)."""
        return await self._t.request(
            "PATCH", f"/imports/{seg(import_id)}/rows/{seg(line)}", json=params
        )

    async def discard(self, import_id: str) -> Result[None]:
        """Discard an import that has not been emitted."""
        return await self._t.request("DELETE", f"/imports/{seg(import_id)}")

    async def download_template(self) -> Result[DownloadedFile]:
        """The spreadsheet template (CSV)."""
        return await self._t.request_raw("GET", "/imports/template")

    async def download_errors(self, import_id: str) -> Result[DownloadedFile]:
        """CSV with the rows that need attention."""
        return await self._t.request_raw("GET", f"/imports/{seg(import_id)}/errors.csv")


def _content_type(file_name: str) -> str:
    if file_name.lower().endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "text/csv"
