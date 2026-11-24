# Changelog

## 0.3.0

Follows the public API contract 0.3.0 ([openapi.json](https://corvo.tech/openapi.json), 94 operations).

### Breaking

- Plan slugs changed: `developer`, `growth`, `scale` and `volume` are gone; the slugs are `free`, `solo`, `equipe`, `empresa`, `escala` (and `self-hosted`). `CreditPlan.slug` is an open string now.
- `invoices.create()` with `options.type` `SCHEDULE` (and the new `RECURRING`) returns the **schedule** (snake_case fields), not an invoice. Follow it with `schedules.list_runs()`.
- `credits.balance()`: `overageUnits` and `overageAmountCents` removed; `planRemaining` and `avulsoBalance` added, and `balance` includes the loose notes.
- `billing.plan()`: `usage.overage_units` and `usage.overage_amount_cents` removed; `usage.avulso_balance`, `subscription.stripe_portal_available`, `stripe_subscription` and `pix_subscription` added; the 404 of a workspace without a plan has `code == "NO_PLAN_ASSIGNED"`.
- The purchase preview is `credits.preview_purchase(units)` (`GET /credits/purchase/preview?units=N`); the old `POST` only answered `410`.
- Invoice and webhook types follow the contract: `documentsReadyAt`, `documentsStatus`, `emailStatus`, `stage`, `lastEmailStatus`, `lastEmailSentAt` (no `documentsReady`/`lastEmail`); 12 webhook event types, with `nfse.invoice.taker_rejected`.
- Webhooks created with a `corvo_test_` key only see test events and cannot manage live webhooks; destinations on private networks are refused (API behavior, no code change).
- Wire types are now the generated `corvo_nfse.types.models` (re-exported under the old names). `Invoice`, `Company`, `CreditPlan`, `Webhook*` and the billing sections may have more or different keys; check them against the contract.
- Binary downloads (`invoices.pdf()`, `xml()` and the new ones) now return the API error when the status is 4xx/5xx instead of a file holding the error body.

### Added

- Public plan prices without an API key: `plans.list(cycle=...)` (`GET /plans`) and `plans.get(slug, cycle=...)` (`GET /plans/{slug}`), typed as `PlanPrice` (replaces `PlanQuote`).
- 51 operations: `customers.*`, `cnpj.lookup`, `service_favorites.*`, `accountant_package.*`, `invoice_package.*`, `invoices.substitute/overview/review`, `schedules.*`, `imports.*` (multipart upload, template and errors CSV), `fiscal_profiles.*`, `service_tax_profiles.*`, `dps_sequence.*`, `integrations.*`, `integration_connections.*`, `integration_operations.*`, `credits.preview_purchase`, `fiscal_portal.status`.
- `invoices.list(customerTaxId=...)`, `invoices.send_email(email=...)`; `RECURRING` options and `customer.foreign`, `purchaseOrder`, `notes` in the request types.
- `CorvoApiError.rate_limit` (`X-RateLimit-*`), error `details` as an object or a list, `User-Agent: corvo-nfse-python/<version>`, path segments percent-encoded.
- `spec/openapi.json` (vendored contract), `scripts/gen_models.py` and `test/test_contract_coverage.py` (every `operationId` must have an SDK method).

### Changed

- Contract corrections: `invoice_package.summary()` returns `total` as a decimal string (`"1234.50"`); company, invoice, schedule and webhook fields the API may answer with `null` are `Optional` (`tradeName`, `address*`, `municipalReg`, `defaultServiceCode`, tax rates, `emailStatus`, `lastEmailStatus`, `cancellationReason`, `portalFlag`, and `classification`/`applicability`/`calculation` of `invoices.calculate`); `nfseNumber`, `dpsNumber` and `DpsSequence.lastNumber` are integers; batch error `details` is a list of issues or an object; `stripe_subscription` is a boolean and `pix_subscription` an object or `None`.
- `companies.update()` no longer accepts `taxId`: the CNPJ is immutable.
- `imports.emit()` sends no body when called without params; `invoices.send_email()` already sent none.
- The generator reads `{"enum": [null]}` and `null` enum members as `Optional`.
- CI: Python 3.10 to 3.13, `ruff` lint and format, generated models checked against the spec. The publish workflow also runs `ruff`.
