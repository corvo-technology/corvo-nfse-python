"""Wire models for the Corvo public API, generated from ``spec/openapi.json`` (contract 0.3.0).

Do not edit by hand: run ``python scripts/gen_models.py``. Field names are the wire names
(camelCase, except billing, schedules and imports, which the API answers in snake_case).
Keys the API may leave out are optional (``total=False``); ``None`` means the API sent ``null``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

class AccountantSend(TypedDict):
    id: str
    month: str
    recipient: str
    invoiceCount: int
    totalCents: int
    status: Literal["sent", "skipped-empty", "skipped-too-large", "failed"]
    trigger: Literal["scheduled", "manual", "mcp-or-api"]
    createdAt: str


class AccountantSendResult(TypedDict):
    # `sent` means queued for e-mail (not proof of delivery). Every `skipped-*` means nothing was
    # sent.
    status: Literal["sent", "skipped-test", "skipped-no-email", "skipped-empty", "skipped-too-large", "skipped-already-sent"]


class AccountantSettings(TypedDict):
    email: Optional[str]
    lastSentMonth: Optional[str]


class AccountantSettingsUpdate(TypedDict):
    email: Optional[str]
    lastSentMonth: Optional[str]
    # True when a short hello was sent to the new address (live companies only, once per address).
    testEmailSent: bool


class _ApiErrorRequired(TypedDict):
    statusCode: int
    # Stable machine-readable code: branch on it, not on `message`. Codes start with `ERROR_` and
    # the list can grow, so treat an unknown code as its HTTP status. A few feature codes have no
    # prefix (`CNPJ_INVALID`, `CHECKOUT_INVALID`, `PACKAGE_TOO_LARGE`, ...); they are described on
    # the operation.
    code: str
    message: str


class ApiErrorDetailsVariant1Item(TypedDict, total=False):
    code: str
    field: str
    message: str


class ApiError(_ApiErrorRequired, total=False):
    # Extra data. For `ERROR_VALIDATION`: a list of `{ field, code, message }`.
    details: Union[Dict[str, Any], List[ApiErrorDetailsVariant1Item]]
    # Short HTTP label, for example `Not Found`.
    error: str
    requestId: str
    # Present (true) on 503: the request can be repeated.
    retryable: bool


class Applicability(TypedDict):
    strategy: str
    customerRequired: bool
    iss: Obligation
    issWithheld: Obligation
    federalWithholding: Obligation
    cbs: Obligation
    ibs: Obligation
    specialTreatment: Obligation
    collectionWaived: bool
    rulesVersion: str
    legalReferences: List[str]


class BillingPlanPlan(TypedDict):
    slug: Literal["free", "self-hosted", "solo", "equipe", "empresa", "escala"]
    name: str
    monthly_allowance: int
    daily_limit: Optional[int]
    max_active_companies: int
    monthly_price_cents: int


class _BillingPlanSubscriptionPix_subscriptionRequired(TypedDict):
    status: Literal["active", "pending"]
    planSlug: str
    brCode: Optional[str]
    paymentLinkUrl: Optional[str]


class BillingPlanSubscriptionPix_subscription(_BillingPlanSubscriptionPix_subscriptionRequired, total=False):
    paymentId: str


class BillingPlanSubscription(TypedDict):
    # Subscription status from the payment provider, or `none`.
    status: str
    paid_until: Optional[str]
    cancel_at_period_end: bool
    scheduled_plan: Optional[str]
    # True when the plan lapsed and cannot issue.
    blocked: bool
    stripe_portal_available: bool
    stripe_subscription: bool
    pix_subscription: Optional[BillingPlanSubscriptionPix_subscription]


class _BillingPlanUsageRequired(TypedDict):
    hard_limit: int
    avulso_balance: int
    credits_used: int
    credits_reserved: int
    credits_remaining: int
    monthly_allowance: int
    daily_usage: int
    daily_limit: Optional[int]
    active_companies: int
    max_active_companies: int


class BillingPlanUsage(_BillingPlanUsageRequired, total=False):
    period_end: str
    period_start: str


class BillingPlan(TypedDict):
    plan: BillingPlanPlan
    subscription: BillingPlanSubscription
    usage: BillingPlanUsage


class Blocking(TypedDict):
    code: str
    message: str
    step: str
    category: Literal["VALIDATION", "CONFIGURATION", "CLASSIFICATION", "UNSUPPORTED", "CALCULATION", "INTEGRATION", "INTERNAL"]
    retryable: bool
    details: Dict[str, Any]


class CalculatedTaxes(TypedDict, total=False):
    cbs: TaxAmount
    ibsCity: TaxAmount
    ibsState: TaxAmount
    ibsTotal: TaxAmount
    iss: TaxAmount


class CalculationMetadata(TypedDict):
    source: Literal["none", "legacy", "rtc", "legacy+rtc"]
    calculatorVersion: Optional[str]
    rulesVersion: Optional[str]
    legalReferences: List[str]


class _CalculationTraceRequired(TypedDict):
    step: str
    status: Literal["applied", "skipped", "failed"]
    # Duration in milliseconds
    durationMs: float


class CalculationTrace(_CalculationTraceRequired, total=False):
    reason: str


class _CancelInvoiceRequired(TypedDict):
    reason: Literal["issue_error", "service_not_provided", "other"]


class CancelInvoice(_CancelInvoiceRequired, total=False):
    # Required (15–255 characters) to cancel an authorized NFS-e or an invoice being issued
    # (processing); optional for a queued invoice.
    description: str


class Certificate(TypedDict):
    id: str
    companyId: str
    serialNumber: str
    issuer: str
    subject: str
    fingerprint: str
    validFrom: str
    validUntil: str
    # For example `active` or `expired`.
    status: str
    createdAt: str


class Classification(TypedDict):
    serviceCode: str
    municipalServiceCode: Optional[str]
    nbsCode: Optional[str]
    cst: Optional[str]
    classCode: Optional[str]
    operationIndicator: Optional[str]
    source: Literal["company_service_profile", "request_override", "official_catalog"]
    serviceProfileId: Optional[str]
    operationNature: str
    iss: Dict[str, Any]
    withholding: Dict[str, Any]
    catalogValidated: bool
    catalogVersions: Dict[str, str]
    justification: str


class CnpjProfile(TypedDict):
    """Empty text means the registry did not say."""

    legalName: str
    tradeName: str
    address: PostalAddress
    # 7-digit IBGE code of the registered address.
    municipalityCode: Optional[str]
    simples: Optional[bool]
    mei: Optional[bool]
    # False when the registry says the CNPJ is not active.
    active: bool
    situation: str


class _CompanyRequired(TypedDict):
    id: str
    tenantId: str
    legalName: str
    # CNPJ, digits only.
    taxId: str
    fiscalSchemaVersion: str
    environment: Literal["test", "live"]
    status: Literal["pending_setup", "ready", "blocked"]
    # What is still missing before the company can issue (for example `certificate`).
    setupGaps: List[str]
    taxRegime: Optional[Literal["MEI", "Simples Nacional", "Lucro Presumido", "Lucro Real"]]
    simpleNational: bool
    specialRegime: Optional[str]
    createdAt: str
    updatedAt: str


class Company(_CompanyRequired, total=False):
    addressCity: str
    addressComplement: str
    addressDistrict: str
    addressNumber: str
    addressState: str
    addressStreet: str
    addressZip: str
    defaultServiceCode: str
    municipalityAgreement: MunicipalityAgreement
    # 7-digit IBGE code.
    municipalityCode: str
    municipalReg: str
    sendMunicipalReg: bool
    # Percent, e.g. "2.00".
    simplesIssRate: str
    # Percent, e.g. "6.00".
    simplesRate: str
    tradeName: str
    # Only on creation: differences between what you sent and the public CNPJ registry. They never
    # block the request.
    warnings: List[RegistryWarning]


class CompanyAddress(TypedDict, total=False):
    city: str
    complement: str
    district: str
    number: str
    state: str
    street: str
    zip: str


class _CompleteCustomerRequired(TypedDict):
    taxId: str


class CompleteCustomer(_CompleteCustomerRequired, total=False):
    email: str
    name: str


class _CreateCompanyRequired(TypedDict):
    # Required IBGE municipality code (7 digits) in test and live.
    municipalityCode: str
    legalName: str
    taxId: str
    taxRegime: Literal["MEI", "Simples Nacional", "Lucro Presumido", "Lucro Real"]


class CreateCompany(_CreateCompanyRequired, total=False):
    address: CompanyAddress
    # Default national service classification (cTribNac, 6 digits).
    defaultServiceCode: str
    municipalReg: Optional[str]
    # Send the municipal registration in the DPS. Default false: the Receita rejects it (E0120)
    # when the city has no complementary data for the company.
    sendMunicipalReg: bool
    simpleNational: bool
    # Simples Nacional only: effective ISS rate (%) of your bracket. Only needed when a customer
    # withholds ISS. Ignored for MEI.
    simplesIssRate: str
    # Simples Nacional only: effective total rate (%) of your DAS, sent in the invoice as
    # pTotTribSN. Required for Simples Nacional; ignored for MEI.
    simplesRate: str
    # Special tax regime (regEspTrib, RTC v1.01): 0 Nenhum, 1 Ato Cooperado, 2 Estimativa, 3
    # Microempresa Municipal, 4 Notário ou Registrador, 5 Profissional Autônomo, 6 Sociedade de
    # Profissionais. Empty string clears it.
    specialRegime: Literal["0", "1", "2", "3", "4", "5", "6"]
    tradeName: str


class _CreateConnectionRequired(TypedDict):
    provider: str
    companyId: str
    credentials: Dict[str, str]


class CreateConnection(_CreateConnectionRequired, total=False):
    activeFrom: str
    environment: Literal["test", "live"]


class _CreateInvoiceRequired(TypedDict):
    # Gross amount in BRL, at most 2 decimals.
    amount: float
    # Competence date (ISO 8601). Without `options.type` it cannot be in the future (422
    # `ERROR_FUTURE_DATE`). With `options.type` SCHEDULE or RECURRING it is the date of the first
    # run, from tomorrow on.
    competenceDate: str
    service: InvoiceService


class CreateInvoice(_CreateInvoiceRequired, total=False):
    # Company id. Required unless `companyTaxId` is sent; wins if both are sent.
    companyId: str
    # Company CNPJ (punctuation optional). Required unless `companyId` is sent.
    companyTaxId: str
    # Customer (tomador). Optional — omit or send an empty object for anonymous consumer invoices;
    # the tomador is then omitted from the DPS.
    customer: InvoiceCustomer
    # Deduction from the ISS tax base declared by the issuer, in BRL (> 0 and < amount - discount,
    # max 2 decimals). Sent in the DPS as vDedRed/vDR. The issuer is responsible for the declared
    # value; Corvo does not check whether the deduction is allowed for the service or
    # municipality.
    deduction: float
    # Unconditional discount (>= 0 and <= amount, max 2 decimals). Validated, never silently
    # truncated.
    discount: float
    # Whether to e-mail the invoice to the customer once it is authorized (needs
    # `customer.email`).
    email: bool
    # Your own reference. Returned on the invoice and usable as a filter in GET /invoices.
    externalId: str
    # Free text printed on the invoice as complementary information (DPS serv/infoCompl/xInfComp).
    # Does not change any tax.
    notes: str
    options: InvoiceOptions
    # Purchase order, service order or project number the customer asked to see on the invoice.
    # Sent in the DPS as serv/infoCompl/xPed and printed on the DANFSe. Does not change any tax.
    purchaseOrder: str


class CreateInvoiceBatch(TypedDict):
    # Invoices to emit. Each item has the same fields as POST /invoices plus an optional
    # idempotencyKey; items may belong to different companies. Items are validated one by one: an
    # invalid item is rejected in the response without failing the others.
    invoices: List[InvoiceBatchItem]


class _CreateServiceFavoriteRequired(TypedDict):
    label: str
    description: str
    # cTribNac, 6 digits.
    serviceCode: str


class CreateServiceFavorite(_CreateServiceFavoriteRequired, total=False):
    # Default amount in cents.
    amountCents: Optional[float]
    # Place of service (7 digits).
    municipalityCode: Optional[str]


class _CreateServiceTaxProfileRequired(TypedDict):
    # National service classification (cTribNac, 6 digits).
    serviceCode: str
    effectiveFrom: str
    name: str


class CreateServiceTaxProfile(_CreateServiceTaxProfileRequired, total=False):
    catalogVersion: Optional[str]
    classCode: Optional[str]
    classificationSource: str
    cst: Optional[str]
    effectiveUntil: Optional[str]
    incidenceMunicipalityCode: Optional[str]
    issRate: Optional[str]
    issTaxation: Optional[Literal["NORMAL", "FIXED", "EXEMPT"]]
    issWithholdingDefault: bool
    municipalServiceCode: Optional[str]
    nbsCode: Optional[str]
    operationIndicator: Optional[str]
    operationNature: Literal["SERVICE", "GOODS", "MIXED", "PARTNER_SALON"]
    regimeApplicability: List[Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]]
    withholdingPolicy: Literal["UNKNOWN", "NONE_CONFIRMED", "CONFIGURED"]
    withholdingRates: Dict[str, str]


class CreateWebhookConfig(TypedDict):
    # HTTPS (or HTTP) address that receives the events.
    url: str
    # Events this endpoint receives.
    events: List[Literal["nfse.invoice.authorized", "nfse.invoice.rejected", "nfse.invoice.failed", "nfse.invoice.reconciliation_required", "nfse.invoice.manual_review", "nfse.invoice.documents_ready", "nfse.invoice.email_sent", "nfse.invoice.email_failed", "nfse.invoice.fiscal_discrepancy", "nfse.invoice.cancelled", "nfse.invoice.cancellation_rejected", "nfse.invoice.taker_rejected"]]


class CreditBalance(TypedDict):
    # Notes available: plan notes left plus loose notes.
    balance: int
    planRemaining: int
    # Loose (one-off) notes bought separately.
    avulsoBalance: int
    hardLimit: int


class _CreditTransactionRequired(TypedDict):
    id: str
    tenantId: str
    amount: int
    type: Literal["purchase", "subscription_charge", "topup", "overage", "invoice_authorized", "invoice_rejected", "expiration", "message_sent", "refund", "adjustment", "bonus"]
    createdAt: str


class CreditTransaction(_CreditTransactionRequired, total=False):
    amountBrlCents: int
    description: str
    isReservation: bool
    metadata: Dict[str, Any]
    periodId: str
    planIdSnapshot: str
    relatedTransactionId: str
    reservedInvoiceId: str
    source: Literal["subscription", "avulso", "bonus"]
    unitPriceCentsApplied: int


class CursorPagination(TypedDict):
    limit: float
    hasMore: bool
    nextCursor: Optional[str]


class CustomerAddress(TypedDict, total=False):
    city: str
    country: str
    # Incidence municipality (7 digits, IBGE code), when known.
    municipalityCode: str
    state: str
    street: str
    zip: str


class _CustomerSnapshotRequired(TypedDict):
    name: str


class _CustomerSnapshotAddressRequired(TypedDict):
    city: str
    state: str


class CustomerSnapshotAddress(_CustomerSnapshotAddressRequired, total=False):
    country: str


class CustomerSnapshot(_CustomerSnapshotRequired, total=False):
    address: CustomerSnapshotAddress
    email: str
    # Customer outside Brazil: taxId (NIF) or noTaxIdReason, and the address abroad.
    foreign: Dict[str, str]
    # Absent for anonymous consumer invoices.
    taxId: str


class Deleted(TypedDict):
    deleted: Literal[True]


class DpsSequence(TypedDict):
    series: str
    # The last DPS number used (0 when none yet).
    lastNumber: int


class EmailOptions(TypedDict, total=False):
    send: bool


class EmitImport(TypedDict, total=False):
    # Email each issued invoice to the customer. Only rows that have a customer email are sent.
    sendEmail: bool


class _FiscalProfileRequired(TypedDict):
    id: str
    tenantId: str
    companyId: str
    taxRegime: Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]
    simpleNational: bool
    specialTaxRegime: Optional[Literal["0", "1", "2", "3", "4", "5", "6"]]
    ibsCbsRegularOption: bool
    ibsCbsRegularFrom: Optional[str]
    simplesIssRate: Optional[str]
    # Inclusive.
    validFrom: str
    # Exclusive. Null while the profile is open.
    validUntil: Optional[str]
    source: str
    reviewStatus: Literal["unreviewed", "approved", "rejected"]
    reviewedBy: Optional[str]
    reviewedAt: Optional[str]
    createdAt: str


class FiscalProfile(_FiscalProfileRequired, total=False):
    simplesApuracao: Optional[Literal["SN", "ISS_MUNICIPAL", "REGULAR"]]


class FiscalWarning(TypedDict):
    code: str
    message: str
    step: str


class _ForeignCustomerRequired(TypedDict):
    # ISO 3166-1 alpha-2 country code, other than BR.
    country: str
    postalCode: str
    city: str
    # State, province or region.
    region: str
    street: str
    # Street number. Required by the DPS.
    number: str
    # District or neighbourhood. Required by the DPS.
    district: str


class ForeignCustomer(_ForeignCustomerRequired, total=False):
    complement: str
    # Why the customer has no tax id (DPS cNaoNIF 1 or 2).
    noTaxIdReason: Literal["exempt", "not_required"]
    # Tax id in the customer's country (DPS NIF). Send this or noTaxIdReason, never both.
    taxId: str


class GetDownloadUrl(TypedDict):
    format: Literal["pdf", "xml"]


class Health(TypedDict):
    status: Literal["ok"]
    timestamp: str
    # Seconds since the process started.
    uptime: float


class ImportCounters(TypedDict):
    total: int
    valid: int
    invalid: int
    accepted: int
    authorized: int
    # Turned away because credits or the plan limit ran out: not an error, emit again.
    awaiting_credits: int
    # BRL, rows ready to emit.
    valid_amount: float
    awaiting_amount: float
    failed: int
    pending: int
    authorized_amount: float
    pending_amount: float
    failed_amount: float


class ImportJob(TypedDict):
    id: str
    status: Literal["processing", "ready", "emitting", "done", "failed"]
    file_name: str
    company_id: Optional[str]
    error_code: Optional[str]
    rows_expected: Optional[int]
    # Header names of the file that matched no column (ignored).
    unknown_columns: List[str]
    emit_started_at: Optional[str]
    emit_finished_at: Optional[str]
    created_at: str
    counters: ImportCounters


class ImportRow(TypedDict):
    # Line of the file, starting at 1.
    line: int
    data: Dict[str, Any]
    status: Literal["valid", "invalid", "queued", "accepted", "rejected"]
    error_code: Optional[str]
    error_message: Optional[str]
    invoice_id: Optional[str]


class ImportStart(TypedDict):
    id: str
    status: Literal["processing", "ready", "emitting", "done", "failed"]
    # Set when the same file was already imported: that import.
    duplicate_of: Optional[str]


class IntegrationConnection(TypedDict):
    id: str
    provider: str
    environment: Literal["test", "live"]
    companyId: str
    state: Literal["draft", "active", "paused", "reauth_required", "disconnected"]
    externalAccountId: Optional[str]
    activeFrom: Optional[str]
    # Paste it into the payment platform.
    webhookUrl: str
    createdAt: str


class IntegrationConnectionCreated(IntegrationConnection):
    # Credentials the platform needs, shown only in this response.
    secrets: Dict[str, str]


class IntegrationEvent(TypedDict):
    id: str
    deliveryId: str
    externalType: str
    state: Literal["received", "processing", "retry_pending", "processed", "ignored", "needs_attention", "dead"]
    attempts: int
    lastError: Optional[str]
    operationId: Optional[str]
    createdAt: str


class IntegrationOperationCustomer(TypedDict):
    name: Optional[str]
    email: Optional[str]
    taxId: Optional[str]
    taxIdMasked: bool


class IntegrationOperation(TypedDict):
    id: str
    operationKey: str
    commercialState: Literal["pending", "paid", "refunded", "disputed", "canceled"]
    fiscalStatus: Literal["none", "blocked", "needs_attention", "submitted"]
    # Why no invoice was issued, for example `no_rule`, `customer_tax_id_missing`,
    # `quota_exceeded`.
    blockReason: Optional[str]
    amountCents: int
    currency: str
    customer: Optional[IntegrationOperationCustomer]
    paidAt: Optional[str]
    invoiceId: Optional[str]
    createdAt: str
    updatedAt: str


class _IntegrationOperationRetryRequired(TypedDict):
    state: Literal["processed", "ignored", "needs_attention"]


class IntegrationOperationRetry(_IntegrationOperationRetryRequired, total=False):
    lastError: str
    operationId: str


class _IntegrationProviderCredentialFieldsItemRequired(TypedDict):
    key: str
    label: str
    secret: bool


class IntegrationProviderCredentialFieldsItem(_IntegrationProviderCredentialFieldsItemRequired, total=False):
    generate: bool
    inWebhookUrl: bool
    revealOnce: bool


class IntegrationProviderWebhookInstructions(TypedDict):
    pt: str
    en: str


class IntegrationProvider(TypedDict):
    id: str
    name: str
    version: str
    credentialFields: List[IntegrationProviderCredentialFieldsItem]
    webhookInstructions: IntegrationProviderWebhookInstructions
    supportedFlows: List[str]


class IntegrationRule(TypedDict):
    id: str
    # Null for the default rule (any product).
    externalProductId: Optional[str]
    service: Dict[str, Any]
    sendEmail: bool
    allowAnonymousCustomer: bool
    cancelOnRefund: bool


class _IntegrationRuleInputRequired(TypedDict):
    service: InvoiceService
    sendEmail: bool


class IntegrationRuleInput(_IntegrationRuleInputRequired, total=False):
    allowAnonymousCustomer: bool
    cancelOnRefund: bool
    externalProductId: Optional[str]


class _InvoiceRequired(TypedDict):
    id: str
    companyId: str
    tenantId: str
    # Environment the invoice was issued in.
    environment: Literal["test", "live"]
    # Your own reference, sent as `externalId` on creation.
    externalId: Optional[str]
    # The `Idempotency-Key` the invoice was created with.
    idempotencyKey: Optional[str]
    # Fiscal status. `queued` and `processing` are in flight; `retry_pending`,
    # `reconciliation_required` and `manual_review` are unresolved emissions (see POST
    # /invoices/review); `authorized`, `rejected`, `failed` and `cancelled` are final;
    # `cancelling` is an authorized invoice whose cancellation event is being processed.
    status: Literal["queued", "processing", "authorized", "rejected", "retry_pending", "reconciliation_required", "manual_review", "failed", "cancelling", "cancelled"]
    # Whether the PDF and XML can be downloaded.
    documentsStatus: Literal["pending", "ready"]
    # Null when no e-mail was requested yet.
    emailStatus: Optional[Literal["queued", "sent", "failed"]]
    # Single lifecycle view derived from the other fields: `completed` means authorized, documents
    # ready and the requested e-mail resolved.
    stage: Literal["pending", "authorized", "documents_ready", "completed", "failed", "cancelled"]
    # Null for anonymous consumer invoices (tomador omitted from the DPS).
    customerSnapshot: Optional[CustomerSnapshot]
    serviceSnapshot: ServiceSnapshot
    # Calculated taxes. Its keys depend on the tax regime and may grow; use POST
    # /invoices/calculate to preview them.
    taxSnapshot: Dict[str, Any]
    # Gross amount in BRL (2 decimals).
    amount: float
    currency: str
    competenceDate: str
    dpsId: Optional[str]
    dpsSeries: Optional[str]
    dpsNumber: Optional[float]
    # NFS-e access key (50 digits), once authorized.
    accessKey: Optional[str]
    nfseNumber: Optional[float]
    fiscalProvider: str
    fiscalSchemaVersion: str
    issuedAt: Optional[str]
    authorizedAt: Optional[str]
    # Rejection or failure code of the last attempt: an `E`-prefixed Sefin rule (E0014) or one of
    # Corvo (DPS_NUMBER_ALREADY_USED, DPS_NUMBER_BELOW_CURRENT, ...).
    lastErrorCode: Optional[str]
    lastErrorMessage: Optional[str]
    lastErrorProvider: Optional[str]
    documentsReadyAt: Optional[str]
    lastEmailStatus: Optional[Literal["queued", "sent", "failed"]]
    lastEmailSentAt: Optional[str]
    createdAt: str
    updatedAt: str


class InvoiceEmailSnapshot(TypedDict, total=False):
    """Whether the e-mail to the customer was requested."""

    send: bool


class Invoice(_InvoiceRequired, total=False):
    # Justification given when the cancellation was requested
    cancellationDescription: Optional[str]
    # Reason given when the cancellation was requested
    cancellationReason: Optional[Literal["issue_error", "service_not_provided", "other"]]
    # Set when the cancellation was requested while the invoice was being issued (processing); it
    # is cancelled at the Sefin as soon as it is authorized
    cancellationRequestedAt: Optional[str]
    # When the invoice reached cancelled
    cancelledAt: Optional[str]
    # Deduction from the ISS tax base declared by the issuer.
    deduction: float
    # Unconditional discount applied to the amount.
    discount: float
    # Whether the e-mail to the customer was requested.
    emailSnapshot: InvoiceEmailSnapshot
    # What the national portal reported after authorization (customer rejected the invoice, or the
    # portal blocked it).
    portalFlag: Optional[Literal["taker_rejected", "blocked"]]
    scheduledFor: Optional[str]
    # On a substitute: the invoice it replaces.
    substitutesInvoiceId: Optional[str]
    substitutionDescription: Optional[str]


class InvoiceBatch(TypedDict):
    total: float
    accepted: float
    rejected: float
    # One entry per request item, in the order they were sent.
    results: List[InvoiceBatchResult]


class _InvoiceBatchErrorRequired(TypedDict):
    code: str
    message: str


class InvoiceBatchError(_InvoiceBatchErrorRequired, total=False):
    # Field-level details, when the error has them.
    details: Dict[str, Any]


class _InvoiceBatchItemRequired(TypedDict):
    # Gross amount in BRL, at most 2 decimals.
    amount: float
    # Competence date (ISO 8601). Without `options.type` it cannot be in the future (422
    # `ERROR_FUTURE_DATE`). With `options.type` SCHEDULE or RECURRING it is the date of the first
    # run, from tomorrow on.
    competenceDate: str
    service: InvoiceService


class InvoiceBatchItem(_InvoiceBatchItemRequired, total=False):
    # Company id. Required unless `companyTaxId` is sent; wins if both are sent.
    companyId: str
    # Company CNPJ (punctuation optional). Required unless `companyId` is sent.
    companyTaxId: str
    # Customer (tomador). Optional — omit or send an empty object for anonymous consumer invoices;
    # the tomador is then omitted from the DPS.
    customer: InvoiceCustomer
    # Deduction from the ISS tax base declared by the issuer, in BRL (> 0 and < amount - discount,
    # max 2 decimals). Sent in the DPS as vDedRed/vDR. The issuer is responsible for the declared
    # value; Corvo does not check whether the deduction is allowed for the service or
    # municipality.
    deduction: float
    # Unconditional discount (>= 0 and <= amount, max 2 decimals). Validated, never silently
    # truncated.
    discount: float
    # Whether to e-mail the invoice to the customer once it is authorized (needs
    # `customer.email`).
    email: bool
    # Your own reference. Returned on the invoice and usable as a filter in GET /invoices.
    externalId: str
    # Per-item idempotency key. Repeating the batch with the same keys never issues twice: the
    # saved invoice comes back with replayed true.
    idempotencyKey: str
    # Free text printed on the invoice as complementary information (DPS serv/infoCompl/xInfComp).
    # Does not change any tax.
    notes: str
    options: InvoiceOptions
    # Purchase order, service order or project number the customer asked to see on the invoice.
    # Sent in the DPS as serv/infoCompl/xPed and printed on the DANFSe. Does not change any tax.
    purchaseOrder: str


class _InvoiceBatchResultRequired(TypedDict):
    # Position of the item in the request, starting at 0.
    index: float
    status: Literal["accepted", "rejected"]


class InvoiceBatchResult(_InvoiceBatchResultRequired, total=False):
    # Present when status is rejected. Rejected items are not saved.
    error: InvoiceBatchError
    # Present when status is accepted.
    invoice: Invoice
    # True when the item repeated an idempotencyKey already saved with the same payload: the
    # existing invoice is returned and nothing new is written.
    replayed: bool


class InvoiceCalculation(TypedDict):
    preEmission: Literal[True]
    status: Literal["ready", "blocked"]
    disclaimer: str
    competenceDate: str
    taxRegime: Optional[Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]]
    classification: Optional[Classification]
    applicability: Optional[Applicability]
    taxes: CalculatedTaxes
    withholdings: List[WithholdingAmount]
    netReceivableAmount: Optional[str]
    collectionWaived: Optional[bool]
    calculation: Optional[CalculationMetadata]
    warnings: List[FiscalWarning]
    pendingFields: List[PendingField]
    blocking: Optional[Blocking]
    trace: List[CalculationTrace]


class InvoiceCustomer(TypedDict, total=False):
    address: CustomerAddress
    # Where the invoice is e-mailed when `email` is true.
    email: str
    # Customer outside Brazil. Cannot be sent with taxId (CPF/CNPJ) or address; name is then
    # required. It does not declare a service export: the invoice keeps its tax treatment.
    foreign: ForeignCustomer
    # Customer name. May be omitted when the customer was already saved: the name is filled from
    # the CPF/CNPJ.
    name: str
    # CPF (11 digits) or CNPJ (14 digits), punctuation optional.
    taxId: str


class InvoiceDownloadUrl(TypedDict):
    downloadUrl: str
    expiresAt: str
    fileName: str
    mimeType: Literal["application/pdf", "application/xml"]


class InvoiceEmailRequest(TypedDict):
    emailId: str
    status: str


class InvoiceEvent(TypedDict):
    id: str
    invoiceId: str
    # An invoice status.
    fromStatus: Optional[str]
    # An invoice status.
    toStatus: str
    reason: Optional[str]
    createdAt: str
    source: Optional[Literal["portal"]]
    # Portal event type, such as REJEICAO_TOMADOR.
    portalEvent: Optional[str]
    portalNsu: Optional[str]


class InvoiceOptions(TypedDict, total=False):
    email: EmailOptions
    # Required when type is RECURRING; not allowed otherwise.
    recurrence: RecurrenceOptions
    # SCHEDULE and RECURRING do not issue now: they create a schedule (HTTP 202 with the schedule)
    # and competenceDate is the date of the first run, from tomorrow on. Runs happen at 09:00
    # America/Sao_Paulo on business days (Monday to Friday); a weekend date runs on Monday, and
    # the note takes the competence of the day it runs.
    type: Literal["IMMEDIATE", "SCHEDULE", "RECURRING"]


InvoiceOverview = TypedDict("InvoiceOverview", {"counts": "OverviewCounts", "dailyActivity": "List[OverviewDay]", "from": "str", "period": "Literal[\"7d\", \"30d\"]", "recentInvoices": "List[Invoice]", "timezone": "str", "to": "str"}, total=True)

class InvoiceReviewResultResultsItemVariant0(TypedDict):
    id: str
    outcome: Literal["accepted"]


class InvoiceReviewResultResultsItemVariant1(TypedDict):
    id: str
    outcome: Literal["skipped"]
    reason: Literal["not_found", "not_in_manual_review", "changed"]


class InvoiceReviewResult(TypedDict):
    # One entry per distinct id sent, in the order sent.
    results: List[Union[InvoiceReviewResultResultsItemVariant0, InvoiceReviewResultResultsItemVariant1]]


class InvoiceService(TypedDict, total=False):
    # National service code (6 digits). Inherits company.defaultServiceCode when omitted, then
    # 100901 (LC 116 item 10.09).
    code: str
    description: str
    # RTC fiscal classification for the service. Optional; passed through to the fiscal engine.
    fiscal: ServiceFiscal
    # Place of service (7 digits). Inherits company.municipalityCode when omitted.
    municipalityCode: str
    # Service profile id (UUID). Optional fiscal classification profile.
    serviceProfileId: str


class MunicipalityAgreement(TypedDict):
    # Whether the municipality joined the national NFS-e system, as the Receita answered.
    status: Literal["not_checked", "active", "inactive", "unknown", "not_found"]
    checkedAt: Optional[str]
    agreementType: Optional[str]


class _ObligationRequired(TypedDict):
    status: Literal["REQUIRED", "NOT_APPLICABLE", "UNSUPPORTED", "MISSING_CONFIGURATION"]


class Obligation(_ObligationRequired, total=False):
    missingFields: List[str]
    reason: str


class OverviewCounts(TypedDict):
    authorized: float
    rejected: float
    # Queued and processing invoices.
    processing: float


class OverviewDay(TypedDict):
    date: str
    count: float


class PackageSummary(TypedDict):
    month: str
    count: int
    # Sum of the amounts, in BRL.
    total: float
    # Most notes a package can hold.
    limit: int
    companyName: str
    companyTaxId: str


class PendingField(TypedDict):
    field: str
    reason: str


class Plan(TypedDict):
    id: str
    slug: Literal["free", "self-hosted", "solo", "equipe", "empresa", "escala"]
    name: str
    description: str
    # Notes included per month.
    monthlyCreditAllowance: int
    dailyLimit: Optional[int]
    maxActiveCompanies: int
    # Price of each note above the allowance.
    creditUnitPriceCents: int
    throughputRps: float
    includesWebhooks: bool
    includesXmlDownload: bool
    includesPdfDownload: bool
    includesApiKeys: bool
    supportTier: Literal["community", "email", "priority"]
    active: bool
    createdAt: str
    updatedAt: str


class PortalStatus(TypedDict):
    environment: Literal["test", "live"]
    # False while emission is paused because the national portal stopped answering; invoices wait
    # in the queue.
    available: bool
    since: Optional[str]
    retryAt: Optional[str]


class _PostalAddressRequired(TypedDict):
    street: str
    number: str
    district: str
    city: str
    state: str
    zip: str


class PostalAddress(_PostalAddressRequired, total=False):
    complement: str


class PurchasePreview(TypedDict):
    units: int
    unitPriceCents: int
    totalCents: int


class PutRules(TypedDict):
    rules: List[IntegrationRuleInput]


class _QuotaStatusRequired(TypedDict):
    canEmit: bool
    creditsRemaining: int
    creditsUsed: int
    creditsReserved: int
    monthlyAllowance: int
    dailyUsage: int
    dailyLimit: Optional[int]
    activeCompanies: int
    maxActiveCompanies: int
    periodStart: Optional[str]
    periodEnd: Optional[str]


class QuotaStatus(_QuotaStatusRequired, total=False):
    # Why `canEmit` is false.
    reason: Literal["no_credits", "daily_limit_exceeded", "company_limit_exceeded", "plan_blocked"]


class _RecurrenceOptionsRequired(TypedDict):
    frequency: Literal["WEEKLY", "BIWEEKLY", "MONTHLY"]


class RecurrenceOptions(_RecurrenceOptionsRequired, total=False):
    # Last day the recurrence may run (inclusive). Without it the recurrence runs until paused or
    # cancelled.
    endsOn: str


class RegistryWarning(TypedDict):
    code: Literal["TAX_REGIME_REGISTRY_MISMATCH", "MEI_MUNICIPALITY_MISMATCH"]
    message: str


class RequestInvoiceEmail(TypedDict, total=False):
    # Send to this address instead of the customer e-mail on the invoice.
    email: str


class ReviewInvoices(TypedDict):
    # retry: send again with the same DPS (never issues twice). discard: reject only after the
    # portal confirms the DPS was never registered.
    action: Literal["retry", "discard"]
    invoiceIds: List[str]


class SavedCustomer(TypedDict):
    # CPF or CNPJ, digits only.
    taxId: str
    name: str
    email: Optional[str]
    lastUsedAt: str
    createdAt: str
    updatedAt: str


class Schedule(TypedDict):
    id: str
    kind: Literal["once", "recurring"]
    frequency: Optional[Literal["WEEKLY", "BIWEEKLY", "MONTHLY"]]
    status: Literal["active", "paused", "completed", "cancelled"]
    pause_reason: Optional[Literal["customer", "failures"]]
    company_id: str
    anchor_on: str
    next_run_on: Optional[str]
    ends_on: Optional[str]
    # Failed attempts in a row on the pending run (0 to 3).
    attempts: float
    last_run_on: Optional[str]
    # The invoice body each run issues.
    invoice: Dict[str, Any]
    created_at: str


class ScheduleRun(TypedDict):
    id: str
    # The due date (may be a weekend day).
    occurrence_on: str
    # The day it actually ran.
    ran_on: str
    attempt: float
    outcome: Literal["issued", "failed"]
    invoice_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: str


class SendAccountantPackage(TypedDict):
    month: str


class ServiceFavorite(TypedDict):
    id: str
    tenantId: str
    companyId: str
    label: str
    description: str
    serviceCode: str
    # Default amount, in cents.
    amountCents: Optional[int]
    municipalityCode: Optional[str]
    createdAt: str


class ServiceFiscal(TypedDict, total=False):
    # Tax classification code — cClassTrib (6 digits, [0-9]{6}).
    classCode: str
    # Municipal tax code — cTribMun (3 digits, [0-9]{3}).
    cst: str
    # NBS code (9 digits, [0-9]{9}).
    nbsCode: str
    # Operation indicator — cIndOp (6 digits, [0-9]{6}).
    operationIndicator: str


class _ServiceSnapshotRequired(TypedDict):
    description: str
    code: str
    municipalityCode: str


class ServiceSnapshot(_ServiceSnapshotRequired, total=False):
    # RTC fiscal classification (nbsCode, cst, classCode, ...).
    fiscal: Dict[str, str]
    # Complementary information printed on the invoice (DPS xInfComp).
    notes: str
    # Customer purchase order (DPS xPed).
    purchaseOrder: str
    serviceProfileId: str


class ServiceTaxProfile(TypedDict):
    id: str
    tenantId: str
    companyId: str
    name: str
    serviceCode: str
    municipalServiceCode: Optional[str]
    nbsCode: Optional[str]
    cst: Optional[str]
    classCode: Optional[str]
    operationIndicator: Optional[str]
    operationNature: Literal["SERVICE", "GOODS", "MIXED", "PARTNER_SALON"]
    regimeApplicability: List[Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]]
    incidenceMunicipalityCode: Optional[str]
    issTaxation: Optional[Literal["NORMAL", "FIXED", "EXEMPT"]]
    issRate: Optional[str]
    issWithholdingDefault: bool
    withholdingPolicy: Literal["UNKNOWN", "NONE_CONFIRMED", "CONFIGURED"]
    withholdingRates: WithholdingRates
    # Inclusive.
    effectiveFrom: str
    # Exclusive.
    effectiveUntil: Optional[str]
    classificationSource: str
    reviewStatus: Literal["unreviewed", "approved", "rejected"]
    catalogVersion: Optional[str]
    createdAt: str


class SetDpsSequence(TypedDict, total=False):
    # The number of the last DPS the company already issued in this series (see the DPS number in
    # the last note, PDF or XML). The next note uses the following number.
    lastNumber: float


class _SubstituteInvoiceRequired(TypedDict):
    # Why the invoice is being substituted. Sent in the DPS as subst/xMotivo.
    description: str


class SubstituteInvoice(_SubstituteInvoiceRequired, total=False):
    # New notes. Omit to keep the original; send an empty text to remove it.
    notes: str
    # New purchase order. Omit to keep the original; send an empty text to remove it.
    purchaseOrder: str
    service: SubstituteService


class SubstituteService(TypedDict, total=False):
    # New service description.
    description: str


class TaxAmount(TypedDict):
    base: str
    rate: str
    amount: str


class UpdateAccountantPackage(TypedDict, total=False):
    # null or blank turns the monthly send off.
    accountantEmail: Optional[str]


class UpdateCompany(TypedDict, total=False):
    address: Optional[CompanyAddress]
    # Default cTribNac. Null removes the default; omission preserves it.
    defaultServiceCode: Optional[str]
    legalName: str
    municipalityCode: str
    municipalReg: Optional[str]
    # Send the municipal registration in the DPS.
    sendMunicipalReg: bool
    simpleNational: bool
    # Simples Nacional only: effective ISS rate (%) of your bracket. Only needed when a customer
    # withholds ISS. Ignored for MEI.
    simplesIssRate: Optional[str]
    # Simples Nacional only: effective total rate (%) of your DAS, sent in the invoice as
    # pTotTribSN. Required for Simples Nacional; ignored for MEI.
    simplesRate: str
    # Special tax regime (regEspTrib, RTC v1.01): 0 Nenhum, 1 Ato Cooperado, 2 Estimativa, 3
    # Microempresa Municipal, 4 Notário ou Registrador, 5 Profissional Autônomo, 6 Sociedade de
    # Profissionais. Empty string clears it.
    specialRegime: Literal["0", "1", "2", "3", "4", "5", "6"]
    # The CNPJ cannot be changed. Sending the current CNPJ is accepted and ignored; any other
    # value returns 422.
    taxId: str
    taxRegime: Literal["MEI", "Simples Nacional", "Lucro Presumido", "Lucro Real"]
    tradeName: str


class UpdateCredentials(TypedDict):
    credentials: Dict[str, str]


class UpdateCustomer(TypedDict, total=False):
    # Send null to remove the saved email.
    email: Optional[str]
    name: str


class UpdateImportRow(TypedDict, total=False):
    # Fields of the invoice to change (same shape as POST /invoices).
    item: Dict[str, Any]


class UpdateSchedule(TypedDict, total=False):
    anchorOn: str
    endsOn: Optional[str]
    frequency: Literal["WEEKLY", "BIWEEKLY", "MONTHLY"]
    # Invoice body fields to change; merged over the stored body and validated like an emission.
    invoice: Dict[str, Any]


class UpdateServiceTaxProfile(TypedDict, total=False):
    catalogVersion: Optional[str]
    classCode: Optional[str]
    classificationSource: str
    cst: Optional[str]
    effectiveFrom: str
    effectiveUntil: Optional[str]
    incidenceMunicipalityCode: Optional[str]
    issRate: Optional[str]
    issTaxation: Optional[Literal["NORMAL", "FIXED", "EXEMPT"]]
    issWithholdingDefault: bool
    municipalServiceCode: Optional[str]
    name: str
    nbsCode: Optional[str]
    operationIndicator: Optional[str]
    operationNature: Literal["SERVICE", "GOODS", "MIXED", "PARTNER_SALON"]
    regimeApplicability: List[Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]]
    serviceCode: str
    withholdingPolicy: Literal["UNKNOWN", "NONE_CONFIRMED", "CONFIGURED"]
    withholdingRates: Dict[str, str]


class _UpsertFiscalProfileRequired(TypedDict):
    # Tax regime for the new validity period.
    taxRegime: Literal["MEI", "SIMPLES_NACIONAL", "LUCRO_PRESUMIDO", "LUCRO_REAL", "OUTRO_REGIME", "UNKNOWN"]


class UpsertFiscalProfile(_UpsertFiscalProfileRequired, total=False):
    # When true the new validity period is recorded as approved by the acting user.
    confirm: bool
    ibsCbsRegularFrom: Optional[str]
    ibsCbsRegularOption: bool
    simpleNational: bool
    # How a ME/EPP apportions federal and municipal taxes (DPS regApTribSN). Only SN (1) is
    # supported; omit it for MEI. ISS_MUNICIPAL and REGULAR (above a sublimit) are refused.
    simplesApuracao: Optional[Literal["SN"]]
    # Special tax regime (regEspTrib, RTC v1.01): 0 Nenhum, 1 Ato Cooperado, 2 Estimativa, 3
    # Microempresa Municipal, 4 Notário ou Registrador, 5 Profissional Autônomo, 6 Sociedade de
    # Profissionais. Null means none.
    specialTaxRegime: Optional[Literal["0", "1", "2", "3", "4", "5", "6"]]
    # Start of the validity period (inclusive). Defaults to today. May be earlier than the whole
    # history, to cover competences before the company was registered.
    validFrom: str


class Webhook(TypedDict):
    id: str
    url: str
    events: List[WebhookEventType]
    # Set when an API key created it: it then only gets events of that environment.
    environment: Optional[Literal["test", "live"]]
    active: bool
    createdAt: str
    updatedAt: str


class _WebhookDeliveryRequired(TypedDict):
    id: str
    tenantId: str
    webhookConfigId: str
    eventType: str
    environment: Literal["test", "live"]
    url: str
    status: Literal["pending", "sent", "delayed", "failed", "manual_retry"]
    retryCount: int
    createdAt: str


class WebhookDelivery(_WebhookDeliveryRequired, total=False):
    durationMs: int
    errorMessage: str
    lastError: str
    nextRetryAt: str
    payload: Dict[str, Any]
    responseBody: str
    statusCode: int


class WebhookRetried(TypedDict):
    retried: Literal[True]


class WebhookStats(TypedDict):
    total: int
    sent: int
    failed: int
    pending: int
    delayed: int


class WebhookTestResultVariant0(TypedDict):
    sent: Literal[True]


class WebhookTestResultVariant1(TypedDict):
    sent: Literal[False]
    statusCode: Optional[int]
    error: str


class WebhookWithSecret(Webhook):
    # Signing secret. Shown only in this response: store it to verify deliveries.
    secret: str


class WithholdingAmount(TypedDict):
    base: str
    rate: str
    amount: str
    tax: Literal["ISS", "IRRF", "PIS", "COFINS", "CSLL", "INSS"]


class WithholdingRates(TypedDict, total=False):
    """Percent strings, e.g. "1.5"."""

    cofins: str
    csll: str
    inss: str
    irrf: str
    pis: str



WebhookEventType = Literal["nfse.invoice.authorized", "nfse.invoice.rejected", "nfse.invoice.failed", "nfse.invoice.reconciliation_required", "nfse.invoice.manual_review", "nfse.invoice.documents_ready", "nfse.invoice.email_sent", "nfse.invoice.email_failed", "nfse.invoice.fiscal_discrepancy", "nfse.invoice.cancelled", "nfse.invoice.cancellation_rejected", "nfse.invoice.taker_rejected"]
WebhookTestResult = Union[WebhookTestResultVariant0, WebhookTestResultVariant1]
