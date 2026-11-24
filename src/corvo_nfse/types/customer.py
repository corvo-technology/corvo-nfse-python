"""Customer, CNPJ lookup, schedule, import and integration wire types."""

from __future__ import annotations

from typing import TypedDict

from . import models

SavedCustomer = models.SavedCustomer
CustomerUpdateParams = models.UpdateCustomer
CnpjProfile = models.CnpjProfile

Schedule = models.Schedule
ScheduleRun = models.ScheduleRun
ScheduleUpdateParams = models.UpdateSchedule

ImportJob = models.ImportJob
ImportStart = models.ImportStart
ImportRow = models.ImportRow
ImportCounters = models.ImportCounters


class ImportEmitParams(TypedDict, total=False):
    """Optional body of ``imports.emit``; the contract documents no body schema."""

    # E-mail each issued invoice to its customer.
    sendEmail: bool


ImportRowUpdateParams = models.UpdateImportRow

IntegrationProvider = models.IntegrationProvider
IntegrationConnection = models.IntegrationConnection
IntegrationConnectionCreated = models.IntegrationConnectionCreated
IntegrationConnectionCreateParams = models.CreateConnection
IntegrationCredentialsUpdateParams = models.UpdateCredentials
IntegrationRule = models.IntegrationRule
IntegrationRuleInput = models.IntegrationRuleInput
IntegrationRulesParams = models.PutRules
IntegrationEvent = models.IntegrationEvent
IntegrationOperation = models.IntegrationOperation
IntegrationOperationRetry = models.IntegrationOperationRetry
IntegrationCompleteCustomerParams = models.CompleteCustomer
