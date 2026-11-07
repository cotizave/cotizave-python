"""The retry *policy*: whether a failure is worth retrying and how long to wait.

These are pure functions. The retry *engine* (the loop and the sleeping) lives
in :mod:`cotizave._transport`.
"""

from __future__ import annotations

import random
from typing import Optional

from .config import RetryContext, _ResolvedRetry
from .errors import APIConnectionError, CotizaveError, RateLimitError


def default_should_retry(error: BaseException, method: str, policy: _ResolvedRetry) -> bool:
    """The built-in decision, before any custom ``should_retry``.

    Only idempotent (GET) requests are retried. A 429 is retried only when it is
    a burst (velocity) limit, never when the monthly quota is exhausted. Errors
    that require changing the request (4xx other than 408/429) are never retried.
    """
    if method != "GET":
        return False
    if isinstance(error, RateLimitError):
        return policy.retry_rate_limited and error.scope == "burst"
    if isinstance(error, APIConnectionError):  # network/timeout, no response
        return True
    if isinstance(error, CotizaveError):
        return error.status in policy.statuses
    return False


def should_retry(
    error: BaseException,
    attempt: int,
    method: str,
    path: str,
    policy: _ResolvedRetry,
) -> bool:
    """Final decision: the caller's ``should_retry`` wins when it returns a bool."""
    default = default_should_retry(error, method, policy)
    if policy.should_retry is None:
        return default
    custom = policy.should_retry(
        RetryContext(
            error=error, attempt=attempt, method=method, path=path, default_decision=default
        )
    )
    return custom if isinstance(custom, bool) else default


def next_delay_seconds(
    error: BaseException,
    attempt: int,
    budget_left: float,
    policy: _ResolvedRetry,
) -> Optional[float]:
    """Seconds to wait before the next attempt, or ``None`` to stop retrying.

    Honors a server ``Retry-After`` (seconds) or Cotizave's sub-second
    ``X-RateLimit-Retry-After-Ms`` when present; otherwise uses exponential
    backoff with full jitter. Returns ``None`` when the wait would exceed the
    remaining time budget.
    """
    if budget_left <= 0:
        return None

    if isinstance(error, RateLimitError) and error.meta is not None:
        info = error.meta.rate_limit
        hint: Optional[float] = None
        if info.retry_after_ms is not None:
            hint = info.retry_after_ms / 1000.0
        elif info.retry_after is not None:
            hint = float(info.retry_after)
        if hint is not None:
            server_wait = max(0.0, hint)  # a garbage/negative hint must not skip the wait
            return server_wait if server_wait <= budget_left else None

    # Exponential backoff with full jitter, capped per wait and by the budget.
    ceiling = min(policy.max_delay, policy.base_delay * (2**attempt))
    return min(random.random() * ceiling, budget_left)
