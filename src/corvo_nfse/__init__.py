"""corvo-nfse — the Python SDK for the Corvo NFS-e API."""

from __future__ import annotations

from .client import Corvo
from .error import CorvoApiError, CorvoErrorDetail, Result
from .transport import DownloadedFile, Query, Unwrap
from .types import (
    WEBHOOK_EVENTS,
    BillingPlanResponse,
    Certificate,
    Company,
    CompanyAddressInput,
    CompanyCreateParams,
    CompanyUpdateParams,
    CreditBalance,
    CreditPlan,
    CreditTransaction,
    Invoice,
    InvoiceCreateParams,
    InvoiceCustomerInput,
    InvoiceDownloadUrl,
    InvoiceEmailResult,
    InvoiceEvent,
    InvoiceListParams,
    InvoiceStage,
    InvoiceStatus,
    Paginated,
    Pagination,
    QuotaStatus,
    TaxRegime,
    Webhook,
    WebhookCreateParams,
    WebhookDelivery,
    WebhookDeliveryStats,
    WebhookEvent,
    WebhookWithSecret,
)
from .webhooks import CorvoWebhooks

VERSION = "0.1.0"
__version__ = VERSION

__all__ = [
    "VERSION",
    "__version__",
    "WEBHOOK_EVENTS",
    "BillingPlanResponse",
    "Certificate",
    "Company",
    "CompanyAddressInput",
    "CompanyCreateParams",
    "CompanyUpdateParams",
    "Corvo",
    "CorvoApiError",
    "CorvoErrorDetail",
    "CorvoWebhooks",
    "CreditBalance",
    "CreditPlan",
    "CreditTransaction",
    "DownloadedFile",
    "Invoice",
    "InvoiceCreateParams",
    "InvoiceCustomerInput",
    "InvoiceDownloadUrl",
    "InvoiceEmailResult",
    "InvoiceEvent",
    "InvoiceListParams",
    "InvoiceStage",
    "InvoiceStatus",
    "Paginated",
    "Pagination",
    "Query",
    "QuotaStatus",
    "Result",
    "TaxRegime",
    "Unwrap",
    "Webhook",
    "WebhookCreateParams",
    "WebhookDelivery",
    "WebhookDeliveryStats",
    "WebhookEvent",
    "WebhookWithSecret",
]
