"""Company wire types (field names mirror the API response exactly)."""

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

# Corvo serves only these two regimes; any other value returns 422 ERROR_TAX_REGIME_NOT_SUPPORTED.
TaxRegime = Literal["MEI", "Simples Nacional"]


class CompanyAddressInput(TypedDict, total=False):
    """All optional. ``state`` is the two-letter UF; ``zip`` has 8 digits."""

    street: str
    number: str
    complement: str
    district: str
    city: str
    state: str
    zip: str


class _CompanyCreateRequired(TypedDict):
    legalName: str
    taxId: str  # CNPJ
    taxRegime: TaxRegime
    municipalityCode: str  # IBGE code of the company's city, 7 digits


class CompanyCreateParams(_CompanyCreateRequired, total=False):
    tradeName: str
    municipalReg: str  # stored; only sent on the invoice when sendMunicipalReg is True
    sendMunicipalReg: bool  # default False: only if the city registered the company nationally
    defaultServiceCode: str  # national service code (6 digits) used when an invoice omits service.code
    simpleNational: bool
    specialRegime: str
    simplesRate: str  # required for Simples Nacional, ignored for MEI: effective DAS rate (%), e.g. "6.54"
    simplesIssRate: str  # Simples Nacional only: effective ISS rate (%) of the bracket (1.80 to 5.00)
    address: CompanyAddressInput


class CompanyUpdateParams(TypedDict, total=False):
    legalName: str
    tradeName: str
    municipalReg: Optional[str]
    sendMunicipalReg: bool
    municipalityCode: str
    defaultServiceCode: Optional[str]
    taxRegime: TaxRegime
    simpleNational: bool
    specialRegime: str
    simplesRate: str  # omit to keep the current value; ignored for MEI
    simplesIssRate: Optional[str]  # None removes it
    address: Optional[CompanyAddressInput]


class _CompanyRequired(TypedDict):
    id: str
    tenantId: str
    legalName: str
    taxId: str
    taxRegime: Optional[TaxRegime]
    simpleNational: bool
    specialRegime: Optional[str]
    fiscalSchemaVersion: str
    environment: Literal["test", "live"]
    status: Literal["pending_setup", "ready", "blocked"]
    createdAt: str
    updatedAt: str
    setupGaps: List[str]  # pending setup: "municipality_code", "certificate"


class Company(_CompanyRequired, total=False):
    """Optional fields are absent from the JSON when they have no value."""

    tradeName: str
    municipalReg: str
    sendMunicipalReg: bool
    municipalityCode: str
    defaultServiceCode: str
    addressStreet: str
    addressNumber: str
    addressComplement: str
    addressDistrict: str
    addressCity: str
    addressState: str
    addressZip: str
    deletedAt: str


class CompanyListParams(TypedDict, total=False):
    limit: int
    cursor: str
