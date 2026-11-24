"""Contract 0.3.0 resources: request shapes, parsing, pagination, downloads and errors."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from conftest import API_KEY, BASE_URL, collect, corvo

from corvo_nfse import VERSION, Corvo

V1 = f"{BASE_URL}/v1"


def _page(items: list, next_cursor: str | None = None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "data": items,
            "pagination": {
                "limit": 2,
                "hasMore": next_cursor is not None,
                "nextCursor": next_cursor,
            },
        },
    )


def test_version_matches_pyproject() -> None:
    text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()
    assert f'version = "{VERSION}"' in text
    assert VERSION == "0.3.0"


@respx.mock
async def test_requests_send_api_key_and_user_agent(corvo: Corvo) -> None:
    route = respx.get(f"{V1}/credits").mock(return_value=httpx.Response(200, json={"data": {}}))
    await corvo.credits.balance()
    headers = route.calls[0].request.headers
    assert headers["x-api-key"] == API_KEY
    assert headers["user-agent"] == f"corvo-nfse-python/{VERSION}"


# --- breaking changes ---------------------------------------------------------------------------


@respx.mock
async def test_credits_balance_has_the_new_fields(corvo: Corvo) -> None:
    respx.get(f"{V1}/credits").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"balance": 12, "planRemaining": 10, "avulsoBalance": 2, "hardLimit": 0}},
        )
    )
    data, error = await corvo.credits.balance()
    assert error is None and data is not None
    assert data["balance"] == data["planRemaining"] + data["avulsoBalance"]
    assert "overageUnits" not in data


@respx.mock
async def test_credits_preview_purchase_is_a_get_with_units(corvo: Corvo) -> None:
    route = respx.get(f"{V1}/credits/purchase/preview").mock(
        return_value=httpx.Response(
            200, json={"data": {"units": 5, "unitPriceCents": 99, "totalCents": 495}}
        )
    )
    data, error = await corvo.credits.preview_purchase(5)
    assert error is None and data is not None
    assert route.calls[0].request.url.params["units"] == "5"
    assert data["totalCents"] == 495


@respx.mock
async def test_billing_plan_no_plan_assigned_is_an_error_value(corvo: Corvo) -> None:
    respx.get(f"{V1}/billing/plan").mock(
        return_value=httpx.Response(
            404,
            json={
                "statusCode": 404,
                "code": "NO_PLAN_ASSIGNED",
                "message": "No plan",
                "requestId": "r1",
            },
            headers={"Content-Type": "application/json"},
        )
    )
    data, error = await corvo.billing.plan()
    assert data is None and error is not None
    assert error.code == "NO_PLAN_ASSIGNED"
    assert error.request_id == "r1"


@respx.mock
async def test_billing_plan_new_subscription_fields(corvo: Corvo) -> None:
    body = {
        "plan": {
            "slug": "solo",
            "name": "Solo",
            "monthly_allowance": 100,
            "daily_limit": None,
            "max_active_companies": 1,
            "monthly_price_cents": 4900,
        },
        "subscription": {
            "status": "active",
            "paid_until": None,
            "cancel_at_period_end": False,
            "scheduled_plan": None,
            "blocked": False,
            "stripe_portal_available": True,
            "stripe_subscription": True,
            "pix_subscription": None,
        },
        "usage": {"avulso_balance": 3},
    }
    respx.get(f"{V1}/billing/plan").mock(return_value=httpx.Response(200, json={"data": body}))
    data, error = await corvo.billing.plan()
    assert error is None and data is not None
    assert data["plan"]["slug"] == "solo"
    assert data["subscription"]["stripe_portal_available"] is True
    assert data["usage"]["avulso_balance"] == 3


@respx.mock
async def test_invoices_create_schedule_returns_the_schedule(corvo: Corvo) -> None:
    schedule = {
        "id": "s_1",
        "kind": "recurring",
        "frequency": "MONTHLY",
        "status": "active",
        "company_id": "c_1",
        "next_run_on": "2026-12-01",
        "invoice": {},
    }
    route = respx.post(f"{V1}/invoices").mock(
        return_value=httpx.Response(202, json={"data": schedule})
    )
    data, error = await corvo.invoices.create(
        {
            "companyId": "c_1",
            "service": {"description": "Mensalidade"},
            "amount": 100,
            "competenceDate": "2026-12-01",
            "options": {"type": "RECURRING", "recurrence": {"frequency": "MONTHLY"}},
        },
        idempotency_key="idem-1",
    )
    assert error is None and data is not None
    assert data["kind"] == "recurring" and data["company_id"] == "c_1"
    request = route.calls[0].request
    assert request.headers["Idempotency-Key"] == "idem-1"
    assert json.loads(request.content)["options"]["recurrence"] == {"frequency": "MONTHLY"}


# --- invoices -----------------------------------------------------------------------------------


@respx.mock
async def test_invoices_list_filters_by_customer_tax_id(corvo: Corvo) -> None:
    route = respx.get(f"{V1}/invoices").mock(return_value=_page([]))
    _, error = await corvo.invoices.list(customerTaxId="52998224725", limit=5)
    assert error is None
    params = route.calls[0].request.url.params
    assert params["customerTaxId"] == "52998224725" and params["limit"] == "5"


@respx.mock
async def test_send_email_to_another_address(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/invoices/i_1/email").mock(
        return_value=httpx.Response(202, json={"data": {"emailId": "e_1", "status": "queued"}})
    )
    data, error = await corvo.invoices.send_email(
        "i_1", email="contador@example.com", idempotency_key="k"
    )
    assert error is None and data == {"emailId": "e_1", "status": "queued"}
    request = route.calls[0].request
    assert json.loads(request.content) == {"email": "contador@example.com"}
    assert request.headers["Idempotency-Key"] == "k"


@respx.mock
async def test_send_email_without_body_keeps_working(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/invoices/i_1/email").mock(
        return_value=httpx.Response(202, json={"data": {"emailId": "e_1", "status": "queued"}})
    )
    _, error = await corvo.invoices.send_email("i_1")
    assert error is None
    assert route.calls[0].request.content == b""


@respx.mock
async def test_substitute_sends_idempotency_key_and_body(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/invoices/i_1/substitute").mock(
        return_value=httpx.Response(
            202, json={"data": {"id": "i_2", "substitutesInvoiceId": "i_1"}}
        )
    )
    data, error = await corvo.invoices.substitute(
        "i_1",
        {"description": "Valor corrigido no servico", "notes": "nova"},
        idempotency_key="sub-1",
    )
    assert error is None and data is not None
    assert data["substitutesInvoiceId"] == "i_1"
    request = route.calls[0].request
    assert request.headers["Idempotency-Key"] == "sub-1"
    assert json.loads(request.content)["notes"] == "nova"


@respx.mock
async def test_substitute_error_code_comes_back_as_a_value(corvo: Corvo) -> None:
    respx.post(f"{V1}/invoices/i_1/substitute").mock(
        return_value=httpx.Response(
            409,
            json={
                "statusCode": 409,
                "code": "ERROR_INVOICE_NOT_SUBSTITUTABLE",
                "message": "no",
                "requestId": "r",
            },
        )
    )
    data, error = await corvo.invoices.substitute("i_1", {"description": "x" * 15})
    assert data is None and error is not None
    assert error.code == "ERROR_INVOICE_NOT_SUBSTITUTABLE" and error.status == 409


@respx.mock
async def test_overview_and_review(corvo: Corvo) -> None:
    respx.get(f"{V1}/invoices/overview").mock(
        return_value=httpx.Response(200, json={"data": {"period": "30d", "counts": {}}})
    )
    review = respx.post(f"{V1}/invoices/review").mock(
        return_value=httpx.Response(
            202, json={"data": {"results": [{"id": "a", "outcome": "accepted"}]}}
        )
    )
    overview, error = await corvo.invoices.overview(period="30d")
    assert error is None and overview is not None and overview["period"] == "30d"
    result, error = await corvo.invoices.review({"action": "retry", "invoiceIds": ["a"]})
    assert error is None and result is not None
    assert result["results"][0]["outcome"] == "accepted"
    assert json.loads(review.calls[0].request.content) == {"action": "retry", "invoiceIds": ["a"]}


@respx.mock
async def test_invoice_package_summary_and_zip_download(corvo: Corvo) -> None:
    respx.get(f"{V1}/companies/c_1/invoice-package/summary").mock(
        return_value=httpx.Response(
            200, json={"data": {"month": "2026-10", "count": 3, "total": "450.50"}}
        )
    )
    zip_route = respx.get(f"{V1}/companies/c_1/invoice-package").mock(
        return_value=httpx.Response(
            200,
            content=b"PK\x03\x04zip",
            headers={
                "Content-Type": "application/zip",
                "Content-Disposition": 'attachment; filename="pacote-2026-10.zip"',
            },
        )
    )
    summary, error = await corvo.invoice_package.summary("c_1", "2026-10")
    assert (
        error is None
        and summary is not None
        and summary["count"] == 3
        and summary["total"] == "450.50"
    )
    file, error = await corvo.invoice_package.download("c_1", "2026-10", include="pdf")
    assert error is None and file is not None
    assert file.content == b"PK\x03\x04zip"
    assert file.mime_type == "application/zip" and file.file_name == "pacote-2026-10.zip"
    params = zip_route.calls[0].request.url.params
    assert params["month"] == "2026-10" and params["include"] == "pdf"


@respx.mock
async def test_downloads_return_the_error_on_failure(corvo: Corvo) -> None:
    respx.get(f"{V1}/companies/c_1/invoice-package").mock(
        return_value=httpx.Response(
            413,
            json={
                "statusCode": 413,
                "code": "PACKAGE_TOO_LARGE",
                "message": "too big",
                "requestId": "r",
            },
        )
    )
    file, error = await corvo.invoice_package.download("c_1", "2026-10")
    assert file is None and error is not None
    assert error.code == "PACKAGE_TOO_LARGE"


# --- customers, cnpj, favorites -----------------------------------------------------------------


@respx.mock
async def test_customers_search_get_update_remove(corvo: Corvo) -> None:
    customer = {"taxId": "52998224725", "name": "Ana", "email": None}
    search = respx.get(f"{V1}/customers").mock(return_value=_page([customer]))
    respx.get(f"{V1}/customers/52998224725").mock(
        return_value=httpx.Response(200, json={"data": customer})
    )
    patch = respx.patch(f"{V1}/customers/52998224725").mock(
        return_value=httpx.Response(200, json={"data": {**customer, "name": "Ana Maria"}})
    )
    delete = respx.delete(f"{V1}/customers/52998224725").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )
    page, error = await corvo.customers.search(search="ana", limit=10)
    assert error is None and page is not None and page["data"] == [customer]
    assert search.calls[0].request.url.params["search"] == "ana"
    got, error = await corvo.customers.get("52998224725")
    assert error is None and got == customer
    updated, error = await corvo.customers.update("52998224725", {"name": "Ana Maria"})
    assert error is None and updated is not None and updated["name"] == "Ana Maria"
    assert json.loads(patch.calls[0].request.content) == {"name": "Ana Maria"}
    removed, error = await corvo.customers.remove("52998224725")
    assert error is None and removed == {"deleted": True}
    assert delete.call_count == 1


@respx.mock
async def test_customers_iterate_follows_the_cursor(corvo: Corvo) -> None:
    route = respx.get(f"{V1}/customers").mock(
        side_effect=[
            _page([{"taxId": "1"}, {"taxId": "2"}], next_cursor="2"),
            _page([{"taxId": "3"}]),
        ]
    )
    items = await collect(corvo.customers.iterate(limit=2))
    assert [i["taxId"] for i in items] == ["1", "2", "3"]
    assert route.calls[1].request.url.params["cursor"] == "2"


@respx.mock
async def test_cnpj_lookup_and_its_error(corvo: Corvo) -> None:
    respx.get(f"{V1}/cnpj/11222333000181").mock(
        return_value=httpx.Response(
            200, json={"data": {"cnpj": "11222333000181", "legalName": "ACME"}}
        )
    )
    respx.get(f"{V1}/cnpj/123").mock(
        return_value=httpx.Response(
            422,
            json={"statusCode": 422, "code": "CNPJ_INVALID", "message": "bad", "requestId": "r"},
        )
    )
    data, error = await corvo.cnpj.lookup("11222333000181")
    assert error is None and data is not None and data["legalName"] == "ACME"
    data, error = await corvo.cnpj.lookup("123")
    assert data is None and error is not None and error.code == "CNPJ_INVALID"


@respx.mock
async def test_service_favorites_crud(corvo: Corvo) -> None:
    fav = {"id": "f_1", "label": "Consultoria", "description": "d", "serviceCode": "010101"}
    respx.get(f"{V1}/companies/c_1/service-favorites").mock(
        return_value=httpx.Response(200, json={"data": [fav]})
    )
    create = respx.post(f"{V1}/companies/c_1/service-favorites").mock(
        return_value=httpx.Response(201, json={"data": fav})
    )
    respx.delete(f"{V1}/companies/c_1/service-favorites/f_1").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )
    listed, error = await corvo.service_favorites.list("c_1")
    assert error is None and listed == [fav]
    created, error = await corvo.service_favorites.create(
        "c_1",
        {"label": "Consultoria", "description": "d", "serviceCode": "010101", "amountCents": 15000},
    )
    assert error is None and created == fav
    assert json.loads(create.calls[0].request.content)["amountCents"] == 15000
    removed, error = await corvo.service_favorites.remove("c_1", "f_1")
    assert error is None and removed == {"deleted": True}


# --- accountant package -------------------------------------------------------------------------


@respx.mock
async def test_accountant_package_flow(corvo: Corvo) -> None:
    respx.get(f"{V1}/companies/c_1/accountant-package").mock(
        return_value=httpx.Response(
            200, json={"data": {"email": "a@b.co", "lastSentMonth": "2026-09"}}
        )
    )
    put = respx.put(f"{V1}/companies/c_1/accountant-package").mock(
        return_value=httpx.Response(200, json={"data": {"email": None, "lastSentMonth": "2026-09"}})
    )
    send = respx.post(f"{V1}/companies/c_1/accountant-package/send").mock(
        return_value=httpx.Response(200, json={"data": {"status": "sent"}})
    )
    sends = respx.get(f"{V1}/companies/c_1/accountant-package/sends").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "x", "month": "2026-09", "status": "sent"}]}
        )
    )
    settings, error = await corvo.accountant_package.get("c_1")
    assert error is None and settings is not None and settings["email"] == "a@b.co"
    _, error = await corvo.accountant_package.update("c_1", {"accountantEmail": None})
    assert error is None
    assert json.loads(put.calls[0].request.content) == {"accountantEmail": None}
    result, error = await corvo.accountant_package.send("c_1", "2026-10")
    assert error is None and result == {"status": "sent"}
    assert json.loads(send.calls[0].request.content) == {"month": "2026-10"}
    listed, error = await corvo.accountant_package.list_sends("c_1")
    assert error is None and listed is not None and listed[0]["status"] == "sent"
    assert sends.call_count == 1


# --- schedules ----------------------------------------------------------------------------------


@respx.mock
async def test_schedules_lifecycle(corvo: Corvo) -> None:
    schedule = {"id": "s_1", "kind": "recurring", "status": "active", "company_id": "c_1"}
    respx.get(f"{V1}/schedules/s_1").mock(return_value=httpx.Response(200, json={"data": schedule}))
    patch = respx.patch(f"{V1}/schedules/s_1").mock(
        return_value=httpx.Response(200, json={"data": {**schedule, "ends_on": "2027-01-01"}})
    )
    pause = respx.post(f"{V1}/schedules/s_1/pause").mock(
        return_value=httpx.Response(200, json={"data": {**schedule, "status": "paused"}})
    )
    resume = respx.post(f"{V1}/schedules/s_1/resume").mock(
        return_value=httpx.Response(200, json={"data": schedule})
    )
    cancel = respx.post(f"{V1}/schedules/s_1/cancel").mock(
        return_value=httpx.Response(200, json={"data": {**schedule, "status": "cancelled"}})
    )
    got, error = await corvo.schedules.get("s_1")
    assert error is None and got == schedule
    updated, error = await corvo.schedules.update("s_1", {"endsOn": "2027-01-01"})
    assert error is None and updated is not None and updated["ends_on"] == "2027-01-01"
    assert json.loads(patch.calls[0].request.content) == {"endsOn": "2027-01-01"}
    paused, _ = await corvo.schedules.pause("s_1")
    assert paused is not None and paused["status"] == "paused"
    await corvo.schedules.resume("s_1")
    cancelled, _ = await corvo.schedules.cancel("s_1")
    assert cancelled is not None and cancelled["status"] == "cancelled"
    assert pause.call_count == resume.call_count == cancel.call_count == 1


@respx.mock
async def test_schedules_list_filters_and_iterate_runs(corvo: Corvo) -> None:
    listed = respx.get(f"{V1}/schedules").mock(return_value=_page([]))
    runs = respx.get(f"{V1}/schedules/s_1/runs").mock(
        side_effect=[_page([{"id": "r1"}], next_cursor="1"), _page([{"id": "r2"}])]
    )
    _, error = await corvo.schedules.list(status="paused", company_id="c_1")
    assert error is None
    params = listed.calls[0].request.url.params
    assert params["status"] == "paused" and params["companyId"] == "c_1"
    items = await collect(corvo.schedules.iterate_runs("s_1"))
    assert [r["id"] for r in items] == ["r1", "r2"]
    assert runs.calls[1].request.url.params["cursor"] == "1"


# --- imports ------------------------------------------------------------------------------------


@respx.mock
async def test_imports_start_is_multipart(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/imports").mock(
        return_value=httpx.Response(
            202, json={"data": {"id": "i_1", "status": "processing", "duplicate_of": None}}
        )
    )
    data, error = await corvo.imports.start(
        b"cnpj;valor\n1;2", company_id="c_1", file_name="notas.csv"
    )
    assert error is None and data is not None and data["status"] == "processing"
    request = route.calls[0].request
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'filename="notas.csv"' in request.content
    assert b"text/csv" in request.content
    assert b'name="companyId"' in request.content and b"c_1" in request.content


@respx.mock
async def test_imports_start_xlsx_content_type(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/imports").mock(
        return_value=httpx.Response(
            202, json={"data": {"id": "i_1", "status": "processing", "duplicate_of": None}}
        )
    )
    await corvo.imports.start(b"x", file_name="notas.xlsx")
    assert b"spreadsheetml.sheet" in route.calls[0].request.content
    assert b'name="companyId"' not in route.calls[0].request.content


@respx.mock
async def test_imports_flow_and_downloads(corvo: Corvo) -> None:
    respx.get(f"{V1}/imports").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "i_1"}]})
    )
    respx.get(f"{V1}/imports/i_1").mock(
        return_value=httpx.Response(200, json={"data": {"id": "i_1", "status": "ready"}})
    )
    emit = respx.post(f"{V1}/imports/i_1/emit").mock(
        return_value=httpx.Response(202, json={"data": {"id": "i_1", "status": "emitting"}})
    )
    rows = respx.get(f"{V1}/imports/i_1/rows").mock(
        side_effect=[_page([{"line": 2}], next_cursor="2"), _page([{"line": 3}])]
    )
    row = respx.patch(f"{V1}/imports/i_1/rows/3").mock(
        return_value=httpx.Response(200, json={"data": {"line": 3}})
    )
    discard = respx.delete(f"{V1}/imports/i_1").mock(return_value=httpx.Response(204))
    template = respx.get(f"{V1}/imports/template").mock(
        return_value=httpx.Response(
            200,
            content=b"cnpj;valor\n",
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": 'attachment; filename="modelo.csv"',
            },
        )
    )
    errors = respx.get(f"{V1}/imports/i_1/errors.csv").mock(
        return_value=httpx.Response(
            200, content=b"line;error\n", headers={"Content-Type": "text/csv"}
        )
    )
    listed, error = await corvo.imports.list(limit=5)
    assert error is None and listed == [{"id": "i_1"}]
    job, error = await corvo.imports.get("i_1")
    assert error is None and job is not None and job["status"] == "ready"
    emitted, error = await corvo.imports.emit("i_1", {"sendEmail": True})
    assert error is None and emitted is not None and emitted["status"] == "emitting"
    assert json.loads(emit.calls[0].request.content) == {"sendEmail": True}
    items = await collect(corvo.imports.iterate_rows("i_1", status="invalid"))
    assert [r["line"] for r in items] == [2, 3]
    assert rows.calls[0].request.url.params["status"] == "invalid"
    updated, error = await corvo.imports.update_row("i_1", 3, {"item": {"amount": 10}})
    assert error is None and updated == {"line": 3}
    assert json.loads(row.calls[0].request.content) == {"item": {"amount": 10}}
    assert await corvo.imports.discard("i_1") == (None, None)
    assert discard.call_count == 1
    tpl, error = await corvo.imports.download_template()
    assert (
        error is None
        and tpl is not None
        and tpl.content == b"cnpj;valor\n"
        and tpl.file_name == "modelo.csv"
    )
    err_csv, error = await corvo.imports.download_errors("i_1")
    assert error is None and err_csv is not None and err_csv.mime_type == "text/csv"
    assert template.call_count == errors.call_count == 1


@respx.mock
async def test_imports_emit_without_params_sends_no_body(corvo: Corvo) -> None:
    route = respx.post(f"{V1}/imports/i_1/emit").mock(
        return_value=httpx.Response(202, json={"data": {"id": "i_1", "status": "emitting"}})
    )
    await corvo.imports.emit("i_1")
    assert route.calls[0].request.content == b""


# --- company setup ------------------------------------------------------------------------------


@respx.mock
async def test_dps_sequence_get_and_set(corvo: Corvo) -> None:
    respx.get(f"{V1}/companies/c_1/dps-sequence").mock(
        return_value=httpx.Response(200, json={"data": {"series": "1", "lastNumber": 7}})
    )
    put = respx.put(f"{V1}/companies/c_1/dps-sequence").mock(
        return_value=httpx.Response(
            422,
            json={
                "statusCode": 422,
                "code": "DPS_NUMBER_BELOW_CURRENT",
                "message": "low",
                "requestId": "r",
            },
        )
    )
    seq, error = await corvo.dps_sequence.get("c_1")
    assert error is None and seq == {"series": "1", "lastNumber": 7}
    _, error = await corvo.dps_sequence.set("c_1", {"lastNumber": 3})
    assert error is not None and error.code == "DPS_NUMBER_BELOW_CURRENT"
    assert json.loads(put.calls[0].request.content) == {"lastNumber": 3}


@respx.mock
async def test_fiscal_and_service_tax_profiles(corvo: Corvo) -> None:
    respx.get(f"{V1}/companies/c_1/fiscal-profile").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    upsert = respx.put(f"{V1}/companies/c_1/fiscal-profile").mock(
        return_value=httpx.Response(200, json={"data": {"id": "p_1"}})
    )
    approve = respx.post(f"{V1}/companies/c_1/fiscal-profile/p_1/approve").mock(
        return_value=httpx.Response(201, json={"data": {"id": "p_1"}})
    )
    tax_list = respx.get(f"{V1}/companies/c_1/service-tax-profiles").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    tax_patch = respx.patch(f"{V1}/companies/c_1/service-tax-profiles/s_1").mock(
        return_value=httpx.Response(200, json={"data": {"id": "s_1"}})
    )
    tax_delete = respx.delete(f"{V1}/companies/c_1/service-tax-profiles/s_1").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )
    assert await corvo.fiscal_profiles.list("c_1") == ([], None)
    _, error = await corvo.fiscal_profiles.upsert("c_1", {"validFrom": "2026-01-01"})
    assert error is None and json.loads(upsert.calls[0].request.content) == {
        "validFrom": "2026-01-01"
    }
    approved, _ = await corvo.fiscal_profiles.approve("c_1", "p_1")
    assert approved == {"id": "p_1"} and approve.call_count == 1
    await corvo.service_tax_profiles.list("c_1", date="2026-11-24")
    assert tax_list.calls[0].request.url.params["date"] == "2026-11-24"
    await corvo.service_tax_profiles.update("c_1", "s_1", {})
    await corvo.service_tax_profiles.remove("c_1", "s_1")
    assert tax_patch.call_count == tax_delete.call_count == 1


# --- integrations -------------------------------------------------------------------------------


@respx.mock
async def test_integration_connections(corvo: Corvo) -> None:
    connection = {"id": "k_1", "provider": "stripe", "status": "pending"}
    create = respx.post(f"{V1}/integrations/connections").mock(
        return_value=httpx.Response(
            201, json={"data": {**connection, "secrets": {"webhookSecret": "whsec"}}}
        )
    )
    rules = respx.put(f"{V1}/integrations/connections/k_1/rules").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    events = respx.get(f"{V1}/integrations/connections/k_1/events").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    created, error = await corvo.integration_connections.create(
        {"provider": "stripe", "companyId": "c_1", "credentials": {"apiKey": "sk"}}
    )
    assert (
        error is None and created is not None and created["secrets"] == {"webhookSecret": "whsec"}
    )
    assert json.loads(create.calls[0].request.content)["credentials"] == {"apiKey": "sk"}
    await corvo.integration_connections.replace_rules("k_1", {"rules": []})
    assert json.loads(rules.calls[0].request.content) == {"rules": []}
    await corvo.integration_connections.list_events("k_1", limit=3)
    assert events.calls[0].request.url.params["limit"] == "3"


@respx.mock
async def test_integration_operations(corvo: Corvo) -> None:
    patch = respx.patch(f"{V1}/integrations/operations/o_1/customer").mock(
        return_value=httpx.Response(200, json={"data": {"id": "o_1"}})
    )
    retry = respx.post(f"{V1}/integrations/operations/o_1/retry").mock(
        return_value=httpx.Response(200, json={"data": {"status": "queued"}})
    )
    done, error = await corvo.integration_operations.complete_customer(
        "o_1", {"taxId": "52998224725", "name": "Ana"}
    )
    assert error is None and done == {"id": "o_1"}
    assert json.loads(patch.calls[0].request.content) == {"taxId": "52998224725", "name": "Ana"}
    again, error = await corvo.integration_operations.retry("o_1")
    assert error is None and again == {"status": "queued"} and retry.call_count == 1


@respx.mock
async def test_fiscal_portal_status_and_health(corvo: Corvo) -> None:
    respx.get(f"{V1}/fiscal-portal/status").mock(
        return_value=httpx.Response(200, json={"data": {"available": True}})
    )
    respx.get(f"{V1}/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok", "timestamp": "t", "uptime": 1})
    )
    status, error = await corvo.fiscal_portal.status()
    assert error is None and status == {"available": True}
    live, error = await corvo.health.live()
    assert error is None and live is not None and live["status"] == "ok"


# --- webhooks and errors ------------------------------------------------------------------------


def test_webhook_events_include_taker_rejected() -> None:
    from corvo_nfse import WEBHOOK_EVENTS

    assert "nfse.invoice.taker_rejected" in WEBHOOK_EVENTS
    assert len(WEBHOOK_EVENTS) == 12


@respx.mock
async def test_error_carries_retry_after_and_rate_limit_headers(corvo: Corvo) -> None:
    respx.get(f"{V1}/customers").mock(
        return_value=httpx.Response(
            429,
            json={
                "statusCode": 429,
                "code": "ERROR_RATE_LIMITED",
                "message": "slow down",
                "requestId": "r9",
            },
            headers={
                "Retry-After": "7",
                "X-RateLimit-Limit": "120",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1795000000",
            },
        )
    )
    data, error = await corvo.customers.search()
    assert data is None and error is not None
    assert error.status == 429 and error.retry_after == 7
    assert error.rate_limit is not None
    assert (error.rate_limit.limit, error.rate_limit.remaining, error.rate_limit.reset) == (
        120,
        0,
        1795000000,
    )


@respx.mock
async def test_error_details_can_be_an_object(corvo: Corvo) -> None:
    respx.get(f"{V1}/customers").mock(
        return_value=httpx.Response(
            422,
            json={
                "statusCode": 422,
                "code": "ERROR_VALIDATION",
                "message": "bad",
                "details": {"field": "x"},
                "requestId": "r",
            },
        )
    )
    _, error = await corvo.customers.search()
    assert error is not None and error.details == [{"field": "x"}]


@respx.mock
async def test_path_segments_are_escaped(corvo: Corvo) -> None:
    route = respx.get(url__regex=r".*/customers/.*").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    await corvo.customers.get("a/b ?x")
    assert route.calls[0].request.url.raw_path.decode().endswith("/customers/a%2Fb%20%3Fx")
