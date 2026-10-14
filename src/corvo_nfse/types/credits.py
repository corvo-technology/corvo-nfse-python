"""Credit wire types."""

from __future__ import annotations

from typing import Literal, Optional, TypedDict


class CreditBalance(TypedDict):
    tenantId: str
    balance: float
    overageUnits: int
    overageAmountCents: int
    hardLimit: Optional[int]


class CreditPlan(TypedDict):
    id: str
    slug: str
    name: str
    description: str
    dailyLimit: int
    maxActiveCompanies: int
    creditUnitPriceCents: int
    throughputRps: float
    includesWebhooks: bool
    includesXmlDownload: bool
    includesPdfDownload: bool
    includesApiKeys: bool
    supportTier: str
    active: bool
    createdAt: str
    updatedAt: str


class CreditTransaction(TypedDict):
    id: str
    type: str
    amount: float
    creditDelta: float
    balanceAfter: float
    environment: Literal["test", "live"]
    source: str
    referenceType: Optional[str]
    referenceId: Optional[str]
    createdAt: str


class CreditHistoryParams(TypedDict, total=False):
    limit: int
    cursor: str
