"""Webhook wire types and the 12 event names you can subscribe to.

``webhook.test`` is only sent by ``webhooks.test()`` and cannot be subscribed.

A webhook created with an API key is tied to that key's environment (``environment`` is ``test``
or ``live``) and only receives its events: a ``corvo_test_`` key cannot reach live webhooks.
Destinations that resolve to private, loopback, link-local, CGNAT, benchmarking, multicast or
NAT64/6to4 addresses are refused when the webhook is registered and when it is delivered.
"""

from __future__ import annotations

from typing import List, Literal, TypedDict

from . import models

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
    "nfse.invoice.taker_rejected",
)

WebhookEvent = models.WebhookEventType

Environment = Literal["test", "live"]

Webhook = models.Webhook
WebhookWithSecret = models.WebhookWithSecret
WebhookCreateParams = models.CreateWebhookConfig
WebhookDelivery = models.WebhookDelivery
WebhookDeliveryStats = models.WebhookStats
WebhookTestResult = models.WebhookTestResult
WebhookRetried = models.WebhookRetried


class WebhookListParams(TypedDict, total=False):
    limit: int
    cursor: str


class WebhookDeliveryListParams(TypedDict, total=False):
    hours: int
    environment: Environment
    limit: int
    cursor: str


WebhookEvents = List[models.WebhookEventType]
