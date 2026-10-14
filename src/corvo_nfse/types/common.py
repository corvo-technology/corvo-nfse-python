"""Shared envelope shapes: pagination."""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict


class Pagination(TypedDict):
    limit: int
    hasMore: bool
    nextCursor: Optional[str]


class Paginated(TypedDict):
    """List envelope: ``{ data: [...], pagination: {...} }`` (wire names)."""

    data: List[Any]
    pagination: Pagination
