"""Webhook signature verification (HMAC-SHA256, timing-safe)."""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Optional, Union

_SIGNATURE_RE = re.compile(r"^sha256=([0-9a-f]{64})$")


class CorvoWebhooks:
    """Static helpers for consuming Corvo webhooks."""

    @staticmethod
    def verify_signature(
        raw_body: Union[str, bytes],
        signature_header: Optional[str],
        secret: str,
    ) -> bool:
        """Verify an ``X-Corbo-Signature: sha256=<hex>`` header.

        Pass the raw request bytes — re-serialized JSON will not match the
        HMAC. Comparison is constant-time via :func:`hmac.compare_digest`.
        """
        if not isinstance(signature_header, str) or not isinstance(secret, str) or not secret:
            return False
        match = _SIGNATURE_RE.match(signature_header.strip())
        if match is None:
            return False
        body = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
        expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(match.group(1), expected)
