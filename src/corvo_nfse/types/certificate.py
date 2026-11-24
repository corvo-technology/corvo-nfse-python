"""Certificate wire types."""

from __future__ import annotations

from . import models

Certificate = models.Certificate

# Input for certificates.upload(): raw .p12 bytes, optional file name, password.
# Not a wire type: the SDK builds the multipart form itself.
