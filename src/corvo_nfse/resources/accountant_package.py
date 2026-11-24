"""Monthly package (XML, PDF and summary) sent to the company's accountant."""

from __future__ import annotations

from typing import List

from ..error import Result
from ..transport import Transport, seg
from ..types.company import (
    AccountantSend,
    AccountantSendResult,
    AccountantSettings,
    AccountantSettingsUpdate,
    AccountantSettingsUpdateParams,
)


class AccountantPackage:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def get(self, company_id: str) -> Result[AccountantSettings]:
        """The accountant e-mail and the last month sent."""
        return await self._t.request("GET", f"/companies/{seg(company_id)}/accountant-package")

    async def update(
        self, company_id: str, params: AccountantSettingsUpdateParams
    ) -> Result[AccountantSettingsUpdate]:
        """Set the accountant e-mail (``{"accountantEmail": None}`` turns the monthly send off)."""
        return await self._t.request(
            "PUT", f"/companies/{seg(company_id)}/accountant-package", json=params
        )

    async def send(self, company_id: str, month: str) -> Result[AccountantSendResult]:
        """Send the package of ``month`` (``YYYY-MM``) to the accountant now.

        ``status == "sent"`` means queued for e-mail; every ``skipped-*`` means nothing was sent.
        """
        return await self._t.request(
            "POST", f"/companies/{seg(company_id)}/accountant-package/send", json={"month": month}
        )

    async def list_sends(self, company_id: str) -> Result[List[AccountantSend]]:
        """The last 12 attempts to send the package."""
        return await self._t.request(
            "GET", f"/companies/{seg(company_id)}/accountant-package/sends"
        )
