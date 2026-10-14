"""Certificate wire types."""

from __future__ import annotations

from typing import TypedDict


class Certificate(TypedDict):
    id: str
    companyId: str
    serialNumber: str
    issuer: str
    subject: str
    fingerprint: str
    validFrom: str
    validUntil: str
    status: str
    createdAt: str


# Input for certificates.upload(): raw .p12 bytes, optional file name, password.
# Not a wire type — the SDK builds the multipart form itself.
