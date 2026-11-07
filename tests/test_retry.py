from __future__ import annotations

import httpx
import pytest

from cotizave import Cotizave, RateLimitError, RetryOptions, ServerError


def test_retries_5xx_then_succeeds(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/x").mock(
        side_effect=[
            httpx.Response(503, json={"code": "server_error", "message": "x"}),
            httpx.Response(200, json={"id": "x", "mid": 1.0}),
        ]
    )
    out = client.rates.get("CO", "x")
    assert out["mid"] == 1.0
    assert route.call_count == 2


def test_stops_after_max_retries(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(503, json={"code": "server_error", "message": "x"})
    )
    with pytest.raises(ServerError):
        client.rates.get("CO", "x", max_retries=2)
    assert route.call_count == 3  # 1 + 2 retries


def test_max_retries_zero_disables(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(503, json={"code": "server_error", "message": "x"})
    )
    with pytest.raises(ServerError):
        client.rates.get("CO", "x", max_retries=0)
    assert route.call_count == 1


def test_burst_429_is_retried(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/x").mock(
        side_effect=[
            httpx.Response(
                429,
                headers={"Retry-After": "0", "X-RateLimit-Scope": "burst"},
                json={
                    "code": "rate_limit_exceeded",
                    "message": "slow",
                    "details": {"kind": "burst"},
                },
            ),
            httpx.Response(200, json={"id": "x", "mid": 1.0}),
        ]
    )
    out = client.rates.get("CO", "x")
    assert out["mid"] == 1.0
    assert route.call_count == 2


def test_monthly_429_is_not_retried(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/x").mock(
        return_value=httpx.Response(
            429,
            headers={"X-RateLimit-Scope": "monthly"},
            json={
                "code": "rate_limit_exceeded",
                "message": "quota",
                "details": {"kind": "monthly"},
            },
        )
    )
    with pytest.raises(RateLimitError):
        client.rates.get("CO", "x")
    assert route.call_count == 1


def test_post_is_not_retried_by_default(client, mock_api):
    route = mock_api.post("/v2/fx/convert").mock(
        return_value=httpx.Response(503, json={"code": "server_error", "message": "x"})
    )
    with pytest.raises(ServerError):
        client.convert_bulk([{"from": "USD", "to": "ARS", "amount": 1}])
    assert route.call_count == 1


def test_custom_should_retry_overrides():
    calls = {"n": 0}

    def never(ctx):
        calls["n"] += 1
        return False

    c = Cotizave(api_key="x", retry=RetryOptions(should_retry=never))
    import respx

    with respx.mock(base_url="https://api.cotizave.com") as m:
        route = m.get("/v2/fx/co/rates/x").mock(
            return_value=httpx.Response(503, json={"code": "server_error", "message": "x"})
        )
        with pytest.raises(ServerError):
            c.rates.get("CO", "x")
        assert route.call_count == 1
        assert calls["n"] == 1
    c.close()


def test_on_retry_hook_called(mock_api):
    events = []
    c = Cotizave(api_key="x", retry=RetryOptions(on_retry=lambda e: events.append(e)))
    mock_api.get("/v2/fx/co/rates/x").mock(
        side_effect=[
            httpx.Response(503, json={"code": "server_error", "message": "x"}),
            httpx.Response(200, json={"id": "x", "mid": 1.0}),
        ]
    )
    c.rates.get("CO", "x")
    assert len(events) == 1
    assert events[0].retry_number == 1
    assert events[0].path == "/v2/fx/co/rates/x"
    c.close()


def test_on_response_hook_called():
    seen = []
    c = Cotizave(api_key="x", on_response=lambda e: seen.append(e.meta.status))
    import respx

    with respx.mock(base_url="https://api.cotizave.com") as m:
        m.get("/v2/fx/co/rates/x").mock(return_value=httpx.Response(200, json={"id": "x"}))
        c.rates.get("CO", "x")
    assert seen == [200]
    c.close()
