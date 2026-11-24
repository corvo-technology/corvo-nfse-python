"""Payment-platform integrations: providers, connections and their operations.

A connection and its operations belong to the key's environment (``test`` or ``live``).
"""

from __future__ import annotations

from typing import List, Optional

from ..error import Result
from ..transport import Transport, seg
from ..types.customer import (
    IntegrationCompleteCustomerParams,
    IntegrationConnection,
    IntegrationConnectionCreated,
    IntegrationConnectionCreateParams,
    IntegrationCredentialsUpdateParams,
    IntegrationEvent,
    IntegrationOperation,
    IntegrationOperationRetry,
    IntegrationProvider,
    IntegrationRule,
    IntegrationRulesParams,
)


class Integrations:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list_providers(self) -> Result[List[IntegrationProvider]]:
        """The payment platforms Corvo can connect to."""
        return await self._t.request("GET", "/integrations/providers")


class IntegrationConnections:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def create(
        self, params: IntegrationConnectionCreateParams
    ) -> Result[IntegrationConnectionCreated]:
        """Create a connection. ``secrets`` is shown only in this response."""
        return await self._t.request("POST", "/integrations/connections", json=params)

    async def list(self) -> Result[List[IntegrationConnection]]:
        return await self._t.request("GET", "/integrations/connections")

    async def get(self, connection_id: str) -> Result[IntegrationConnection]:
        return await self._t.request("GET", f"/integrations/connections/{seg(connection_id)}")

    async def validate(self, connection_id: str) -> Result[IntegrationConnection]:
        """Check the credentials and identify the external account."""
        return await self._t.request(
            "POST", f"/integrations/connections/{seg(connection_id)}/validate"
        )

    async def update_credentials(
        self, connection_id: str, params: IntegrationCredentialsUpdateParams
    ) -> Result[IntegrationConnection]:
        """Replace credentials (for example a rotated API key)."""
        return await self._t.request(
            "PUT", f"/integrations/connections/{seg(connection_id)}/credentials", json=params
        )

    async def activate(self, connection_id: str) -> Result[IntegrationConnection]:
        """Start issuing invoices automatically."""
        return await self._t.request(
            "POST", f"/integrations/connections/{seg(connection_id)}/activate"
        )

    async def pause(self, connection_id: str) -> Result[IntegrationConnection]:
        """Stop issuing; events are still recorded."""
        return await self._t.request(
            "POST", f"/integrations/connections/{seg(connection_id)}/pause"
        )

    async def disconnect(self, connection_id: str) -> Result[IntegrationConnection]:
        """Disconnect for good."""
        return await self._t.request(
            "POST", f"/integrations/connections/{seg(connection_id)}/disconnect"
        )

    async def list_rules(self, connection_id: str) -> Result[List[IntegrationRule]]:
        return await self._t.request("GET", f"/integrations/connections/{seg(connection_id)}/rules")

    async def replace_rules(
        self, connection_id: str, params: IntegrationRulesParams
    ) -> Result[List[IntegrationRule]]:
        return await self._t.request(
            "PUT", f"/integrations/connections/{seg(connection_id)}/rules", json=params
        )

    async def list_events(
        self, connection_id: str, *, limit: Optional[int] = None
    ) -> Result[List[IntegrationEvent]]:
        """Recent events received for a connection."""
        return await self._t.request(
            "GET",
            f"/integrations/connections/{seg(connection_id)}/events",
            query={"limit": limit},
        )

    async def list_operations(
        self, connection_id: str, *, limit: Optional[int] = None
    ) -> Result[List[IntegrationOperation]]:
        """Recent operations (sales) and their invoice status."""
        return await self._t.request(
            "GET",
            f"/integrations/connections/{seg(connection_id)}/operations",
            query={"limit": limit},
        )


class IntegrationOperations:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def complete_customer(
        self, operation_id: str, params: IntegrationCompleteCustomerParams
    ) -> Result[IntegrationOperation]:
        """Fill in the customer of an operation that was waiting for it."""
        return await self._t.request(
            "PATCH", f"/integrations/operations/{seg(operation_id)}/customer", json=params
        )

    async def retry(self, operation_id: str) -> Result[IntegrationOperationRetry]:
        """Try to issue the invoice of an operation again."""
        return await self._t.request("POST", f"/integrations/operations/{seg(operation_id)}/retry")
