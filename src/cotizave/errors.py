"""The error hierarchy raised by the SDK.

Catch :class:`CotizaveError` to handle any API failure, or a subclass
(e.g. :class:`RateLimitError`) for a specific family. Every error carries the
API-provided ``code`` and ``message`` when available, plus optional
``field``/``details`` and the response metadata (status, headers, rate-limit
info).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type


@dataclass(frozen=True)
class RateLimitInfo:
    """Parsed rate-limit metadata from response headers."""

    #: Which axis was hit on a 429: ``"monthly"`` quota vs ``"burst"`` (per-minute).
    scope: Optional[str] = None
    #: Monthly quota ceiling (``X-RateLimit-Limit``).
    limit: Optional[int] = None
    #: Monthly quota remaining (``X-RateLimit-Remaining``).
    remaining: Optional[int] = None
    #: When the monthly quota resets (``X-RateLimit-Reset``, RFC 3339).
    reset: Optional[str] = None
    #: Per-minute velocity ceiling (``X-RateLimit-Limit-Minute``).
    limit_per_minute: Optional[int] = None
    #: Per-minute velocity remaining (``X-RateLimit-Remaining-Minute``).
    remaining_per_minute: Optional[int] = None
    #: ``Retry-After`` in whole seconds.
    retry_after: Optional[int] = None
    #: Sub-second retry hint for burst limits (``X-RateLimit-Retry-After-Ms``).
    retry_after_ms: Optional[int] = None


@dataclass(frozen=True)
class ResponseMeta:
    """Everything the SDK knows about a finished HTTP exchange."""

    status: int
    headers: Mapping[str, str]
    rate_limit: RateLimitInfo
    request_id: Optional[str] = None


class CotizaveError(Exception):
    """Base class for every error the SDK raises."""

    def __init__(
        self,
        message: str,
        *,
        status: int = 0,
        code: str = "cotizave_error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        meta: Optional[ResponseMeta] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        #: HTTP status code, or 0 when the request never completed (network/timeout).
        self.status = status
        #: Machine-readable error code from the API (e.g. ``rate_limit_exceeded``).
        self.code = code
        #: Offending field, when the API points at one.
        self.field = field
        #: Structured extra context from the API error body.
        self.details = details
        #: Response metadata, including parsed rate-limit headers.
        self.meta = meta
        if cause is not None:
            self.__cause__ = cause

    @property
    def rate_limit(self) -> Optional[RateLimitInfo]:
        """Rate-limit metadata parsed from the response, if any."""
        return self.meta.rate_limit if self.meta is not None else None

    @property
    def headers(self) -> Optional[Mapping[str, str]]:
        """Response headers, if the request completed."""
        return self.meta.headers if self.meta is not None else None

    @property
    def request_id(self) -> Optional[str]:
        """The server-assigned request id (``X-Request-Id``), for support."""
        return self.meta.request_id if self.meta is not None else None

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}(status={self.status}, code={self.code!r})"


class BadRequestError(CotizaveError):
    """400 — invalid parameters, formats, or body."""


class AuthenticationError(CotizaveError):
    """401 — missing, invalid, or revoked API key."""


class FeatureNotInPlanError(CotizaveError):
    """402 — the requested feature is not included in the account's plan."""


class ForbiddenError(CotizaveError):
    """403 — account restriction or out-of-retention access."""


class NotFoundError(CotizaveError):
    """404 — resource or rate not found, or country not supported."""


class NotAcceptableError(CotizaveError):
    """406 — the requested format cannot represent this response."""


class UnprocessableError(CotizaveError):
    """422 — the operation has no usable reference right now."""


class ServerError(CotizaveError):
    """5xx — server-side failure."""


class APIConnectionError(CotizaveError):
    """The request failed before any response (DNS, TCP, TLS, abort)."""


class APITimeoutError(APIConnectionError):
    """The request was aborted because it exceeded the configured timeout."""


class RateLimitError(CotizaveError):
    """429 — rate limited. Use :attr:`scope` to tell quota from burst."""

    @property
    def scope(self) -> Optional[str]:
        """``"monthly"`` = quota exhausted (do not retry soon); ``"burst"`` = slow down."""
        from_details = (self.details or {}).get("kind")
        if from_details in ("monthly", "burst"):
            return from_details
        return self.meta.rate_limit.scope if self.meta is not None else None

    @property
    def retry_after(self) -> Optional[int]:
        """``Retry-After`` in seconds, if provided."""
        return self.meta.rate_limit.retry_after if self.meta is not None else None

    @property
    def is_quota_exhausted(self) -> bool:
        """True when the monthly quota is exhausted (waiting a few seconds won't help)."""
        return self.scope == "monthly"


_STATUS_MAP: Dict[int, Type[CotizaveError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: FeatureNotInPlanError,
    403: ForbiddenError,
    404: NotFoundError,
    406: NotAcceptableError,
    422: UnprocessableError,
    429: RateLimitError,
}


def _fallback_code(status: int) -> str:
    if status >= 500:
        return "server_error"
    if status == 404:
        return "resource_not_found"
    return "http_error"


def _truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def error_from_response(
    status: int,
    body: Optional[Mapping[str, Any]],
    meta: ResponseMeta,
    raw_body_text: Optional[str] = None,
) -> CotizaveError:
    """Build the right :class:`CotizaveError` subclass from a completed response.

    ``body`` is the already-parsed error payload, or ``None`` when the body was
    absent or not valid JSON (e.g. an HTML page from a proxy).
    """
    ctor: Type[CotizaveError] = _STATUS_MAP.get(
        status, ServerError if status >= 500 else CotizaveError
    )

    has_api_error = isinstance(body, Mapping) and isinstance(body.get("code"), str)
    code = body["code"] if has_api_error else _fallback_code(status)  # type: ignore[index]
    message = (
        body["message"]  # type: ignore[index]
        if has_api_error and body.get("message")  # type: ignore[union-attr]
        else f"Unexpected HTTP {status} response from Cotizave."
    )

    details: Optional[Dict[str, Any]]
    if has_api_error:
        raw_details = body.get("details")  # type: ignore[union-attr]
        details = dict(raw_details) if isinstance(raw_details, Mapping) else None
    elif raw_body_text:
        details = {"non_json_body": _truncate(raw_body_text)}
    else:
        details = None

    kwargs: Dict[str, Any] = {"status": status, "code": code, "meta": meta}
    if has_api_error and isinstance(body.get("field"), str):  # type: ignore[union-attr]
        kwargs["field"] = body["field"]  # type: ignore[index]
    if details is not None:
        kwargs["details"] = details
    return ctor(message, **kwargs)
