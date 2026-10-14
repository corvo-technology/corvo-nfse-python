"""Billing wire types.

Note: ``BillingPlanResponse`` keeps the server's snake_case keys (the one
place the API mixes casing) — pass-through, no re-casing.
"""

from __future__ import annotations

from typing import Optional, TypedDict


class BillingPlanSection(TypedDict):
    slug: str
    name: str
    monthly_allowance: int
    daily_limit: Optional[int]
    max_active_companies: int
    monthly_price_cents: int


class BillingSubscriptionSection(TypedDict):
    status: str
    paid_until: Optional[str]
    cancel_at_period_end: bool
    scheduled_plan: Optional[str]
    blocked: bool


class BillingUsageSection(TypedDict):
    overage_units: int
    overage_amount_cents: int
    hard_limit: Optional[int]
    credits_used: int
    credits_reserved: int
    credits_remaining: int
    monthly_allowance: int
    daily_usage: int
    daily_limit: Optional[int]
    active_companies: int
    max_active_companies: int
    period_start: Optional[str]
    period_end: Optional[str]


class BillingPlanResponse(TypedDict):
    plan: BillingPlanSection
    subscription: BillingSubscriptionSection
    usage: BillingUsageSection


class QuotaStatus(TypedDict):
    canEmit: bool
    creditsRemaining: float
    creditsUsed: float
    creditsReserved: float
    monthlyAllowance: float
    dailyUsage: float
    dailyLimit: Optional[int]
    activeCompanies: int
    maxActiveCompanies: int
    periodStart: Optional[str]
    periodEnd: Optional[str]
