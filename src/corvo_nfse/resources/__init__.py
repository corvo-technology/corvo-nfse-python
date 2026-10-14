"""Resource namespaces mounted on the Corvo client."""

from __future__ import annotations

from .billing import Billing
from .certificates import Certificates
from .companies import Companies
from .credits import Credits
from .health import Health
from .invoices import Invoices
from .webhooks import Deliveries, Webhooks

__all__ = [
    "Billing",
    "Certificates",
    "Companies",
    "Credits",
    "Deliveries",
    "Health",
    "Invoices",
    "Webhooks",
]
