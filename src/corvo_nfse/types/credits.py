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
    slug: Literal["free", "developer", "growth", "scale", "volume"]
    name: str
    description: str
    monthlyCreditAllowance: int
    dailyLimit: Optional[int]
    maxActiveCompanies: int
    creditUnitPriceCents: int
    throughputRps: float
    includesWebhooks: bool
    includesXmlDownload: bool
    includesPdfDownload: bool
    includesApiKeys: bool
    supportTier: Literal["community", "email", "priority"]
    active: bool
    createdAt: str
    updatedAt: str


class _CreditTransactionRequired(TypedDict):
    id: str
    tenantId: str
    type: str
    amount: float  # in credits, not BRL
    createdAt: str


class CreditTransaction(_CreditTransactionRequired, total=False):
    description: str
    source: Literal["subscription", "avulso", "bonus"]
    amountBrlCents: int
    unitPriceCentsApplied: int
    planIdSnapshot: str
    reservedInvoiceId: str
    periodId: str
    isReservation: bool
    relatedTransactionId: str


class CreditHistoryParams(TypedDict, total=False):
    limit: int
    cursor: str


class PlanQuote(TypedDict):
    """Public catalog entry (``GET /plans``): prices in centavos, monthly cycle only."""

    slug: str
    name: str
    monthlyAllowance: int
    basePriceCents: int
    perCreditOverageCents: int
    monthlyTotalCents: int
    currency: Literal["BRL"]


class PlanRecommendation(TypedDict):
    """Plan recommended for a monthly volume (``GET /plans/quote``). Note the snake_case keys."""

    volume: int
    recommended_plan: str
    plan_name: str
    monthly_allowance: int
    overage_credits: int
    overage_cost_cents: int
    base_price_cents: int
    total_estimated_cents: int
    currency: Literal["BRL"]
    billing_cycle: Literal["monthly"]
