"""Error type and result-style tuple alias for the Corvo NFS-e API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypeVar

T = TypeVar("T")

#: Every API call resolves to ``(data, error)`` where exactly one is ``None``.
#: API, network, and timeout failures are values, not exceptions. The single
#: documented exception is the ``iterate()`` async generators, which raise the
#: error on first-page failure because they have no ``yield`` slot for it.
Result = Tuple[Optional[T], Optional["CorvoApiError"]]


@dataclass
class CorvoApiError(Exception):
    """Typed error carrying the server's stable ``code`` and HTTP context.

    Network and timeout failures use ``status=0`` and ``code`` of
    ``"network_error"`` or ``"timeout"``.
    """

    status: int
    code: str
    message: str
    details: List[Dict[str, Any]] = field(default_factory=list)
    request_id: Optional[str] = None
    retry_after: Optional[int] = None

    def __post_init__(self) -> None:
        # Make str(error) / print(error) show the message, not the repr.
        Exception.__init__(self, self.message)

    def __str__(self) -> str:
        return self.message


#: Field-level validation detail entry: ``{ field, code, message }``.
CorvoErrorDetail = Dict[str, Any]
