"""Parsing of Cotizave's response headers into typed metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Dict, Optional

from .errors import RateLimitInfo, ResponseMeta


def _to_record(headers: Mapping[str, str]) -> Dict[str, str]:
    """Flatten headers into a lowercase-keyed plain dict."""
    return {str(k).lower(): v for k, v in headers.items()}


def _int(record: Mapping[str, str], key: str) -> Optional[int]:
    raw = record.get(key)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def parse_rate_limit(record: Mapping[str, str]) -> RateLimitInfo:
    """Parse Cotizave's rate-limit headers from a (lowercased) record."""
    scope = record.get("x-ratelimit-scope")
    return RateLimitInfo(
        scope=scope if scope in ("monthly", "burst") else None,
        limit=_int(record, "x-ratelimit-limit"),
        remaining=_int(record, "x-ratelimit-remaining"),
        reset=record.get("x-ratelimit-reset"),
        limit_per_minute=_int(record, "x-ratelimit-limit-minute"),
        remaining_per_minute=_int(record, "x-ratelimit-remaining-minute"),
        retry_after=_int(record, "retry-after"),
        retry_after_ms=_int(record, "x-ratelimit-retry-after-ms"),
    )


def build_meta(status: int, headers: Mapping[str, str]) -> ResponseMeta:
    """Build response metadata (status, headers, request id, rate limit)."""
    record = _to_record(headers)
    return ResponseMeta(
        status=status,
        headers=record,
        rate_limit=parse_rate_limit(record),
        request_id=record.get("x-request-id") or None,
    )
