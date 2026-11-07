"""Client configuration: options, validation and resolved defaults.

Misconfiguration raises a plain :class:`ValueError`/:class:`TypeError` (not a
:class:`~cotizave.errors.CotizaveError`), because no request has been made yet.
"""

from __future__ import annotations

import platform
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, FrozenSet, Optional
from urllib.parse import urlsplit

from ._version import __version__

if TYPE_CHECKING:
    from .errors import ResponseMeta

DEFAULT_BASE_URL = "https://api.cotizave.com"
# The API cuts any response at 10s and its own queries at 1-1.5s, so these stay low.
DEFAULT_TIMEOUT = 5.0
DEFAULT_HISTORY_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_RETRY_DELAY = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 25_000_000
DEFAULT_RETRY_BASE_DELAY = 0.25
DEFAULT_RETRY_MAX_DELAY = 2.0
DEFAULT_RETRY_STATUSES: Sequence[int] = (408, 500, 502, 503, 504)

#: Environment variable the client reads when ``api_key`` is not passed explicitly.
API_KEY_ENV_VAR = "COTIZAVE_API_KEY"

#: Header the SDK owns; callers can never set or replace it.
_RESERVED_HEADER = "x-api-key"
_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]+$")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class RetryContext:
    """What a custom :attr:`RetryOptions.should_retry` receives."""

    #: The error of the failed attempt (usually a ``CotizaveError``).
    error: BaseException
    #: Zero-based index of the attempt that just failed.
    attempt: int
    method: str
    #: Request path, e.g. ``/v2/fx/ar/rates``.
    path: str
    #: What the built-in policy would decide for this failure.
    default_decision: bool


@dataclass(frozen=True)
class RetryEvent:
    """Passed to :attr:`RetryOptions.on_retry` right before the SDK waits and retries."""

    error: BaseException
    #: One-based number of the retry about to happen.
    retry_number: int
    #: How long the SDK will wait before retrying, in seconds.
    delay: float
    method: str
    path: str


@dataclass(frozen=True)
class ResponseEvent:
    """Passed to ``on_response`` for every completed HTTP exchange."""

    method: str
    path: str
    #: Status, headers and parsed rate-limit metadata.
    meta: ResponseMeta


@dataclass
class RetryOptions:
    """Fine-grained retry behaviour. Every field has a production-safe default.

    How *many* retries and the total time budget are the top-level ``max_retries``
    and ``max_retry_delay`` client options.
    """

    #: Base delay (seconds) of the exponential backoff.
    base_delay: float = DEFAULT_RETRY_BASE_DELAY
    #: Ceiling (seconds) for a single backoff wait.
    max_delay: float = DEFAULT_RETRY_MAX_DELAY
    #: HTTP statuses retried for idempotent (GET) requests.
    statuses: Sequence[int] = DEFAULT_RETRY_STATUSES
    #: Retry a ``429`` caused by the per-minute (burst) limit, waiting for the
    #: server's ``Retry-After``. A ``429`` from an exhausted monthly quota is
    #: never retried by the built-in policy.
    retry_rate_limited: bool = True
    #: Take the decision yourself. Return ``True``/``False`` to override the
    #: built-in policy, or ``None`` to keep it. Retries stay bounded by
    #: ``max_retries`` and ``max_retry_delay`` either way.
    should_retry: Optional[Callable[[RetryContext], Optional[bool]]] = None
    #: Called before each retry wait. Handy for logging and metrics.
    on_retry: Optional[Callable[[RetryEvent], None]] = None


@dataclass(frozen=True)
class PublicConfig:
    """The configuration exposed on ``client.config``.

    It leaves out the API key, custom headers, hooks and the HTTP client, so
    logging or serializing a client is always safe.
    """

    base_url: str
    timeout: float
    history_timeout: float
    max_retries: int
    max_retry_delay: float
    max_response_bytes: int
    user_agent: str
    language: Optional[str] = None


@dataclass(frozen=True)
class _ResolvedRetry:
    base_delay: float
    max_delay: float
    statuses: FrozenSet[int]
    retry_rate_limited: bool
    should_retry: Optional[Callable[[RetryContext], Optional[bool]]]
    on_retry: Optional[Callable[[RetryEvent], None]]


@dataclass(frozen=True)
class ResolvedConfig:
    """Fully-resolved configuration with defaults applied. Internal to the SDK."""

    api_key: str
    base_url: str
    timeout: float
    history_timeout: float
    max_retries: int
    max_retry_delay: float
    retry: _ResolvedRetry
    max_response_bytes: int
    headers: Mapping[str, str]
    user_agent: str
    language: Optional[str] = None
    on_response: Optional[Callable[[ResponseEvent], None]] = None

    def to_public(self) -> PublicConfig:
        return PublicConfig(
            base_url=self.base_url,
            timeout=self.timeout,
            history_timeout=self.history_timeout,
            max_retries=self.max_retries,
            max_retry_delay=self.max_retry_delay,
            max_response_bytes=self.max_response_bytes,
            user_agent=self.user_agent,
            language=self.language,
        )


def _base_user_agent() -> str:
    return f"cotizave-python/{__version__} python/{platform.python_version()}"


def _validate_header_value(value: object, name: str) -> str:
    """Reject non-strings and CR/LF/control characters (header injection)."""
    if not isinstance(value, str) or _CONTROL_CHARS_RE.search(value):
        raise TypeError(f"Cotizave: `{name}` must be a string without control characters.")
    return value


def validate_headers(headers: Optional[Mapping[str, str]], option_name: str) -> Dict[str, str]:
    """Validate caller-supplied headers and return a clean copy."""
    clean: Dict[str, str] = {}
    if headers is None:
        return clean
    if not isinstance(headers, Mapping):
        raise TypeError(f"Cotizave: `{option_name}` must be a mapping of header names to values.")
    for name, value in headers.items():
        if not isinstance(name, str) or not _HEADER_NAME_RE.match(name):
            raise TypeError(f"Cotizave: invalid header name in `{option_name}`: {name!r}")
        if name.lower() == _RESERVED_HEADER:
            raise TypeError(
                f"Cotizave: `{option_name}` cannot set the X-API-Key header; "
                "use the `api_key` option."
            )
        clean[name] = _validate_header_value(value, f"{option_name}.{name}")
    return clean


def _number(value: Optional[float], name: str, minimum: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"Cotizave: `{name}` must be a number.")
    if value != value or value in (float("inf"), float("-inf")):  # NaN / inf
        raise ValueError(f"Cotizave: `{name}` must be finite.")
    if value < minimum:
        raise ValueError(f"Cotizave: `{name}` must be >= {minimum}.")
    return float(value)


def _integer(value: Optional[int], name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Cotizave: `{name}` must be an integer.")
    if value < minimum:
        raise ValueError(f"Cotizave: `{name}` must be >= {minimum}.")
    return value


def _resolve_base_url(base_url: str, allow_insecure_http: bool) -> str:
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"Cotizave: `base_url` must be an http(s) URL, got: {base_url!r}")
    if parts.scheme == "http" and not allow_insecure_http:
        raise ValueError(
            "Cotizave: `base_url` uses http:// which would send your API key in cleartext. "
            "Use https://, or set allow_insecure_http=True for local testing."
        )
    return base_url.rstrip("/")


def _resolve_retry(retry: Optional[RetryOptions]) -> _ResolvedRetry:
    retry = retry or RetryOptions()
    if not isinstance(retry, RetryOptions):
        raise TypeError("Cotizave: `retry` must be a RetryOptions instance.")
    statuses = tuple(retry.statuses)
    if not all(isinstance(s, int) and not isinstance(s, bool) for s in statuses):
        raise TypeError("Cotizave: `retry.statuses` must be a sequence of HTTP status codes.")
    base_delay = _number(retry.base_delay, "retry.base_delay", 0)
    max_delay = _number(retry.max_delay, "retry.max_delay", 0)
    return _ResolvedRetry(
        base_delay=base_delay,
        max_delay=max(max_delay, base_delay),
        statuses=frozenset(statuses),
        retry_rate_limited=bool(retry.retry_rate_limited),
        should_retry=retry.should_retry,
        on_retry=retry.on_retry,
    )


def resolve_config(
    *,
    api_key: str,
    base_url: str,
    timeout: float,
    history_timeout: float,
    max_retries: int,
    max_retry_delay: float,
    max_response_bytes: int,
    retry: Optional[RetryOptions],
    headers: Optional[Mapping[str, str]],
    language: Optional[str],
    user_agent: Optional[str],
    allow_insecure_http: bool,
    on_response: Optional[Callable[[ResponseEvent], None]],
) -> ResolvedConfig:
    """Validate and normalize client options, applying defaults."""
    if not isinstance(api_key, str) or api_key.strip() == "":
        raise ValueError(
            "Cotizave: an API key is required. Pass api_key=... or set the "
            f"{API_KEY_ENV_VAR} environment variable."
        )
    ua = _base_user_agent()
    if user_agent is not None:
        ua = f"{ua} {_validate_header_value(user_agent, 'user_agent')}".strip()
    return ResolvedConfig(
        api_key=api_key,
        base_url=_resolve_base_url(base_url, allow_insecure_http),
        timeout=_number(timeout, "timeout", 0.001),
        history_timeout=_number(history_timeout, "history_timeout", 0.001),
        max_retries=_integer(max_retries, "max_retries", 0),
        max_retry_delay=_number(max_retry_delay, "max_retry_delay", 0),
        retry=_resolve_retry(retry),
        max_response_bytes=_integer(max_response_bytes, "max_response_bytes", 1),
        headers=validate_headers(headers, "headers"),
        language=_validate_header_value(language, "language") if language is not None else None,
        user_agent=ua,
        on_response=on_response,
    )
