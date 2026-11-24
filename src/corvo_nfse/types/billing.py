"""Billing wire types.

``BillingPlanResponse`` keeps the server's snake_case keys (``GET /billing/plan`` is one of the
routes that answers in snake_case): pass-through, no re-casing.
"""

from __future__ import annotations

from . import models

BillingPlanSection = models.BillingPlanPlan
BillingSubscriptionSection = models.BillingPlanSubscription
BillingPixSubscription = models.BillingPlanSubscriptionPix_subscription
BillingUsageSection = models.BillingPlanUsage
BillingPlanResponse = models.BillingPlan
QuotaStatus = models.QuotaStatus
