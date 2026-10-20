# corvo-nfse

**The Python SDK for the [Corvo](https://corvo.tech) NFS-e API.** Register companies, calculate taxes, issue Brazilian service invoices (NFS-e), follow them by webhook and download the PDF and XML, from Python 3.10+.

- **Async-first** on `httpx`, fully typed (`py.typed`, `mypy --strict` clean). Library only, no CLI.
- **Result-style errors.** API, network and timeout failures return `(None, error)`: a `CorvoApiError` carrying the server's stable `code`, the HTTP `status`, the `request_id`, field-level `details` and `retry_after`.
- **Pagination built in.** Every list returns `({data, pagination}, None)`, and `iterate()` walks all pages for you.
- **Safe retries.** Issuing an invoice and sending an email accept an idempotency key.
- **Webhook signature check** in constant time.

Full API reference: <https://corvo.tech/en/docs>.

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
        "taxRegime": "Simples Nacional",  # "MEI" | "Simples Nacional" | "Lucro Presumido" | "Lucro Real"
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

Use `"options": {"type": "SCHEDULE"}` with a future `competenceDate` to schedule the issuance. Request bodies and responses are wire pass-through: camelCase stays camelCase.

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

## Cancel an invoice

`reason` is one of `"issue_error"`, `"service_not_provided"` or `"other"` (`InvoiceCancellationReason`). `description` (up to 255 characters) is optional for a `queued` invoice; for an `authorized` or `processing` invoice the API requires 15 to 255 characters and answers `422` otherwise.

```python
invoice, error = await corvo.invoices.cancel(
    invoice_id,
    reason="issue_error",
    description="Wrong amount on the invoice",
)
if error is not None:
    # 409 ERROR_INVOICE_NOT_CANCELLABLE: retry_pending, reconciliation_required or manual_review
    print(error.code, error.status)
```

The returned invoice tells you where the cancellation stands:

- `queued` invoices are cancelled right away: `status == "cancelled"` and `cancelledAt` is set.
- `authorized` invoices go to `status == "cancelling"` while the Sefin processes the cancellation event. Cancelling an issued NFS-e does not refund the credit.
- `processing` invoices stay `processing` with `cancellationRequestedAt` set, and are cancelled once issued.

Repeating the request returns the current state. Check the result later with `get()`:

```python
invoice, error = await corvo.invoices.get(invoice_id)
if invoice is not None:
    if invoice["status"] == "cancelled":
        print("cancelled at", invoice["cancelledAt"], invoice["cancellationReason"])
    elif invoice["status"] == "cancelling":
        print("still processing at the Sefin")
    elif invoice["status"] == "authorized" and invoice["lastErrorCode"]:
        # The Sefin rejected the cancellation.
        print(invoice["lastErrorCode"], invoice["lastErrorMessage"])
```

The `nfse.invoice.cancelled` and `nfse.invoice.cancellation_rejected` webhook events report the outcome too.

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

| Namespace | Operations |
| --- | --- |
| `corvo.companies` | `create`, `get`, `update`, `remove`, `list`, `iterate` |
| `corvo.certificates` | `upload`, `list`, `remove` |
| `corvo.invoices` | `create`, `calculate`, `get`, `list`, `iterate`, `events`, `pdf`, `xml`, `download_url`, `send_email`, `cancel` |
| `corvo.webhooks` | `create`, `remove`, `test`, `list`, `iterate`, `.deliveries.list`, `.deliveries.iterate`, `.deliveries.stats`, `.deliveries.retry` |
| `corvo.credits` | `balance`, `plans`, `history`, `iterate_history` |
| `corvo.billing` | `plan`, `usage` |
| `corvo.plans` | `list`, `get`, `quote` (public price catalog) |
| `corvo.health` | `live`, `ready` |

Changing plans and the billing portal exist only in the dashboard, so they are not in the SDK.

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

- **Auth.** Every request sends `X-API-Key`. Keys are `corvo_test_...` or `corvo_live_...` and belong to one account and environment; the key decides the environment.
- **Responses.** Single resources and list items come back as the API's `data`; lists add `pagination`.
- **Errors.** Network failures, timeouts, non-2xx responses and malformed JSON all return a `CorvoApiError`. `code` is the API's `ERROR_*` code, falling back to `http_<status>`; transport failures use `network_error`, `timeout` and `invalid_json`. On `429`, `retry_after` holds the seconds to wait.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest   # unit tests; the contract test skips without env
python -m mypy src
```

The contract test in `test/contract/` runs only when `CORVO_API_KEY` and `CORVO_BASE_URL` point to a reachable instance.

## License

MIT, see [LICENSE](LICENSE).
