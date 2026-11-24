# corvo-nfse

**The Python SDK for the [Corvo](https://corvo.tech) NFS-e API.** Register companies, calculate taxes, issue Brazilian service invoices (NFS-e), follow them by webhook and download the PDF and XML, from Python 3.10+.

- **Async-first** on `httpx`, fully typed (`py.typed`, `mypy --strict` clean). Library only, no CLI.
- **Result-style errors.** API, network and timeout failures return `(None, error)`: a `CorvoApiError` carrying the server's stable `code`, the HTTP `status`, the `request_id`, field-level `details` and `retry_after`.
- **Pagination built in.** Every list returns `({data, pagination}, None)`, and `iterate()` walks all pages for you.
- **Safe retries.** Issuing an invoice and sending an email accept an idempotency key.
- **Webhook signature check** in constant time.

Full API reference: <https://corvo.tech/en/docs>. The machine-readable contract (OpenAPI 0.3.0) is <https://corvo.tech/openapi.json>; a copy lives in [`spec/openapi.json`](spec/openapi.json) and a test checks that every one of its 94 operations has an SDK method.

## Install

```bash
pip install corvo-nfse
```

## Quickstart

Start with a `corvo_test_...` key: invoices issued with it have no fiscal value.

```python
import asyncio

from corvo_nfse import Corvo


async def main() -> None:
    async with Corvo(api_key="corvo_test_...") as corvo:  # or set CORVO_API_KEY
        page, error = await corvo.companies.list(limit=10)
        if error is not None:
            # CorvoApiError: code, status, request_id, details, retry_after
            print(error.code, error.status, error.request_id, error.details)
        else:
            print(page["data"], page["pagination"])


asyncio.run(main())
```

`Corvo(...)` is the only call that raises: it fails fast with `ValueError` when no API key is configured or the base URL is invalid.

## Result style

Every API method returns `(data, error)` where exactly one is `None`:

```python
company, error = await corvo.companies.get("c_1")
if error is not None:
    handle(error)  # error.code, error.status, error.request_id, error.details
else:
    use(company)   # the API's JSON, camelCase as the server sends it
```

A `204 No Content` (deletions) returns `(None, None)`.

The one documented exception: the `iterate()` async generators raise `CorvoApiError` when a page fails, since a generator has no slot for a tuple.

```python
try:
    async for invoice in corvo.invoices.iterate(companyId=company_id):
        print(invoice["nfseNumber"])
except CorvoApiError as err:
    print(err.code, err.status)
```

## Register a company

```python
company, error = await corvo.companies.create(
    {
        "legalName": "Empresa Exemplo Ltda",
        "taxId": "11222333000181",
        "taxRegime": "Simples Nacional",  # "MEI" | "Simples Nacional" (the only regimes Corvo serves)
        "simplesRate": "6.54",  # required for Simples Nacional: effective DAS rate (%), ignored for MEI
        "municipalityCode": "3550308",  # IBGE code, 7 digits
        "defaultServiceCode": "010101",  # optional: used when an invoice omits service.code
    }
)
```

In `live`, also upload the A1 certificate (multipart is built for you). The company is ready when `company["status"] == "ready"` and `company["setupGaps"]` is empty.

```python
with open("certificado.pfx", "rb") as fh:
    cert, error = await corvo.certificates.upload(company["id"], fh.read(), password="...")
```

## Estimate the taxes before issuing

Nothing is issued, stored or charged.

```python
estimate, error = await corvo.invoices.calculate(
    {
        "companyTaxId": "11222333000181",
        "service": {"description": "Consultoria"},
        "amount": 1500,
        "competenceDate": "2026-10-16",
    }
)
# estimate["status"] is "ready" or "blocked": a fiscal gap is data, not an error.
```

## Issue an invoice

Issuing is asynchronous: a successful call means the request was accepted, not that the invoice is authorized. Follow the status with `invoices.get()` or webhooks.

```python
invoice, error = await corvo.invoices.create(
    {
        "companyTaxId": "11222333000181",  # or "companyId"
        # "customer" is optional; when sent, "taxId" (CPF or CNPJ) is required.
        "customer": {"taxId": "52998224725", "name": "Cliente", "email": "cliente@example.com"},
        "service": {"description": "Consultoria"},  # code and city default to the company's
        "amount": 150.5,
        "competenceDate": "2026-10-16",
        "options": {"email": {"send": True}},
    },
    idempotency_key="order-42",  # the same key never issues twice
)
```

### Schedule or repeat an invoice

`"options": {"type": "SCHEDULE"}` (once) and `"RECURRING"` (with `"recurrence": {"frequency": "WEEKLY" | "BIWEEKLY" | "MONTHLY", "endsOn": ...}`) do **not** return an invoice: they answer `202` with a *schedule* (snake_case fields). The note only exists when the schedule runs (09:00 America/Sao_Paulo, Monday to Friday). `competenceDate` is the date of the first run and must be from tomorrow on.

```python
schedule, error = await corvo.invoices.create(
    {
        "companyTaxId": "11222333000181",
        "service": {"description": "Mensalidade"},
        "amount": 300,
        "competenceDate": "2026-12-01",
        "options": {"type": "RECURRING", "recurrence": {"frequency": "MONTHLY"}},
    }
)
runs, error = await corvo.schedules.list_runs(schedule["id"])
await corvo.schedules.pause(schedule["id"])
```

Request bodies and responses are wire pass-through: camelCase stays camelCase (billing, schedules and imports answer in snake_case, as the API does).

To declare a deduction from the ISS base, send `"deduction"` (greater than 0 and less than `amount` minus `discount`). The invoice is still issued for the full `amount`, and you are responsible for the declared value.

## Issue up to 50 invoices at once

`create_batch` takes 1 to 50 items (they can belong to different companies). Items are checked one by one: valid ones are saved together, invalid ones come back `rejected` and are not saved. Send an `idempotencyKey` per item, so repeating the batch after a timeout returns the saved ones with `replayed`.

```python
batch, error = await corvo.invoices.create_batch(
    [
        {
            "companyTaxId": "11222333000181",
            "idempotencyKey": "sheet-row-2",
            "service": {"description": "Consultoria"},
            "amount": 150.5,
            "competenceDate": "2026-10-16",
        },
        {
            "companyTaxId": "11222333000181",
            "idempotencyKey": "sheet-row-3",
            "service": {"description": "Manutenção"},
            "amount": 300,
            "competenceDate": "2026-10-16",
        },
    ]
)
for result in batch["results"] if batch else []:
    if result["status"] == "rejected":
        print(result["index"], result["error"]["code"], result["error"]["message"])
```

The route allows 10 batches per minute per tenant (`429` with `Retry-After`).

## Cancel an invoice

```python
invoice, error = await corvo.invoices.cancel(
    invoice_id,
    {
        "reason": "issue_error",
        "description": "Wrong amount on the invoice",
    },  # reason: issue_error | service_not_provided | other
)
```

- `queued`: cancelled at once, `status == "cancelled"` with `cancelledAt` set.
- `authorized`: `status == "cancelling"` while the cancellation is processed at the Sefin. The issuance credit is not refunded.
- `processing`: stays `processing` with `cancellationRequestedAt` set and is cancelled once authorized.

`description` (15 to 255 characters) is required for an authorized or processing invoice and optional for a queued one. Read the invoice again (or listen to the `nfse.invoice.cancelled` and `nfse.invoice.cancellation_rejected` webhooks) to see the outcome: `cancelled`, or back to `authorized` with `lastErrorCode` when the cancellation was rejected.

## Look up a CNPJ, customers and favorite services

```python
profile, error = await corvo.cnpj.lookup("11222333000181")        # error.code == "CNPJ_INVALID" when malformed

page, error = await corvo.customers.search(search="ana", limit=20)  # saved customers, most recent first
customer, error = await corvo.customers.get("52998224725")
_, error = await corvo.customers.update("52998224725", {"email": "ana@example.com"})
_, error = await corvo.customers.remove("52998224725")            # issued invoices do not change

async for customer in corvo.customers.iterate():
    ...

fav, error = await corvo.service_favorites.create(
    company_id, {"label": "Consultoria", "description": "Consultoria em TI", "serviceCode": "010101"}
)
```

## Substitute an invoice and the monthly package

```python
new_invoice, error = await corvo.invoices.substitute(
    invoice_id, {"description": "Valor do servico corrigido"}, idempotency_key="sub-42"
)

summary, error = await corvo.invoice_package.summary(company_id, "2026-10")
zip_file, error = await corvo.invoice_package.download(company_id, "2026-10", include="xml")
settings, error = await corvo.accountant_package.update(company_id, {"accountantEmail": "contador@example.com"})
sent, error = await corvo.accountant_package.send(company_id, "2026-10")  # sent["status"], list_sends() for history
```

`invoices.send_email(invoice_id, email="outro@example.com")` sends to another address than the customer's. `invoices.list(customerTaxId="...")` filters by customer.

## Import a spreadsheet

```python
template, error = await corvo.imports.download_template()   # CSV bytes in template.content
job, error = await corvo.imports.start(open("notas.csv", "rb").read(), company_id=company_id)
job, error = await corvo.imports.get(job["id"])             # status: processing -> ready
async for row in corvo.imports.iterate_rows(job["id"], status="invalid"):
    await corvo.imports.update_row(job["id"], row["line"], {"item": {"amount": 100}})
await corvo.imports.emit(job["id"], {"sendEmail": True})
errors_csv, error = await corvo.imports.download_errors(job["id"])
```

## Walk every page

```python
async for invoice in corvo.invoices.iterate(companyId=company_id, status="authorized"):
    print(invoice["nfseNumber"])
```

## Download the PDF or XML

The invoice must be `authorized` and have its documents ready.

```python
pdf, error = await corvo.invoices.pdf(invoice["id"])
if pdf is not None:
    with open("nfse.pdf", "wb") as fh:
        fh.write(pdf.content)  # also pdf.mime_type and pdf.file_name
```

## Verify webhook signatures

```python
from corvo_nfse import CorvoWebhooks


async def webhook_handler(request) -> None:
    # Use the raw body: re-serialized JSON will never match the HMAC.
    signature = request.headers.get("X-Corvo-Signature")
    if not CorvoWebhooks.verify_signature(await request.body(), signature, secret):
        return  # reject with 400
    # Deduplicate by the event id: the same event can be delivered more than once.
```

Webhook events you can subscribe to are exported as `corvo_nfse.WEBHOOK_EVENTS`. The `webhook.test` event is only sent by `corvo.webhooks.test()`.

## Resources

Every contract operation (`operationId`) has a method; `test/test_contract_coverage.py` keeps the mapping.

| Namespace | Operations |
| --- | --- |
| `corvo.companies` | `create`, `get`, `update`, `remove`, `list`, `iterate` |
| `corvo.certificates` | `upload`, `list`, `remove` |
| `corvo.dps_sequence` | `get`, `set` |
| `corvo.fiscal_profiles` | `list`, `upsert`, `approve` |
| `corvo.service_tax_profiles` | `list`, `create`, `update`, `remove`, `approve` |
| `corvo.service_favorites` | `list`, `create`, `remove` |
| `corvo.accountant_package` | `get`, `update`, `send`, `list_sends` |
| `corvo.invoice_package` | `summary`, `download` |
| `corvo.invoices` | `create`, `create_batch`, `calculate`, `get`, `list`, `iterate`, `events`, `pdf`, `xml`, `download_url`, `send_email`, `cancel`, `substitute`, `overview`, `review` |
| `corvo.schedules` | `list`, `iterate`, `get`, `update`, `pause`, `resume`, `cancel`, `list_runs`, `iterate_runs` |
| `corvo.imports` | `start`, `list`, `get`, `emit`, `list_rows`, `iterate_rows`, `update_row`, `discard`, `download_template`, `download_errors` |
| `corvo.customers` | `search`, `iterate`, `get`, `update`, `remove` |
| `corvo.cnpj` | `lookup` |
| `corvo.integrations` | `list_providers` |
| `corvo.integration_connections` | `create`, `list`, `get`, `validate`, `update_credentials`, `activate`, `pause`, `disconnect`, `list_rules`, `replace_rules`, `list_events`, `list_operations` |
| `corvo.integration_operations` | `complete_customer`, `retry` |
| `corvo.webhooks` | `create`, `remove`, `test`, `list`, `iterate`, `.deliveries.list`, `.deliveries.iterate`, `.deliveries.stats`, `.deliveries.retry` |
| `corvo.credits` | `balance`, `plans`, `history`, `iterate_history`, `preview_purchase` |
| `corvo.billing` | `plan`, `usage` |
| `corvo.fiscal_portal` | `status` |
| `corvo.plans` | `list`, `get`, `quote` (public price catalog, not in the contract) |
| `corvo.health` | `live`, `ready` |

Plans are `free`, `solo`, `equipe`, `empresa` and `escala` (plus `self-hosted` on a self-hosted instance): treat the slug as an open string and read the allowances from the plan. `credits.balance()` returns `balance` (plan notes left plus loose notes), `planRemaining` and `avulsoBalance`; buying notes is done in the dashboard (`credits.preview_purchase(units)` only prices it).

Webhooks created with an API key belong to that key's environment: a `corvo_test_` key cannot reach live webhooks, and destinations on private networks are refused.

Changing plans, checkout and the billing portal exist only in the dashboard, so they are not in the SDK.

## Configuration

| Option | Env fallback | Default |
| --- | --- | --- |
| `api_key` | `CORVO_API_KEY` | required |
| `base_url` | `CORVO_BASE_URL` | `https://api.corvo.tech` |
| `prefix` | none | `v1` |
| `timeout` | none | `30.0` seconds |
| `allow_insecure_http` | none | `False` (`http://` only for loopback and private hosts) |
| `http_client` | none | an internal `httpx.AsyncClient` |

## Behavior

- **Auth.** Every request sends `X-API-Key` and a `User-Agent` of `corvo-nfse-python/<version>`. Keys are `corvo_test_...` or `corvo_live_...` and belong to one account and environment; the key decides the environment.
- **Responses.** Single resources and list items come back as the API's `data`; lists add `pagination`.
- **Errors.** Network failures, timeouts, non-2xx responses and malformed JSON all return a `CorvoApiError`. `code` is an open string (the API's `ERROR_*` codes and a few others such as `NO_PLAN_ASSIGNED`), falling back to `http_<status>`; `rate_limit` holds the `X-RateLimit-*` headers when sent; transport failures use `network_error`, `timeout` and `invalid_json`. On `429`, `retry_after` holds the seconds to wait.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest   # unit tests + contract coverage; the live test skips without env
python -m mypy src
ruff check . && ruff format --check .
```

The wire types in `src/corvo_nfse/types/models.py` are generated from `spec/openapi.json` (`python scripts/gen_models.py`); the client itself is hand-written. To adopt a new contract version, replace `spec/openapi.json`, regenerate, and add the new operations to `test/test_contract_coverage.py`.

The contract test in `test/contract/` runs only when `CORVO_API_KEY` and `CORVO_BASE_URL` point to a reachable instance.

## License

MIT, see [LICENSE](LICENSE).
