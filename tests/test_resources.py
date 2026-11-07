from __future__ import annotations

import json

import httpx
import pytest


def _url(route):
    return str(route.calls.last.request.url)


def test_rates_list(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("CO")
    assert route.calls.last.request.url.path == "/v2/fx/co/rates"


def test_rates_get_encodes_segment(client, mock_api):
    route = mock_api.get("/v2/fx/co/rates/co-trm").mock(
        return_value=httpx.Response(200, json={"id": "co-trm"})
    )
    client.rates.get("CO", "co-trm")
    assert route.calls.last.request.url.path == "/v2/fx/co/rates/co-trm"


def test_rates_snapshot_uses_date(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.snapshot("AR", "2026-10-01")
    assert "date=2026-10-01" in _url(route)


def test_rates_global_joins_symbols(client, mock_api):
    route = mock_api.get("/v2/fx/rates").mock(return_value=httpx.Response(200, json={"rates": []}))
    client.rates.global_(symbols=["BRL", "EUR"])
    assert "symbols=BRL%2CEUR" in _url(route) or "symbols=BRL,EUR" in _url(route)


def test_country_code_normalized_to_lower(client, mock_api):
    route = mock_api.get("/v2/fx/ve/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("VE")
    assert route.calls.last.request.url.path == "/v2/fx/ve/rates"


def test_convert_requires_positive_amount(client):
    with pytest.raises(TypeError):
        client.convert(from_="USD", to="BRL", amount=0)
    with pytest.raises(TypeError):
        client.convert(from_="USD", to="BRL", amount=-5)


def test_convert_builds_query(client, mock_api):
    route = mock_api.get("/v2/fx/convert").mock(
        return_value=httpx.Response(200, json={"rate": 5.0})
    )
    client.convert(from_="USD", to="BRL", amount=100)
    url = _url(route)
    assert "from=USD" in url and "to=BRL" in url and "amount=100" in url


def test_convert_bulk_posts_body(client, mock_api):
    route = mock_api.post("/v2/fx/convert").mock(
        return_value=httpx.Response(200, json={"count": 1, "results": []})
    )
    client.convert_bulk([{"from": "USD", "to": "ARS", "amount": 1}])
    body = json.loads(route.calls.last.request.content)
    assert body == {"conversions": [{"from": "USD", "to": "ARS", "amount": 1}]}
    assert route.calls.last.request.headers["content-type"] == "application/json"


def test_convert_bulk_empty_rejected(client):
    with pytest.raises(TypeError):
        client.convert_bulk([])


def test_convert_bulk_too_many_rejected(client):
    with pytest.raises(TypeError):
        client.convert_bulk([{"from": "USD", "to": "ARS", "amount": 1}] * 51)


def test_history_daily_query(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates/ar-official/history").mock(
        return_value=httpx.Response(200, json={"points": []})
    )
    client.history.daily("AR", "ar-official", from_="2026-09-01", to="2026-09-30")
    url = _url(route)
    assert "granularity=daily" in url and "from=2026-09-01" in url and "to=2026-09-30" in url


def test_history_iterate_follows_cursor(client, mock_api):
    mock_api.get("/v2/fx/ve/rates/ve-bcv/history").mock(
        side_effect=[
            httpx.Response(200, json={"points": [{"date": "2026-01-01"}], "next_cursor": "c2"}),
            httpx.Response(200, json={"points": [{"date": "2026-01-02"}], "next_cursor": None}),
        ]
    )
    points = list(client.history.iterate("VE", "ve-bcv"))
    assert [p["date"] for p in points] == ["2026-01-01", "2026-01-02"]


def test_history_iterate_respects_max_pages(client, mock_api):
    route = mock_api.get("/v2/fx/ve/rates/ve-bcv/history").mock(
        return_value=httpx.Response(200, json={"points": [{"date": "d"}], "next_cursor": "more"})
    )
    points = list(client.history.iterate("VE", "ve-bcv", max_pages=3))
    assert len(points) == 3
    assert route.call_count == 3


def test_markets_spread_route_bank_rates(client, mock_api):
    m = mock_api.get("/v2/fx/ve/markets").mock(
        return_value=httpx.Response(200, json={"markets": []})
    )
    s = mock_api.get("/v2/fx/ve/spread").mock(return_value=httpx.Response(200, json={}))
    r = mock_api.get("/v2/fx/ve/route").mock(return_value=httpx.Response(200, json={}))
    b = mock_api.get("/v2/fx/ve/bank-rates").mock(
        return_value=httpx.Response(200, json={"banks": []})
    )
    client.markets("VE")
    client.spread("VE", against="ve-paralelo")
    client.route("VE", from_="USD", to="VES", amount=100)
    client.bank_rates("VE", bank="0102")
    assert m.called and s.called and r.called and b.called
    assert "against=ve-paralelo" in str(s.calls.last.request.url)
    assert "amount=100" in str(r.calls.last.request.url)
    assert "bank=0102" in str(b.calls.last.request.url)


def test_catalogs(client, mock_api):
    co = mock_api.get("/v2/countries").mock(
        return_value=httpx.Response(200, json={"countries": []})
    )
    cu = mock_api.get("/v2/currencies").mock(
        return_value=httpx.Response(200, json={"currencies": []})
    )
    bk = mock_api.get("/v2/banks/ve").mock(return_value=httpx.Response(200, json={"banks": []}))
    iss = mock_api.get("/v2/issuers").mock(return_value=httpx.Response(200, json={"issuers": []}))
    assert client.countries.list() == {"countries": []}
    assert client.currencies.list() == {"currencies": []}
    assert client.banks.list("VE", q="banesco") == {"banks": []}
    assert client.issuers.list() == {"issuers": []}
    assert co.called and cu.called and bk.called and iss.called
    assert "q=banesco" in str(bk.calls.last.request.url)


def test_holidays(client, mock_api):
    yr = mock_api.get("/v2/holidays/ar").mock(
        return_value=httpx.Response(200, json={"country": "AR", "year": 2026, "holidays": []})
    )
    bd = mock_api.get("/v2/holidays/ve/business-days").mock(
        return_value=httpx.Response(200, json={"result": "2026-10-08"})
    )
    client.holidays.list("AR", year=2026)
    client.holidays.business_days("VE", from_="2026-10-01", days=5)
    assert "year=2026" in str(yr.calls.last.request.url)
    assert "days=5" in str(bd.calls.last.request.url)


def test_business_days_validates(client):
    with pytest.raises(TypeError):
        client.holidays.business_days("VE", days=-1)


def test_crypto(client, mock_api):
    lst = mock_api.get("/v2/crypto").mock(return_value=httpx.Response(200, json={"rates": []}))
    one = mock_api.get("/v2/crypto/usdt-usd").mock(
        return_value=httpx.Response(200, json={"id": "usdt-usd"})
    )
    client.crypto.list(tag="usdt")
    client.crypto.get("usdt-usd")
    assert "tag=usdt" in str(lst.calls.last.request.url)
    assert one.calls.last.request.url.path == "/v2/crypto/usdt-usd"


def test_export_csv(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, text="id,mid\nar-official,1000")
    )
    out = client.export("/v2/fx/ar/rates", format="csv")
    assert out.startswith("id,mid")
    assert route.calls.last.request.headers["accept"] == "text/csv"
    assert "format=csv" in str(route.calls.last.request.url)


def test_export_rejects_bad_format(client):
    with pytest.raises(ValueError):
        client.export("/v2/fx/ar/rates", format="pdf")


def test_per_call_language_and_headers(client, mock_api):
    route = mock_api.get("/v2/fx/ar/rates").mock(
        return_value=httpx.Response(200, json={"rates": []})
    )
    client.rates.list("AR", language="es", headers={"X-Trace": "abc"})
    req = route.calls.last.request
    assert req.headers["accept-language"] == "es"
    assert req.headers["x-trace"] == "abc"
