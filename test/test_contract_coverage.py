"""Every operation of the vendored contract (spec/openapi.json) must have an SDK method.

The table below maps each ``operationId`` to a call of the SDK. For each case the test checks the
HTTP method, the path and that only query parameters the contract declares were sent, so a
route that moved, a method that was forgotten or a new operation in a refreshed spec fails here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Tuple

import httpx
import respx
from conftest import API_KEY, BASE_URL

from corvo_nfse import Corvo

SPEC = json.loads((Path(__file__).resolve().parent.parent / "spec" / "openapi.json").read_text())

Call = Callable[[Corvo], Awaitable[Any]]

INVOICE: Dict[str, Any] = {
    "companyTaxId": "11222333000181",
    "service": {"description": "Consultoria"},
    "amount": 100,
    "competenceDate": "2026-11-24",
}

# operationId -> (call, path parameter values used by the call)
CASES: Dict[str, Tuple[Call, Dict[str, str]]] = {
    "billing_getPlan": (lambda c: c.billing.plan(), {}),
    "billing_getUsage": (lambda c: c.billing.usage(), {}),
    "cnpj_lookup": (lambda c: c.cnpj.lookup("11222333000181"), {"cnpj": "11222333000181"}),
    "companies_list": (lambda c: c.companies.list(limit=1, cursor="x"), {}),
    "companies_create": (
        lambda c: c.companies.create(
            {"legalName": "A", "taxId": "1", "taxRegime": "MEI", "municipalityCode": "3550308"}
        ),
        {},
    ),
    "accountantPackage_get": (lambda c: c.accountant_package.get("c_1"), {"companyId": "c_1"}),
    "accountantPackage_update": (
        lambda c: c.accountant_package.update("c_1", {"accountantEmail": "a@b.co"}),
        {"companyId": "c_1"},
    ),
    "accountantPackage_send": (
        lambda c: c.accountant_package.send("c_1", "2026-10"),
        {"companyId": "c_1"},
    ),
    "accountantPackage_listSends": (
        lambda c: c.accountant_package.list_sends("c_1"),
        {"companyId": "c_1"},
    ),
    "certificates_list": (lambda c: c.certificates.list("c_1"), {"companyId": "c_1"}),
    "certificates_upload": (
        lambda c: c.certificates.upload("c_1", b"p12", "pw"),
        {"companyId": "c_1"},
    ),
    "certificates_revoke": (
        lambda c: c.certificates.remove("c_1", "cert_1"),
        {"companyId": "c_1", "certId": "cert_1"},
    ),
    "invoicePackage_download": (
        lambda c: c.invoice_package.download("c_1", "2026-10", include="xml"),
        {"companyId": "c_1"},
    ),
    "invoicePackage_summary": (
        lambda c: c.invoice_package.summary("c_1", "2026-10"),
        {"companyId": "c_1"},
    ),
    "serviceFavorites_list": (lambda c: c.service_favorites.list("c_1"), {"companyId": "c_1"}),
    "serviceFavorites_create": (
        lambda c: c.service_favorites.create(
            "c_1", {"label": "x", "description": "y", "serviceCode": "010101"}
        ),
        {"companyId": "c_1"},
    ),
    "serviceFavorites_delete": (
        lambda c: c.service_favorites.remove("c_1", "fav_1"),
        {"companyId": "c_1", "favoriteId": "fav_1"},
    ),
    "companies_delete": (lambda c: c.companies.remove("c_1"), {"id": "c_1"}),
    "companies_get": (lambda c: c.companies.get("c_1"), {"id": "c_1"}),
    "companies_update": (lambda c: c.companies.update("c_1", {"tradeName": "x"}), {"id": "c_1"}),
    "dpsSequence_get": (lambda c: c.dps_sequence.get("c_1"), {"id": "c_1"}),
    "dpsSequence_set": (lambda c: c.dps_sequence.set("c_1", {"lastNumber": 10}), {"id": "c_1"}),
    "fiscalProfiles_list": (lambda c: c.fiscal_profiles.list("c_1"), {"id": "c_1"}),
    "fiscalProfiles_upsert": (
        lambda c: c.fiscal_profiles.upsert("c_1", {}),
        {"id": "c_1"},
    ),
    "fiscalProfiles_approve": (
        lambda c: c.fiscal_profiles.approve("c_1", "p_1"),
        {"id": "c_1", "profileId": "p_1"},
    ),
    "serviceTaxProfiles_list": (
        lambda c: c.service_tax_profiles.list("c_1", date="2026-11-24"),
        {"id": "c_1"},
    ),
    "serviceTaxProfiles_create": (
        lambda c: c.service_tax_profiles.create("c_1", {}),
        {"id": "c_1"},
    ),
    "serviceTaxProfiles_delete": (
        lambda c: c.service_tax_profiles.remove("c_1", "s_1"),
        {"id": "c_1", "serviceId": "s_1"},
    ),
    "serviceTaxProfiles_update": (
        lambda c: c.service_tax_profiles.update("c_1", "s_1", {}),
        {"id": "c_1", "serviceId": "s_1"},
    ),
    "serviceTaxProfiles_approve": (
        lambda c: c.service_tax_profiles.approve("c_1", "s_1"),
        {"id": "c_1", "serviceId": "s_1"},
    ),
    "credits_getBalance": (lambda c: c.credits.balance(), {}),
    "credits_listHistory": (lambda c: c.credits.history(limit=1), {}),
    "credits_listPlans": (lambda c: c.credits.plans(limit=1), {}),
    "credits_previewPurchase": (lambda c: c.credits.preview_purchase(5), {}),
    "customers_search": (lambda c: c.customers.search(search="ana", limit=5, cursor="0"), {}),
    "customers_delete": (lambda c: c.customers.remove("52998224725"), {"taxId": "52998224725"}),
    "customers_get": (lambda c: c.customers.get("52998224725"), {"taxId": "52998224725"}),
    "customers_update": (
        lambda c: c.customers.update("52998224725", {"name": "Ana"}),
        {"taxId": "52998224725"},
    ),
    "fiscalPortal_status": (lambda c: c.fiscal_portal.status(), {}),
    "health_live": (lambda c: c.health.live(), {}),
    "imports_list": (lambda c: c.imports.list(limit=5), {}),
    "imports_start": (lambda c: c.imports.start(b"a;b", company_id="c_1"), {}),
    "imports_discard": (lambda c: c.imports.discard("i_1"), {"id": "i_1"}),
    "imports_get": (lambda c: c.imports.get("i_1"), {"id": "i_1"}),
    "imports_emit": (lambda c: c.imports.emit("i_1", {"sendEmail": True}), {"id": "i_1"}),
    "imports_downloadErrors": (lambda c: c.imports.download_errors("i_1"), {"id": "i_1"}),
    "imports_listRows": (
        lambda c: c.imports.list_rows("i_1", status="invalid", limit=10, cursor="5"),
        {"id": "i_1"},
    ),
    "imports_updateRow": (
        lambda c: c.imports.update_row("i_1", 3, {}),
        {"id": "i_1", "line": "3"},
    ),
    "imports_downloadTemplate": (lambda c: c.imports.download_template(), {}),
    "integrationConnections_list": (lambda c: c.integration_connections.list(), {}),
    "integrationConnections_create": (
        lambda c: c.integration_connections.create(
            {"provider": "stripe", "companyId": "c_1", "credentials": {"apiKey": "k"}}
        ),
        {},
    ),
    "integrationConnections_get": (lambda c: c.integration_connections.get("k_1"), {"id": "k_1"}),
    "integrationConnections_activate": (
        lambda c: c.integration_connections.activate("k_1"),
        {"id": "k_1"},
    ),
    "integrationConnections_updateCredentials": (
        lambda c: c.integration_connections.update_credentials(
            "k_1", {"credentials": {"apiKey": "k"}}
        ),
        {"id": "k_1"},
    ),
    "integrationConnections_disconnect": (
        lambda c: c.integration_connections.disconnect("k_1"),
        {"id": "k_1"},
    ),
    "integrationConnections_listEvents": (
        lambda c: c.integration_connections.list_events("k_1", limit=5),
        {"id": "k_1"},
    ),
    "integrationConnections_listOperations": (
        lambda c: c.integration_connections.list_operations("k_1", limit=5),
        {"id": "k_1"},
    ),
    "integrationConnections_pause": (
        lambda c: c.integration_connections.pause("k_1"),
        {"id": "k_1"},
    ),
    "integrationConnections_listRules": (
        lambda c: c.integration_connections.list_rules("k_1"),
        {"id": "k_1"},
    ),
    "integrationConnections_replaceRules": (
        lambda c: c.integration_connections.replace_rules("k_1", {"rules": []}),
        {"id": "k_1"},
    ),
    "integrationConnections_validate": (
        lambda c: c.integration_connections.validate("k_1"),
        {"id": "k_1"},
    ),
    "integrationOperations_completeCustomer": (
        lambda c: c.integration_operations.complete_customer("o_1", {"taxId": "1"}),
        {"id": "o_1"},
    ),
    "integrationOperations_retry": (
        lambda c: c.integration_operations.retry("o_1"),
        {"id": "o_1"},
    ),
    "integrations_listProviders": (lambda c: c.integrations.list_providers(), {}),
    "invoices_list": (
        lambda c: c.invoices.list(
            companyId="c_1",
            status="authorized",
            from_="2026-11-01",
            to="2026-11-30",
            externalId="e",
            customerTaxId="52998224725",
            limit=1,
            cursor="x",
        ),
        {},
    ),
    "invoices_create": (lambda c: c.invoices.create(INVOICE, idempotency_key="k1"), {}),
    "invoices_get": (lambda c: c.invoices.get("inv_1"), {"id": "inv_1"}),
    "invoices_cancel": (
        lambda c: c.invoices.cancel("inv_1", {"reason": "other", "description": "x" * 20}),
        {"id": "inv_1"},
    ),
    "invoices_createDownloadUrl": (
        lambda c: c.invoices.download_url("inv_1", "xml"),
        {"id": "inv_1"},
    ),
    "invoices_sendEmail": (
        lambda c: c.invoices.send_email("inv_1", email="a@b.co", idempotency_key="k1"),
        {"id": "inv_1"},
    ),
    "invoices_listEvents": (lambda c: c.invoices.events("inv_1", limit=1), {"id": "inv_1"}),
    "invoices_downloadPdf": (lambda c: c.invoices.pdf("inv_1"), {"id": "inv_1"}),
    "invoices_substitute": (
        lambda c: c.invoices.substitute("inv_1", {"description": "x" * 15}, idempotency_key="k1"),
        {"id": "inv_1"},
    ),
    "invoices_downloadXml": (lambda c: c.invoices.xml("inv_1"), {"id": "inv_1"}),
    "invoices_createBatch": (lambda c: c.invoices.create_batch([INVOICE]), {}),
    "invoices_calculate": (lambda c: c.invoices.calculate(INVOICE), {}),
    "invoices_overview": (lambda c: c.invoices.overview(period="30d"), {}),
    "invoices_review": (
        lambda c: c.invoices.review({"action": "retry", "invoiceIds": ["a"]}),
        {},
    ),
    "schedules_list": (
        lambda c: c.schedules.list(status="active", company_id="c_1", limit=1, cursor="0"),
        {},
    ),
    "schedules_get": (lambda c: c.schedules.get("s_1"), {"id": "s_1"}),
    "schedules_update": (
        lambda c: c.schedules.update("s_1", {"endsOn": "2027-01-01"}),
        {"id": "s_1"},
    ),
    "schedules_cancel": (lambda c: c.schedules.cancel("s_1"), {"id": "s_1"}),
    "schedules_pause": (lambda c: c.schedules.pause("s_1"), {"id": "s_1"}),
    "schedules_resume": (lambda c: c.schedules.resume("s_1"), {"id": "s_1"}),
    "schedules_listRuns": (lambda c: c.schedules.list_runs("s_1", limit=1), {"id": "s_1"}),
    "webhooks_list": (lambda c: c.webhooks.list(limit=1), {}),
    "webhooks_create": (
        lambda c: c.webhooks.create(
            {"url": "https://x.example/h", "events": ["nfse.invoice.authorized"]}
        ),
        {},
    ),
    "webhooks_delete": (lambda c: c.webhooks.remove("w_1"), {"id": "w_1"}),
    "webhooks_test": (lambda c: c.webhooks.test("w_1"), {"id": "w_1"}),
    "webhookDeliveries_list": (
        lambda c: c.webhooks.deliveries.list(hours=2, environment="test", limit=1),
        {},
    ),
    "webhookDeliveries_retry": (lambda c: c.webhooks.deliveries.retry("d_1"), {"id": "d_1"}),
    "webhookDeliveries_stats": (
        lambda c: c.webhooks.deliveries.stats(hours=2, environment="live"),
        {},
    ),
}


def _operations() -> Dict[str, Tuple[str, str, List[str], bool]]:
    """operationId -> (METHOD, path template, declared query names, takes Idempotency-Key)."""
    out: Dict[str, Tuple[str, str, List[str], bool]] = {}
    for path, item in SPEC["paths"].items():
        for method, op in item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            queries: List[str] = []
            idempotent = False
            for raw in op.get("parameters", []):
                param = raw
                if "$ref" in raw:
                    param = SPEC
                    for part in raw["$ref"][2:].split("/"):
                        param = param[part]
                if param["in"] == "query":
                    queries.append(param["name"])
                if param["in"] == "header" and param["name"] == "Idempotency-Key":
                    idempotent = True
            out[op["operationId"]] = (method.upper(), path, queries, idempotent)
    return out


OPERATIONS = _operations()


def test_contract_is_the_expected_version() -> None:
    assert SPEC["info"]["version"] == "0.3.0"
    assert len(OPERATIONS) == 92


def test_every_operation_has_a_case_and_no_case_is_stale() -> None:
    missing = sorted(set(OPERATIONS) - set(CASES))
    stale = sorted(set(CASES) - set(OPERATIONS))
    assert not missing, f"operations of the contract without an SDK case: {missing}"
    assert not stale, f"cases whose operation left the contract: {stale}"


@respx.mock
async def test_each_operation_hits_the_contract_route() -> None:
    route = respx.route().mock(return_value=httpx.Response(200, json={"data": None}))
    async with Corvo(api_key=API_KEY, base_url=BASE_URL) as corvo:
        for operation_id, (call, params) in CASES.items():
            method, template, queries, idempotent = OPERATIONS[operation_id]
            before = len(route.calls)
            await call(corvo)
            assert len(route.calls) == before + 1, operation_id
            request = route.calls[before].request
            expected = "/v1" + template
            for name, value in params.items():
                expected = expected.replace("{" + name + "}", value)
            assert request.method == method, operation_id
            assert request.url.path == expected, operation_id
            assert request.headers["x-api-key"] == API_KEY, operation_id
            sent = set(request.url.params.keys())
            assert sent <= set(queries), f"{operation_id}: undeclared query {sent - set(queries)}"
            if idempotent:
                assert request.headers.get("Idempotency-Key") == "k1", operation_id
