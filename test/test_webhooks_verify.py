"""HMAC signature verification tests, including the shared known vector."""

from __future__ import annotations

from corvo_nfse import WEBHOOK_EVENTS, CorvoWebhooks

BODY = b'{"type":"nfse.invoice.authorized","data":{"id":"inv_1"}}'
SECRET = "whsec_test_123"
EXPECTED = "sha256=8f9bd040d8f717b19618ab3395ddfa4b8c176b8dc863195227b88dd85426bbbc"


def test_known_vector() -> None:
    assert CorvoWebhooks.verify_signature(BODY, EXPECTED, SECRET) is True


def test_known_vector_str_body() -> None:
    assert CorvoWebhooks.verify_signature(BODY.decode("utf-8"), EXPECTED, SECRET) is True


def test_header_whitespace_tolerated() -> None:
    assert CorvoWebhooks.verify_signature(BODY, f"  {EXPECTED} ", SECRET) is True


def test_tampered_body() -> None:
    tampered = BODY.replace(b"inv_1", b"inv_2")
    assert CorvoWebhooks.verify_signature(tampered, EXPECTED, SECRET) is False


def test_wrong_secret() -> None:
    assert CorvoWebhooks.verify_signature(BODY, EXPECTED, "whsec_wrong") is False


def test_malformed_header() -> None:
    assert CorvoWebhooks.verify_signature(BODY, "sha256=zz", SECRET) is False
    assert CorvoWebhooks.verify_signature(BODY, "md5=abc", SECRET) is False
    assert CorvoWebhooks.verify_signature(BODY, EXPECTED.upper(), SECRET) is False


def test_missing_or_empty_inputs() -> None:
    assert CorvoWebhooks.verify_signature(BODY, None, SECRET) is False
    assert CorvoWebhooks.verify_signature(BODY, "", SECRET) is False
    assert CorvoWebhooks.verify_signature(BODY, EXPECTED, "") is False
    assert CorvoWebhooks.verify_signature(BODY, EXPECTED, None) is False  # type: ignore[arg-type]


def test_webhook_events_constant() -> None:
    assert len(WEBHOOK_EVENTS) == 11
    assert "nfse.invoice.authorized" in WEBHOOK_EVENTS
    assert "nfse.invoice.fiscal_discrepancy" in WEBHOOK_EVENTS
    assert "nfse.invoice.cancelled" in WEBHOOK_EVENTS
    assert "nfse.invoice.cancellation_rejected" in WEBHOOK_EVENTS
    assert "webhook.test" not in WEBHOOK_EVENTS
