"""HTTP transport: envelope unwrap, error mapping, pagination, downloads.

Every resource routes through :class:`Transport`. Two envelope helpers live
here — ``unwrap()`` (modes ``data`` / ``data+props`` / ``none``) and
``to_error()`` (non-2xx -> :class:`CorvoApiError`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Literal,
    Mapping,
    Optional,
    Union,
)

import httpx

from .error import CorvoApiError, Result

Unwrap = Literal["data", "none"]
Query = Mapping[str, Union[str, int, float, bool, None]]

DEFAULT_BASE_URL = "https://api.corvo.tech"
DEFAULT_PREFIX = "v1"
DEFAULT_TIMEOUT = 30.0

_FILENAME_RE = re.compile(r'filename="([^"]+)"')


@dataclass
class DownloadedFile:
    """Binary payload from ``/invoices/:id/pdf|xml``."""

    content: bytes = field(default=b"")
    mime_type: Optional[str] = None
    file_name: Optional[str] = None


def is_private_host(hostname: str) -> bool:
    """True for loopback / RFC1918 / link-local hosts (http:// allowed there)."""
    host = hostname.lower().rstrip(".")
    if host in ("localhost", "[::1]", "::1") or host.endswith(".localhost"):
        return True
    parts = host.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        return False
    octets = [int(p) for p in parts]
    if any(o > 255 for o in octets):
        return False
    a, b = octets[0], octets[1]
    return (
        a == 127
        or a == 10
        or a == 0
        or (a == 192 and b == 168)
        or (a == 172 and 16 <= b <= 31)
        or (a == 169 and b == 254)
    )


def unwrap(value: Any, mode: Unwrap = "data") -> Any:
    """Unwrap a response envelope.

    - ``data`` -> ``body.data`` (or ``None`` if missing)
    - ``none`` -> the whole body
    """
    if mode == "none":
        return value
    return value.get("data") if isinstance(value, dict) else None


class Transport:
    """Thin async HTTP layer over ``httpx.AsyncClient``.

    Never raises for API/network/timeout failures — those come back as
    ``(None, CorvoApiError)``.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = DEFAULT_PREFIX,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._timeout = timeout
        self._client = client if client is not None else httpx.AsyncClient(timeout=timeout)
        cleaned_prefix = (prefix or "").strip("/")
        base = base_url.rstrip("/")
        self._base = f"{base}/{cleaned_prefix}" if cleaned_prefix else base
        self._headers: Dict[str, str] = {
            "X-API-Key": api_key,
            "Accept": "application/json",
        }

    @property
    def base_url(self) -> str:
        return self._base

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        query: Optional[Query] = None,
        idempotency_key: Optional[str] = None,
        unwrap: Unwrap = "data",
    ) -> Result[Any]:
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        params = {k: v for k, v in (query or {}).items() if v is not None} or None
        response, error = await self._send(
            method, f"{self._base}{path}", json=json, params=params, headers=headers
        )
        if error is not None:
            return (None, error)
        assert response is not None
        return self._handle_response(response, unwrap)

    async def request_form(
        self,
        method: str,
        path: str,
        *,
        files: Any,
        data: Any = None,
        unwrap: Unwrap = "data",
    ) -> Result[Any]:
        # httpx sets the multipart Content-Type boundary itself; we never set it.
        response, error = await self._send(
            method,
            f"{self._base}{path}",
            files=files,
            data=data,
            headers=dict(self._headers),
        )
        if error is not None:
            return (None, error)
        assert response is not None
        return self._handle_response(response, unwrap)

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Query] = None,
    ) -> Result[DownloadedFile]:
        params = {k: v for k, v in (query or {}).items() if v is not None} or None
        response, error = await self._send(
            method, f"{self._base}{path}", params=params, headers=dict(self._headers)
        )
        if error is not None:
            return (None, error)
        assert response is not None
        disposition = response.headers.get("Content-Disposition")
        match = _FILENAME_RE.search(disposition) if disposition else None
        return (
            DownloadedFile(
                content=response.content,
                mime_type=response.headers.get("Content-Type"),
                file_name=match.group(1) if match else None,
            ),
            None,
        )

    async def list_page(
        self,
        path: str,
        query: Optional[Query] = None,
    ) -> Result[Dict[str, Any]]:
        """Fetch one list page as ``{ data, pagination }`` (wire pass-through)."""
        raw, error = await self.request("GET", path, query=query, unwrap="none")
        if error is not None:
            return (None, error)
        body = raw if isinstance(raw, dict) else {}
        items = body.get("data") or []
        return ({"data": items, "pagination": body.get("pagination")}, None)

    async def iterate(
        self,
        path: str,
        query: Optional[Query] = None,
    ) -> AsyncIterator[Any]:
        """Walk cursor pages, yielding items.

        The only place in the SDK that raises: a first-page (or any-page)
        failure raises :class:`CorvoApiError` instead of returning a tuple,
        because an async generator has no ``yield`` slot for a result.
        """
        base_query = dict(query or {})
        cursor = base_query.get("cursor")
        while True:
            page_query = dict(base_query)
            if cursor is not None:
                page_query["cursor"] = cursor
            page, error = await self.list_page(path, page_query)
            if error is not None:
                raise error
            assert page is not None  # list_page returns (None, error) only on failure.
            for item in page.get("data") or []:
                yield item
            pagination = page.get("pagination") or {}
            if not pagination.get("hasMore"):
                return
            cursor = pagination.get("nextCursor")
            if cursor is None:
                return

    async def _send(
        self,
        method: str,
        url: str,
        *,
        headers: Dict[str, str],
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        files: Any = None,
        data: Any = None,
    ) -> tuple[Optional[httpx.Response], Optional[CorvoApiError]]:
        try:
            response = await self._client.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                files=files,
                data=data,
            )
        except httpx.TimeoutException as exc:
            return (
                None,
                CorvoApiError(
                    status=0,
                    code="timeout",
                    message=f"Request timed out after {self._timeout}s: {exc}",
                ),
            )
        except httpx.HTTPError as exc:
            return (
                None,
                CorvoApiError(
                    status=0,
                    code="network_error",
                    message=f"Network request failed: {exc}",
                ),
            )
        return (response, None)

    def _handle_response(
        self, response: httpx.Response, unwrap_mode: Unwrap
    ) -> Result[Any]:
        if response.status_code == 204:
            return (None, None)
        if response.status_code >= 400:
            return (None, self.to_error(response))
        if not response.content:
            return (None, None)
        try:
            parsed = response.json()
        except ValueError:
            return (
                None,
                CorvoApiError(
                    status=response.status_code,
                    code="invalid_json",
                    message="Invalid JSON in response",
                    request_id=response.headers.get("X-Request-Id"),
                ),
            )
        return (unwrap(parsed, unwrap_mode), None)

    def to_error(self, response: httpx.Response) -> CorvoApiError:
        """Map a non-2xx response to a typed error (see shared spec)."""
        body: Dict[str, Any] = {}
        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                parsed = response.json()
                if isinstance(parsed, dict):
                    body = parsed
            except ValueError:
                body = {}
        code = body.get("code") if isinstance(body.get("code"), str) else None
        message: str
        raw_message = body.get("message")
        if isinstance(raw_message, str):
            message = raw_message
        elif isinstance(raw_message, list):
            message = "; ".join(str(part) for part in raw_message)
        elif isinstance(body.get("error"), str):
            message = str(body["error"])
        else:
            message = f"Request failed with status {response.status_code}"
        raw_details = body.get("details")
        details: list[Dict[str, Any]] = (
            [part for part in raw_details if isinstance(part, dict)]
            if isinstance(raw_details, list)
            else []
        )
        request_id = body.get("requestId") or response.headers.get("X-Request-Id")
        retry_after = body.get("retryAfter")
        if not isinstance(retry_after, (int, float)):
            retry_after = None
            header_retry_after = response.headers.get("Retry-After")
            if header_retry_after is not None:
                try:
                    retry_after = float(header_retry_after)
                except ValueError:
                    retry_after = None
        return CorvoApiError(
            status=response.status_code,
            code=code if code else f"http_{response.status_code}",
            message=message,
            details=details,
            request_id=request_id if isinstance(request_id, str) else None,
            retry_after=int(retry_after) if retry_after is not None else None,
        )
