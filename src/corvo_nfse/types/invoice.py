"""Invoice wire types (36 verified fields on Invoice)."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, TypedDict

InvoiceStatus = Literal[
    "queued",
    "processing",
    "authorized",
    "rejected",
    "retry_pending",
    "reconciliation_required",
    "manual_review",
    "failed",
]

InvoiceStage = Literal["pending", "authorized", "documents_ready", "completed", "failed"]


class InvoiceCustomerAddress(TypedDict, total=False):
    street: str
    city: str
    state: str
    zip: str
    country: str


class _InvoiceCustomerRequired(TypedDict):
    name: str
    taxId: str


class InvoiceCustomerInput(_InvoiceCustomerRequired, total=False):
    email: str
    address: InvoiceCustomerAddress


class _InvoiceServiceRequired(TypedDict):
    code: str


class InvoiceServiceInput(_InvoiceServiceRequired, total=False):
    municipalityCode: str
    description: str


class InvoiceEmailOptions(TypedDict, total=False):
    email: Dict[str, bool]


class _InvoiceCreateRequired(TypedDict):
    customer: InvoiceCustomerInput
    service: InvoiceServiceInput
    amount: float
    competenceDate: str


class InvoiceCreateParams(_InvoiceCreateRequired, total=False):
    companyId: str
    companyTaxId: str
    externalId: str
    correlationId: str
    email: str
    options: InvoiceEmailOptions


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
    documentsStatus: str
    emailStatus: Optional[str]
    stage: InvoiceStage


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
