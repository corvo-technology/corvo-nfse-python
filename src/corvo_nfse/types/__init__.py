"""Wire-format types mirroring the verified Corvo NFS-e API contract."""

from __future__ import annotations

from .billing import (
    BillingPlanResponse,
    BillingPlanSection,
    BillingSubscriptionSection,
    BillingUsageSection,
    QuotaStatus,
)
from .certificate import Certificate
from .common import Paginated, Pagination
from .company import (
    Company,
    CompanyAddressInput,
    CompanyCreateParams,
    CompanyListParams,
    CompanyUpdateParams,
    TaxRegime,
)
from .credits import (
    CreditBalance,
    CreditHistoryParams,
    CreditPlan,
    CreditTransaction,
    PlanQuote,
    PlanRecommendation,
)
from .invoice import (
    Invoice,
    InvoiceCalculation,
    InvoiceCreateParams,
    InvoiceCustomerInput,
    InvoiceDownloadUrl,
    InvoiceEmailResult,
    InvoiceEvent,
    InvoiceListParams,
    InvoiceStage,
    InvoiceStatus,
)
from .webhook import (
    WEBHOOK_EVENTS,
    Webhook,
    WebhookCreateParams,
    WebhookDelivery,
    WebhookDeliveryListParams,
    WebhookDeliveryStats,
    WebhookEvent,
    WebhookListParams,
    WebhookWithSecret,
)

__all__ = [
    "WEBHOOK_EVENTS",
    "BillingPlanResponse",
    "BillingPlanSection",
    "BillingSubscriptionSection",
    "BillingUsageSection",
    "Certificate",
    "Company",
    "CompanyAddressInput",
    "CompanyCreateParams",
    "CompanyListParams",
    "CompanyUpdateParams",
    "CreditBalance",
    "CreditHistoryParams",
    "CreditPlan",
    "CreditTransaction",
    "Invoice",
    "InvoiceCalculation",
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
    "PlanQuote",
    "PlanRecommendation",
    "QuotaStatus",
    "TaxRegime",
    "Webhook",
    "WebhookCreateParams",
    "WebhookDelivery",
    "WebhookDeliveryListParams",
    "WebhookDeliveryStats",
    "WebhookEvent",
    "WebhookListParams",
    "WebhookWithSecret",
]
