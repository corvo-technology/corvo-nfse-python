# corvo-nfse

**The Python SDK for the Corvo NFS-e API — result-style errors, cursor pagination you don't have to think about, and webhook signatures that verify in one call.**

Issue, list, download, and reconcile Brazilian electronic service invoices (NFS-e) from a Python 3.10+ app. Async-first on `httpx`, fully typed (`py.typed`), library only — no CLI.

## Why corvo-nfse

- **Errors that never throw.** API, network, and timeout failures return `(None, error)` — a `CorvoApiError` carrying the server's stable `code`, HTTP `status`, `request_id`, field-level `details`, and `retry_after`. Raise it yourself if you prefer.
- **Self-hosted first.** Point it at your own Corvo install; the public default `https://api.corvo.tech` only applies when you don't.
- **Pagination you don't have to think about.** Every list returns `({data, pagination}, None)` with an opaque cursor. Want every page? `async for ... in corvo.invoices.iterate(...)` walks them for you.
- **Fully typed.** TypedDict wire types mirror the verified API contract; `mypy --strict` clean.

## Install

```bash
pip install corvo-nfse
```

## Quickstart

```python
import asyncio

from corvo_nfse import Corvo

async def main() -> None:
    corvo = Corvo(
        api_key="corvo_live_xxx",          # or set CORVO_API_KEY
        base_url="https://api.corvo.tech", # or CORVO_BASE_URL for your self-hosted install
    )

    data, error = await corvo.companies.list(limit=10)
    if error is not None:
        # CorvoApiError: code, status, request_id, details, retry_after
        print(error.code, error.status, error.request_id, error.details)
    else:
        print(data["data"], data["pagination"])

asyncio.run(main())
```

Or use the client as an async context manager to close the connection pool:

```python
async with Corvo(api_key="corvo_live_xxx") as corvo:
    ...
```

## Result style

Every API method returns a 2-tuple `(data, error)` where **exactly one is `None`**:

```python
data, error = await corvo.companies.get("c_1")
if error is not None:
    handle(error)  # error.code, error.status, error.request_id, error.details
else:
    use(data)      # unwrapped payload (dict, raw JSON pass-through)
```

Deletions (`204 No Content`) return `(None, None)` — success with no body.

The **one documented exception**: the `iterate()` async generators raise `CorvoApiError` on a page failure, since an async generator has no channel to return a tuple. Wrap the loop if you prefer results:

```python
try:
    async for invoice in corvo.invoices.iterate(companyId=company_id):
        print(invoice["nfseNumber"])
except CorvoApiError as err:
    print(err.code, err.status)
```

## Issue an invoice

```python
invoice, error = await corvo.invoices.create(
    {
        "companyId": "...",
        "customer": {"name": "Customer", "taxId": "52998224725", "email": "a@b.com"},
        "service": {"code": "010101", "municipalityCode": "3170206", "description": "Services"},
        "amount": 150.5,
        "competenceDate": "2026-10-12",
    },
    idempotency_key="order-42",  # safe to retry without double-issuing
)
```

Request bodies and responses are **wire pass-through**: camelCase stays camelCase, exactly as the server speaks it. No re-casing, no silent surprises.

## Download the PDF or XML of an authorized invoice

```python
pdf, error = await corvo.invoices.pdf(invoice["id"])
if pdf is not None:
    with open("nfse.pdf", "wb") as fh:
        fh.write(pdf.content)  # pdf.mime_type and pdf.file_name included
```

## Walk every page without thinking about cursors

```python
async for invoice in corvo.invoices.iterate(companyId=company_id, status="authorized"):
    print(invoice["nfseNumber"])
```

## Upload an A1 certificate (multipart, built for you)

```python
with open("cert.p12", "rb") as fh:
    cert, error = await corvo.certificates.upload(company_id, fh.read(), password="...")
```

## Verify webhook signatures

```python
from corvo_nfse import CorvoWebhooks

async def webhook_handler(request) -> None:
    # Use the RAW request body — re-serialized JSON will never match the HMAC.
    signature = request.headers.get("X-Corvo-Signature")
    if not CorvoWebhooks.verify_signature(await request.body(), signature, secret):
        return  # reject: 400
    # ... handle event
```

Verification is constant-time (`hmac.compare_digest`).

## Resources

| Namespace | Operations |
| --- | --- |
| `corvo.companies` | `create`, `get`, `update`, `remove`, `list`, `iterate` |
| `corvo.certificates` | `upload`, `list`, `remove` |
| `corvo.invoices` | `create`, `get`, `list`, `iterate`, `events`, `pdf`, `xml`, `download_url`, `send_email` |
| `corvo.webhooks` | `create`, `remove`, `test`, `list`, `iterate`, `.deliveries.list`, `.deliveries.iterate`, `.deliveries.stats`, `.deliveries.retry` |
| `corvo.credits` | `balance`, `plans`, `history`, `iterate_history` |
| `corvo.billing` | `plan`, `usage` |
| `corvo.health` | `live`, `ready` (public, no envelope) |

Webhook events: `nfse.invoice.authorized`, `nfse.invoice.rejected`, `nfse.invoice.failed`, `nfse.invoice.reconciliation_required`, `nfse.invoice.manual_review`, `nfse.invoice.documents_ready`, `nfse.invoice.email_sent`, `nfse.invoice.email_failed`, `webhook.test` — exported as `corvo_nfse.WEBHOOK_EVENTS`.

## Configuration

| Option | Env fallback | Default |
| --- | --- | --- |
| `api_key` | `CORVO_API_KEY` | required (`ValueError` if missing) |
| `base_url` | `CORVO_BASE_URL` | `https://api.corvo.tech` |
| `prefix` | — | `v1` |
| `timeout` | — | `30.0` seconds |
| `allow_insecure_http` | — | `False` (`http://` only allowed for loopback/private hosts) |

## Development

```bash
python -m pip install -e ".[dev]"
python -m compileall -q src   # byte-compile
pytest                        # unit + resource tests (mocked HTTP via respx)
mypy src                      # strict type check
```

Contract tests run only when `CORVO_API_KEY` and `CORVO_BASE_URL` are set against a reachable instance; they skip automatically otherwise.

## License

MIT — see [LICENSE](LICENSE).
