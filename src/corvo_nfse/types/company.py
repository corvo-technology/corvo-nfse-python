"""Company wire types (aliases of the generated models: names mirror the API exactly)."""

from __future__ import annotations

from typing import Literal, TypedDict

from . import models

# Corvo serves only these two regimes; any other value returns 422 ERROR_TAX_REGIME_NOT_SUPPORTED.
TaxRegime = Literal["MEI", "Simples Nacional"]

CompanyAddressInput = models.CompanyAddress
CompanyCreateParams = models.CreateCompany
CompanyUpdateParams = models.UpdateCompany
Company = models.Company
MunicipalityAgreement = models.MunicipalityAgreement
DpsSequence = models.DpsSequence
DpsSequenceSetParams = models.SetDpsSequence
FiscalProfile = models.FiscalProfile
FiscalProfileUpsertParams = models.UpsertFiscalProfile
ServiceTaxProfile = models.ServiceTaxProfile
ServiceTaxProfileCreateParams = models.CreateServiceTaxProfile
ServiceTaxProfileUpdateParams = models.UpdateServiceTaxProfile
ServiceFavorite = models.ServiceFavorite
ServiceFavoriteCreateParams = models.CreateServiceFavorite
AccountantSettings = models.AccountantSettings
AccountantSettingsUpdate = models.AccountantSettingsUpdate
AccountantSettingsUpdateParams = models.UpdateAccountantPackage
AccountantSend = models.AccountantSend
AccountantSendResult = models.AccountantSendResult
AccountantSendParams = models.SendAccountantPackage


class CompanyListParams(TypedDict, total=False):
    limit: int
    cursor: str
