"""Credit wire types."""

from __future__ import annotations

from typing import Literal, TypedDict

from . import models

CreditBalance = models.CreditBalance
#: ``slug`` is an open string: ``free``, ``self-hosted``, ``solo``, ``equipe``, ``empresa``, ``escala``.
CreditPlan = models.Plan
CreditTransaction = models.CreditTransaction
CreditPurchasePreview = models.PurchasePreview


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
