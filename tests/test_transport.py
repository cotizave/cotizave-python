from __future__ import annotations

import httpx
import pytest

from cotizave import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Cotizave,
    CotizaveError,
    FeatureNotInPlanError,
    ForbiddenError,
    NotAcceptableError,
    NotFoundError,
    RateLimitError,
    ServerError,
    UnprocessableError,
)

BASE = "https://api.cotizave.com"


def test_success_returns_parsed_json(client, mock_api):
    mock_api.get("/v2/fx/co/rates/co-trm").mock(
        return_value=httpx.Response(200, json={"id": "co-trm", "mid": 3950.5})
    )
    out = client.rates.get("CO", "co-trm")
    assert out["mid"] == 3950.5


def test_auth_header_and_user_agent_sent(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("AR")
    req = route.calls.last.request
    assert req.headers["x-api-key"] == "ctz_test_key"
    assert req.headers["user-agent"].startswith("cotizave-python/")
    assert req.headers["accept"] == "application/json"


def test_query_params_serialized(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("AR", tag="bcv", base="USD")
    url = str(route.calls.last.request.url)
    assert "tag=bcv" in url and "base=USD" in url


def test_none_query_params_omitted(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("AR")
    assert "tag=" not in str(route.calls.last.request.url)


@pytest.mark.parametrize(
    "status,exc,code",
    [
        (400, BadRequestError, "bad_request"),
        (401, AuthenticationError, "invalid_api_key"),
        (402, FeatureNotInPlanError, "feature_not_in_plan"),
        (403, ForbiddenError, "forbidden"),
        (404, NotFoundError, "rate_not_found"),
        (406, NotAcceptableError, "not_acceptable"),
        (422, UnprocessableError, "no_reference"),
        (500, ServerError, "server_error"),
    ],
)
def test_error_status_maps_to_subclass(client, mock_api, status, exc, code):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(status, json={"code": code, "message": "nope"})
    )
    with pytest.raises(exc) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.status == status
    assert info.value.code == code
    assert info.value.message == "nope"


def test_error_field_and_details(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(
            400,
            json={
                "code": "unknown_parameter",
                "message": "bad",
                "field": "base",
                "details": {"k": 1},
            },
        )
    )
    with pytest.raises(BadRequestError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.field == "base"
    assert info.value.details == {"k": 1}


def test_non_json_error_body_kept(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(502, text="<html>Bad Gateway</html>")
    )
    with pytest.raises(ServerError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert "non_json_body" in (info.value.details or {})


def test_rate_limit_scope_and_retry_after(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "30", "X-RateLimit-Scope": "monthly"},
            json={
                "code": "rate_limit_exceeded",
                "message": "quota",
                "details": {"kind": "monthly"},
            },
        )
    )
    with pytest.raises(RateLimitError) as info:
        client.rates.get("CO", "x", max_retries=0)
    err = info.value
    assert err.scope == "monthly"
    assert err.is_quota_exhausted is True
    assert err.retry_after == 30


def test_304_not_modified(client, mock_api):
    mock_api.get("/v2/fx/co/rates/co-trm").mock(return_value=httpx.Response(304))
    result = client.request(path="/v2/fx/co/rates/co-trm", if_none_match='"etag"')
    assert result.not_modified is True
    assert result.data is None


def test_response_too_large():
    with Cotizave(api_key="x", max_response_bytes=10) as c:
        import respx

        with respx.mock(base_url=BASE) as m:
            m.get("/v2/fx/co/rates/x").mock(return_value=httpx.Response(200, text="x" * 1000))
            with pytest.raises(CotizaveError) as info:
                c.rates.get("CO", "x", max_retries=0)
            assert info.value.code == "response_too_large"


def test_origin_pinning_rejects_offhost(client):
    with pytest.raises(CotizaveError) as info:
        client.request(path="@evil.com/steal")
    assert info.value.code == "invalid_request_path"


def test_invalid_json_success_body(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(
            200, text="not json {", headers={"content-type": "application/json"}
        )
    )
    with pytest.raises(CotizaveError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.code == "invalid_json_response"


def test_timeout_maps_to_timeout_error(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.code == "timeout"


def test_connection_error_maps(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(APIConnectionError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.code == "connection_error"


def test_redirect_refused(client, mock_api):
    mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(302, headers={"location": "https://evil.com"})
    )
    with pytest.raises(CotizaveError) as info:
        client.rates.get("CO", "x", max_retries=0)
    assert info.value.code == "unexpected_redirect"
