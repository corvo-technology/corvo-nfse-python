"""Invoice wire types (aliases of the generated models, so they match the contract exactly)."""

from __future__ import annotations

from typing import Any, List, Literal, TypedDict

from . import models

InvoiceStatus = Literal[
    "queued",
    "processing",
    "authorized",
    "rejected",
    "retry_pending",
    "reconciliation_required",
    "manual_review",
    "failed",
    "cancelling",
    "cancelled",
]

INVOICE_STATUSES = (
    "queued",
    "processing",
    "authorized",
    "rejected",
    "retry_pending",
    "reconciliation_required",
    "manual_review",
    "failed",
    "cancelling",
    "cancelled",
)

InvoiceCancellationReason = Literal["issue_error", "service_not_provided", "other"]

INVOICE_CANCELLATION_REASONS = ("issue_error", "service_not_provided", "other")

InvoiceStage = Literal["pending", "authorized", "documents_ready", "completed", "failed"]

InvoiceCustomerAddress = models.CustomerAddress
InvoiceCustomerInput = models.InvoiceCustomer
InvoiceForeignCustomer = models.ForeignCustomer
InvoiceServiceInput = models.InvoiceService
InvoiceEmailOptions = models.EmailOptions
InvoiceOptions = models.InvoiceOptions
InvoiceRecurrence = models.RecurrenceOptions
InvoiceCreateParams = models.CreateInvoice
InvoiceCancelParams = models.CancelInvoice
InvoiceSubstituteParams = models.SubstituteInvoice
InvoiceReviewParams = models.ReviewInvoices
InvoiceReviewResult = models.InvoiceReviewResult
InvoiceEmailParams = models.RequestInvoiceEmail
InvoiceBatchItem = models.InvoiceBatchItem
InvoiceBatchError = models.InvoiceBatchError
InvoiceBatchResult = models.InvoiceBatchResult
InvoiceBatchSummary = models.InvoiceBatch
InvoiceCustomerSnapshot = models.CustomerSnapshot
InvoiceServiceSnapshot = models.ServiceSnapshot
Invoice = models.Invoice
InvoiceEvent = models.InvoiceEvent
InvoiceDownloadUrl = models.InvoiceDownloadUrl
InvoiceEmailResult = models.InvoiceEmailRequest
InvoiceCalculation = models.InvoiceCalculation
InvoiceOverview = models.InvoiceOverview
InvoicePackageSummary = models.PackageSummary
FiscalPortalStatus = models.PortalStatus
CalculatedTaxes = models.CalculatedTaxes


class InvoiceListParams(TypedDict, total=False):
    companyId: str
    status: InvoiceStatus
    from_: str
    to: str
    externalId: str
    customerTaxId: str
    limit: int
    cursor: str


#: ``POST /invoices`` answers with an :class:`Invoice` for ``IMMEDIATE`` and with a
#: :class:`~corvo_nfse.types.models.Schedule` (snake_case fields) for ``SCHEDULE``/``RECURRING``.
InvoiceCreateResult = Any
InvoiceList = List[models.Invoice]
