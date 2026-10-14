"""Company wire types (field names mirror the API response exactly)."""

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

TaxRegime = Literal["MEI", "Simples Nacional", "Lucro Presumido", "Lucro Real"]


class CompanyAddressInput(TypedDict, total=False):
    street: str
    number: str
    complement: str
    district: str
    city: str
    state: str
    zip: str


class _CompanyCreateRequired(TypedDict):
    legalName: str
    taxId: str
    taxRegime: TaxRegime


class CompanyCreateParams(_CompanyCreateRequired, total=False):
    tradeName: str
    municipalReg: str
    municipalityCode: str
    simpleNational: bool
    specialRegime: str
    address: CompanyAddressInput


class CompanyUpdateParams(TypedDict, total=False):
    legalName: str
    tradeName: str
    municipalReg: Optional[str]
    municipalityCode: str
    taxRegime: TaxRegime
    simpleNational: bool
    specialRegime: str
    address: Optional[CompanyAddressInput]


class Company(TypedDict):
    id: str
    tenantId: str
    legalName: str
    tradeName: Optional[str]
    taxId: str
    municipalReg: Optional[str]
    municipalityCode: Optional[str]
    taxRegime: TaxRegime
    simpleNational: bool
    specialRegime: Optional[str]
    addressStreet: Optional[str]
    addressNumber: Optional[str]
    addressComplement: Optional[str]
    addressDistrict: Optional[str]
    addressCity: str
    addressState: str
    addressZip: str
    fiscalSchemaVersion: str
    environment: Literal["test", "live"]
    status: str
    createdAt: str
    updatedAt: str
    deletedAt: Optional[str]
    setupGaps: List[str]


class CompanyListParams(TypedDict, total=False):
    limit: int
    cursor: str
