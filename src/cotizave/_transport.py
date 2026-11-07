"""The typed HTTP layer, built on httpx.

This adds what is specific to Cotizave on top of httpx: authentication, pinning
every request to the configured origin, refusing redirects, the retry policy
(quota vs. burst limits), a response-size cap, and mapping failures to typed
:class:`~cotizave.errors.CotizaveError`\\s. Resource modules sit on top of it;
most users never call it directly.
"""

from __future__ import annotations

import contextlib
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

import httpx

from ._headers import build_meta
from ._retry import next_delay_seconds, should_retry
from .config import (
    ResolvedConfig,
    ResponseEvent,
    RetryEvent,
    _validate_header_value,
    validate_headers,
)
from .errors import (
    APIConnectionError,
    APITimeoutError,
    CotizaveError,
    ResponseMeta,
    error_from_response,
)

QueryValue = Any  # str | int | float | bool | None
QueryParams = Mapping[str, QueryValue]


@dataclass(frozen=True)
class RawResult:
    """Low-level result returned by :meth:`Transport.request`."""

    #: Parsed body, or ``None`` on a ``304 Not Modified`` / empty body.
    data: Any
    #: Status, headers and parsed rate-limit metadata.
    meta: ResponseMeta
    #: True when the server answered ``304 Not Modified``.
    not_modified: bool


def _safe_call(hook: Optional[Any], event: Any) -> None:
    """Run a user hook; a throwing hook must never break a request."""
    if hook is None:
        return
    # Observability hooks are best-effort: a throwing hook never breaks a request.
    with contextlib.suppress(Exception):
        hook(event)


class Transport:
    def __init__(self, config: ResolvedConfig, http_client: Optional[httpx.Client] = None) -> None:
        self._config = config
        parts = urlsplit(config.base_url)
        self._origin = (parts.scheme, parts.netloc)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(follow_redirects=False)

    @property
    def history_timeout(self) -> float:
        return self._config.history_timeout

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # -- convenience wrappers ------------------------------------------------

    def get(self, path: str, query: Optional[QueryParams] = None, **config: Any) -> Any:
        return self.request(method="GET", path=path, query=query, **config).data

    def post(self, path: str, body: Any, **config: Any) -> Any:
        return self.request(method="POST", path=path, body=body, **config).data

    # -- the full request with retries --------------------------------------

    def request(
        self,
        *,
        method: str,
        path: str,
        query: Optional[QueryParams] = None,
        body: Any = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
        max_response_bytes: Optional[int] = None,
        if_none_match: Optional[str] = None,
        accept: Optional[str] = None,
        parse: str = "json",
    ) -> RawResult:
        config = self._config
        url = self._build_url(path, query)
        hdrs = self._build_headers(
            method, headers, language, accept, if_none_match, body is not None
        )
        timeout_s = timeout if timeout is not None else config.timeout
        max_bytes = (
            max_response_bytes if max_response_bytes is not None else config.max_response_bytes
        )
        limit = max_retries if max_retries is not None else config.max_retries
        policy = config.retry
        budget = config.max_retry_delay
        spent = 0.0
        attempt = 0

        while True:
            try:
                return self._exchange(method, path, url, hdrs, body, timeout_s, max_bytes, parse)
            except CotizaveError as error:
                if attempt >= limit or not should_retry(error, attempt, method, path, policy):
                    raise
                delay = next_delay_seconds(error, attempt, budget - spent, policy)
                if delay is None:
                    raise
                spent += delay
                _safe_call(
                    policy.on_retry,
                    _retry_event(error, attempt + 1, delay, method, path),
                )
                time.sleep(delay)
                attempt += 1

    # -- a single HTTP exchange, errors already mapped ----------------------

    def _exchange(
        self,
        method: str,
        path: str,
        url: str,
        headers: Dict[str, str],
        body: Any,
        timeout_s: float,
        max_bytes: int,
        parse: str,
    ) -> RawResult:
        content = json.dumps(body).encode("utf-8") if body is not None else None
        request = self._client.build_request(
            method, url, headers=headers, content=content, timeout=timeout_s
        )
        try:
            response = self._client.send(request, stream=True)
            try:
                if response.has_redirect_location:
                    location = response.headers.get("location")
                    raise CotizaveError(
                        f"Refusing to follow a redirect to {location!r}; the API is not "
                        "expected to redirect and following one could leak the API key.",
                        status=response.status_code,
                        code="unexpected_redirect",
                        meta=build_meta(response.status_code, response.headers),
                    )
                text = _read_capped(response, max_bytes, url)
            finally:
                response.close()
        except httpx.TimeoutException as exc:
            raise APITimeoutError(
                f"Request to {url} timed out after {timeout_s}s.",
                code="timeout",
                cause=exc,
            ) from exc
        except httpx.TransportError as exc:
            raise APIConnectionError(
                f"Network error while requesting {url}: {exc}",
                code="connection_error",
                cause=exc,
            ) from exc

        meta = build_meta(response.status_code, response.headers)
        _safe_call(self._config.on_response, _response_event(method, path, meta))
        status = response.status_code

        if status == 304:
            return RawResult(data=None, meta=meta, not_modified=True)
        if status >= 400:
            body_obj, raw_text = _parse_error_body(text)
            raise error_from_response(status, body_obj, meta, raw_text)
        if parse == "text":
            return RawResult(data=text, meta=meta, not_modified=False)
        if text.strip() == "":
            return RawResult(data=None, meta=meta, not_modified=False)
        try:
            return RawResult(data=json.loads(text), meta=meta, not_modified=False)
        except ValueError as exc:
            raise CotizaveError(
                f"Expected JSON from {url} but could not parse the response body.",
                status=status,
                code="invalid_json_response",
                details={"non_json_body": text[:500]},
                meta=meta,
            ) from exc

    # -- building the request -----------------------------------------------

    def _build_url(self, path: str, query: Optional[QueryParams]) -> str:
        parts = urlsplit(self._config.base_url + path)
        # A `path` must never change the host. Values like `@evil.com/...` parse
        # into a different origin and would send the X-API-Key header there.
        if (parts.scheme, parts.netloc) != self._origin:
            raise CotizaveError(
                f"Refusing to send a request to a different origin ({parts.scheme}://"
                f"{parts.netloc}). A request path must stay on "
                f"{self._origin[0]}://{self._origin[1]}.",
                code="invalid_request_path",
            )
        url = httpx.URL(urlunsplit(parts))
        if query:
            params = {k: _query_str(v) for k, v in query.items() if v is not None}
            if params:
                url = url.copy_merge_params(params)
        return str(url)

    def _build_headers(
        self,
        method: str,
        per_call: Optional[Mapping[str, str]],
        language: Optional[str],
        accept: Optional[str],
        if_none_match: Optional[str],
        has_body: bool,
    ) -> Dict[str, str]:
        config = self._config
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": config.user_agent,
        }
        headers.update(config.headers)
        if config.language:
            headers["Accept-Language"] = config.language

        for name, value in _guard(lambda: validate_headers(per_call, "headers")).items():
            headers[name] = value
        if language is not None:
            headers["Accept-Language"] = _guard(
                lambda: _validate_header_value(language, "language")
            )
        if accept is not None:
            headers["Accept"] = _guard(lambda: _validate_header_value(accept, "accept"))
        if if_none_match is not None:
            headers["If-None-Match"] = _guard(
                lambda: _validate_header_value(if_none_match, "if_none_match")
            )
        if method == "POST" and has_body:
            headers["Content-Type"] = "application/json"
        # The API key is set last; nothing can override it.
        headers["X-API-Key"] = config.api_key
        return headers


def _read_capped(response: httpx.Response, max_bytes: int, url: str) -> str:
    total = 0
    chunks = []
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise CotizaveError(
                f"Response body exceeded the maximum allowed size ({max_bytes} bytes).",
                code="response_too_large",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    return data.decode(response.encoding or "utf-8", errors="replace")


def _parse_error_body(text: str) -> Tuple[Optional[Mapping[str, Any]], Optional[str]]:
    stripped = text.strip()
    if stripped == "":
        return None, None
    try:
        parsed = json.loads(stripped)
    except ValueError:
        return None, text
    if isinstance(parsed, Mapping):
        return parsed, None
    return None, text


def _query_str(value: QueryValue) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _guard(validate: Any) -> Any:
    """Turn a validation failure of per-call input into a catchable CotizaveError."""
    try:
        return validate()
    except (TypeError, ValueError) as exc:
        raise CotizaveError(str(exc), code="invalid_header_value", cause=exc) from exc


def _retry_event(
    error: BaseException, retry_number: int, delay: float, method: str, path: str
) -> RetryEvent:
    return RetryEvent(error=error, retry_number=retry_number, delay=delay, method=method, path=path)


def _response_event(method: str, path: str, meta: ResponseMeta) -> ResponseEvent:
    return ResponseEvent(method=method, path=path, meta=meta)
