from __future__ import annotations

from cotizave import RateLimitError
from cotizave.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitInfo,
    ResponseMeta,
    ServerError,
    error_from_response,
)


def _meta(status=400, rate_limit=None):
    return ResponseMeta(status=status, headers={}, rate_limit=rate_limit or RateLimitInfo())


def test_error_from_response_uses_api_code():
    err = error_from_response(401, {"code": "invalid_api_key", "message": "bad"}, _meta(401))
    assert isinstance(err, AuthenticationError)
    assert err.code == "invalid_api_key"
    assert err.message == "bad"


def test_error_from_response_fallback_code():
    err = error_from_response(404, None, _meta(404))
    assert isinstance(err, NotFoundError)
    assert err.code == "resource_not_found"


def test_error_from_response_server_fallback():
    err = error_from_response(503, None, _meta(503))
    assert isinstance(err, ServerError)
    assert err.code == "server_error"


def test_rate_limit_scope_from_details():
    err = error_from_response(
        429,
        {"code": "rate_limit_exceeded", "message": "x", "details": {"kind": "burst"}},
        _meta(429),
    )
    assert isinstance(err, RateLimitError)
    assert err.scope == "burst"
    assert err.is_quota_exhausted is False


def test_rate_limit_scope_from_headers():
    err = error_from_response(
        429,
        {"code": "rate_limit_exceeded", "message": "x"},
        _meta(429, RateLimitInfo(scope="monthly", retry_after=60)),
    )
    assert err.scope == "monthly"
    assert err.retry_after == 60
    assert err.is_quota_exhausted is True


def test_non_json_body_captured_in_details():
    err = error_from_response(502, None, _meta(502), raw_body_text="<html>oops</html>")
    assert err.details == {"non_json_body": "<html>oops</html>"}
