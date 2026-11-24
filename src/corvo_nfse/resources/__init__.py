"""Resource namespaces mounted on the Corvo client."""

from __future__ import annotations

from .accountant_package import AccountantPackage
from .billing import Billing
from .certificates import Certificates
from .companies import Companies
from .company_setup import DpsSequences, FiscalProfiles, ServiceTaxProfiles
from .credits import Credits
from .customers import Cnpj, Customers
from .fiscal_portal import FiscalPortal
from .health import Health
from .imports import Imports
from .integrations import IntegrationConnections, IntegrationOperations, Integrations
from .invoice_package import InvoicePackage
from .invoices import Invoices
from .plans import Plans
from .schedules import Schedules
from .service_favorites import ServiceFavorites
from .webhooks import Deliveries, Webhooks

__all__ = [
    "AccountantPackage",
    "Billing",
    "Certificates",
    "Cnpj",
    "Companies",
    "Credits",
    "Customers",
    "Deliveries",
    "DpsSequences",
    "FiscalPortal",
    "FiscalProfiles",
    "Health",
    "Imports",
    "IntegrationConnections",
    "IntegrationOperations",
    "Integrations",
    "InvoicePackage",
    "Invoices",
    "Plans",
    "Schedules",
    "ServiceFavorites",
    "ServiceTaxProfiles",
    "Webhooks",
]
