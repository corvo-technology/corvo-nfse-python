"""Invoice wire types."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

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

#: Why an invoice is being cancelled: sent to ``invoices.cancel()`` and echoed as ``cancellationReason``.
InvoiceCancellationReason = Literal["issue_error", "service_not_provided", "other"]

InvoiceStage = Literal["pending", "authorized", "documents_ready", "completed", "failed"]


class InvoiceCustomerAddress(TypedDict, total=False):
    street: str
    city: str
    state: str
    zip: str
    country: str


class _InvoiceCustomerRequired(TypedDict):
    taxId: str


class InvoiceCustomerInput(_InvoiceCustomerRequired, total=False):
    """Required whenever a customer is sent: ``taxId`` (CPF or CNPJ). Omit the customer for none."""

    name: str
    email: str
    address: InvoiceCustomerAddress


class InvoiceServiceInput(TypedDict, total=False):
    """All optional: ``code`` defaults to the company's, then to ``100901``; the city to the company's."""

    code: str
    municipalityCode: str
    description: str


class InvoiceEmailOptions(TypedDict, total=False):
    send: bool


class InvoiceOptions(TypedDict, total=False):
    email: InvoiceEmailOptions
    type: Literal["IMMEDIATE", "SCHEDULE"]


class _InvoiceCreateRequired(TypedDict):
    service: InvoiceServiceInput
    amount: float
    competenceDate: str


class InvoiceCreateParams(_InvoiceCreateRequired, total=False):
    """Identify the company by ``companyId`` or ``companyTaxId``; ``customer`` is optional."""

    companyId: str
    companyTaxId: str
    externalId: str
    customer: InvoiceCustomerInput
    discount: float
    email: bool
    options: InvoiceOptions


class InvoiceCustomerSnapshot(TypedDict, total=False):
    name: str
    email: str
    taxId: str
    address: InvoiceCustomerAddress


class InvoiceServiceSnapshot(TypedDict, total=False):
    code: str
    description: str
    municipalityCode: str


class Invoice(TypedDict):
    id: str
    companyId: str
    tenantId: str
    environment: Literal["test", "live"]
    documentKeyVersion: int
    emailSnapshot: Dict[str, Any]
    externalId: Optional[str]
    idempotencyKey: Optional[str]
    status: InvoiceStatus
    customerSnapshot: InvoiceCustomerSnapshot
    serviceSnapshot: InvoiceServiceSnapshot
    taxSnapshot: Dict[str, Any]
    amount: float
    currency: str
    competenceDate: str
    dpsId: Optional[str]
    dpsSeries: Optional[str]
    dpsNumber: Optional[int]
    accessKey: Optional[str]
    nfseNumber: Optional[int]
    fiscalProvider: Optional[str]
    fiscalSchemaVersion: Optional[str]
    issuedAt: Optional[str]
    authorizedAt: Optional[str]
    lastErrorCode: Optional[str]
    lastErrorMessage: Optional[str]
    lastErrorProvider: Optional[str]
    documentsReadyAt: Optional[str]
    lastEmailStatus: Optional[str]
    lastEmailSentAt: Optional[str]
    createdAt: str
    updatedAt: str
    documentsStatus: Literal["pending", "ready"]
    emailStatus: Optional[Literal["queued", "sent", "failed"]]
    stage: InvoiceStage
    scheduledFor: Optional[str]
    cancellationReason: Optional[InvoiceCancellationReason]
    cancellationDescription: Optional[str]
    cancelledAt: Optional[str]
    cancellationRequestedAt: Optional[str]


class _InvoiceCancelRequired(TypedDict):
    reason: InvoiceCancellationReason


class InvoiceCancelParams(_InvoiceCancelRequired, total=False):
    """Body of ``POST /invoices/{id}/cancel``. ``description``: at most 255 characters."""

    description: str


class InvoiceEvent(TypedDict):
    id: str
    invoiceId: str
    fromStatus: Optional[InvoiceStatus]
    toStatus: InvoiceStatus
    reason: Optional[str]
    createdAt: str


class InvoiceListParams(TypedDict, total=False):
    companyId: str
    status: InvoiceStatus
    from_: str
    to: str
    externalId: str
    limit: int
    cursor: str


class InvoiceDownloadUrl(TypedDict):
    downloadUrl: str
    expiresAt: str
    fileName: str
    mimeType: str


class InvoiceEmailResult(TypedDict):
    emailId: str
    status: str


class CalculatedTaxAmount(TypedDict, total=False):
    base: str
    rate: str  # absent on ibsTotal, which sums the state and municipal IBS
    amount: str


class CalculatedTaxes(TypedDict, total=False):
    iss: CalculatedTaxAmount
    cbs: CalculatedTaxAmount
    ibsState: CalculatedTaxAmount
    ibsCity: CalculatedTaxAmount
    ibsTotal: CalculatedTaxAmount


class InvoiceCalculation(TypedDict):
    """Pre-emission estimate. ``status`` is ``ready`` or ``blocked``: a fiscal gap is data, not an error."""

    preEmission: Literal[True]
    status: Literal["ready", "blocked"]
    disclaimer: str
    competenceDate: str
    taxRegime: Optional[str]
    classification: Dict[str, Any]
    applicability: Dict[str, Any]
    taxes: CalculatedTaxes
    withholdings: List[Dict[str, Any]]
    netReceivableAmount: Optional[str]
    collectionWaived: Optional[bool]
    calculation: Dict[str, Any]
    warnings: List[Dict[str, Any]]
    pendingFields: List[Dict[str, str]]
    blocking: Optional[Dict[str, str]]
    trace: List[Dict[str, Any]]
