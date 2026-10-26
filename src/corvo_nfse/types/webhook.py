"""Webhook wire types and the 11 event names you can subscribe to.

``webhook.test`` is only sent by ``webhooks.test()`` and cannot be subscribed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

WEBHOOK_EVENTS = (
    "nfse.invoice.authorized",
    "nfse.invoice.rejected",
    "nfse.invoice.failed",
    "nfse.invoice.reconciliation_required",
    "nfse.invoice.manual_review",
    "nfse.invoice.documents_ready",
    "nfse.invoice.email_sent",
    "nfse.invoice.email_failed",
    "nfse.invoice.fiscal_discrepancy",
    "nfse.invoice.cancelled",
    "nfse.invoice.cancellation_rejected",
)

WebhookEvent = str

Environment = Literal["test", "live"]


class Webhook(TypedDict):
    id: str
    url: str
    events: List[str]
    active: bool
    createdAt: str
    updatedAt: str


class WebhookWithSecret(Webhook):
    secret: str


class WebhookCreateParams(TypedDict):
    url: str
    events: List[str]


class WebhookListParams(TypedDict, total=False):
    limit: int
    cursor: str


class WebhookDelivery(TypedDict):
    id: str
    tenantId: str
    webhookConfigId: str
    eventType: str
    environment: Environment
    url: str
    payload: Dict[str, Any]
    statusCode: Optional[int]
    responseBody: Any
    errorMessage: Optional[str]
    status: str
    durationMs: Optional[int]
    retryCount: int
    nextRetryAt: Optional[str]
    lastError: Optional[str]
    createdAt: str


class WebhookDeliveryStats(TypedDict):
    total: int
    sent: int
    failed: int
    pending: int
    delayed: int


class WebhookDeliveryListParams(TypedDict, total=False):
    hours: int
    environment: Environment
    limit: int
    cursor: str
