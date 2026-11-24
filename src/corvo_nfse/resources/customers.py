"""Customers (saved tomadores) and the CNPJ registry lookup."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional

from ..error import Result
from ..transport import Transport, seg
from ..types.customer import CnpjProfile, CustomerUpdateParams, SavedCustomer


class Customers:
    """``customers_search``, ``customers_get``, ``customers_update``, ``customers_delete``."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def search(
        self,
        *,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        """List saved customers, most recently used first.

        ``search`` is part of the name or the first digits of the CPF/CNPJ. The cursor is the
        offset of the next page: pass it back untouched.
        """
        return await self._t.list_page(
            "/customers", {"search": search, "limit": limit, "cursor": cursor}
        )

    def iterate(
        self,
        *,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[SavedCustomer]:
        """Yield every saved customer across pages (raises on a page failure)."""
        return self._t.iterate("/customers", {"search": search, "limit": limit, "cursor": cursor})

    async def get(self, tax_id: str) -> Result[SavedCustomer]:
        """A saved customer by CPF or CNPJ (digits)."""
        return await self._t.request("GET", f"/customers/{seg(tax_id)}")

    async def update(self, tax_id: str, params: CustomerUpdateParams) -> Result[SavedCustomer]:
        """Correct the name or the e-mail of a saved customer."""
        return await self._t.request("PATCH", f"/customers/{seg(tax_id)}", json=params)

    async def remove(self, tax_id: str) -> Result[Dict[str, bool]]:
        """Forget a saved customer. Issued invoices are not changed."""
        return await self._t.request("DELETE", f"/customers/{seg(tax_id)}")


class Cnpj:
    """``cnpj_lookup``."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def lookup(self, cnpj: str) -> Result[CnpjProfile]:
        """Registration data of a CNPJ (digits). Errors: ``CNPJ_INVALID``, ``CNPJ_LOOKUP_UNAVAILABLE``."""
        return await self._t.request("GET", f"/cnpj/{seg(cnpj)}")
