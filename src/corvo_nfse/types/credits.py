"""Credit wire types."""

from __future__ import annotations

from typing import Literal, TypedDict

from . import models

CreditBalance = models.CreditBalance
#: ``slug`` is an open string: ``free``, ``self-hosted``, ``solo``, ``equipe``, ``empresa``, ``escala``.
CreditPlan = models.Plan
CreditTransaction = models.CreditTransaction
CreditPurchasePreview = models.PurchasePreview
#: Public catalog entry (``GET /plans``, ``GET /plans/{slug}``): prices in centavos.
PlanPrice = models.PlanPrice


class CreditHistoryParams(TypedDict, total=False):
    limit: int
    cursor: str


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
