<div align="center">

**English** · [Español](./README.es.md)

# Cotizave Python SDK

Official, fully-typed Python client for the **Cotizave API v2** — multi-country
exchange-rate references, currency conversion, historical series, bank rates and
calendars, behind a single API key.

[![PyPI](https://img.shields.io/pypi/v/cotizave?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/cotizave/)
[![Python](https://img.shields.io/pypi/pyversions/cotizave)](https://pypi.org/project/cotizave/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

[API & docs hub](https://github.com/cotizave/exchange-rates-api) · [Documentation](https://docs.cotizave.com) · [API reference](https://docs.cotizave.com/api/v2/introduction) · [Get an API key](https://app.cotizave.com)

</div>

---

## Install

```bash
pip install cotizave
```

Requires Python 3.10+. The only runtime dependency is [httpx](https://www.python-httpx.org/).

## Quick start

```python
from cotizave import Cotizave

# Reads COTIZAVE_API_KEY from the environment; or pass api_key="..."
client = Cotizave()

# Every rate published for a country
response = client.rates.list("AR")
for rate in response["rates"]:
    print(rate["id"], rate.get("mid"))

# A single rate by its canonical id
trm = client.rates.get("CO", "co-trm")
print(trm["mid"])

# A currency conversion (resolved on Cotizave, never computed client-side)
result = client.convert(from_="USD", to="BRL", amount=100)
print(result["to"]["amount"])

client.close()
```

Use it as a context manager to close the connection pool automatically:

```python
with Cotizave() as client:
    feed = client.rates.global_(symbols=["BRL", "EUR"])
```

> **Keep your API key server-side.** It is sent only as the `X-API-Key` header.
> Never ship it in a browser bundle, a mobile app or any public client.

## Authentication

Pass the key explicitly or let the client read it from the environment:

```python
client = Cotizave(api_key="ctz_live_...")  # explicit
client = Cotizave()  # from COTIZAVE_API_KEY
```

## What you can do

| Area | Call |
| --- | --- |
| Rates of a country | `client.rates.list("CO")` |
| One rate by id | `client.rates.get("CO", "co-trm")` |
| Past board of a country | `client.rates.snapshot("AR", "2026-10-01")` |
| Official rate of every country | `client.rates.global_(symbols=["BRL", "EUR"])` |
| Convert one amount | `client.convert(from_="USD", to="BRL", amount=100)` |
| Convert up to 50 amounts | `client.convert_bulk([...])` |
| Point-in-time history | `client.history.get("CO", "co-trm", "2026-10-01")` |
| Daily history series | `client.history.daily("AR", "ar-official", from_="2026-09-01", to="2026-09-30")` |
| Period statistics | `client.history.stats("AR", "ar-official", from_="...", to="...", moving_average=7)` |
| Raw captures (paginated) | `client.history.raw(...)` / `client.history.iterate(...)` |
| History coverage | `client.history.limits()` |
| Rate catalog | `client.markets("VE")` |
| Spread vs another market | `client.spread("VE", against="ve-paralelo")` |
| Best executable route | `client.route("VE", from_="USD", to="VES", amount=100)` |
| Bank-published rates | `client.bank_rates("VE")` |
| Countries / currencies | `client.countries.list()` · `client.currencies.list()` |
| Banks / issuers | `client.banks.list("VE")` · `client.issuers.list()` |
| Holidays & business days | `client.holidays.list("AR")` · `client.holidays.business_days("VE", from_="2026-10-01", days=5)` |
| Stablecoins (USD) | `client.crypto.list()` · `client.crypto.get("usdt-usd")` |

Responses are plain `dict`s, typed with `TypedDict` for editor completion. The
fields present depend on your plan, the country and the market — read them with
`.get(...)` and check the [API reference](https://docs.cotizave.com/api/v2/introduction).

### Iterating raw history safely

```python
for point in client.history.iterate("VE", "ve-bcv", max_pages=10):
    print(point["date"], point.get("mid"))
```

`iterate` follows the server's cursors for you and stops at `max_pages`
(default 50) so it never silently downloads an entire history.

## Errors

Every failure raises a subclass of `CotizaveError`. Catch the base class for any
API error, or a specific subclass for a family:

```python
from cotizave import Cotizave, RateLimitError, NotFoundError, CotizaveError

client = Cotizave()
try:
    rate = client.rates.get("CO", "co-trm")
except RateLimitError as err:
    if err.is_quota_exhausted:
        print("Monthly quota exhausted")
    else:
        print(f"Slow down; retry after {err.retry_after}s")
except NotFoundError:
    print("No such rate")
except CotizaveError as err:
    print(err.status, err.code, err.message)
```

| Exception | HTTP |
| --- | --- |
| `BadRequestError` | 400 |
| `AuthenticationError` | 401 |
| `FeatureNotInPlanError` | 402 |
| `ForbiddenError` | 403 |
| `NotFoundError` | 404 |
| `NotAcceptableError` | 406 |
| `UnprocessableError` | 422 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | no response (network/timeout) |

Each error carries `status`, `code`, `message`, optional `field`/`details`, and
`rate_limit` / `headers` / `request_id` from the response.

## Configuration

Everything has a production-safe default; override only what you need:

```python
from cotizave import Cotizave, RetryOptions

client = Cotizave(
    api_key="ctz_live_...",
    timeout=5.0,  # per-request timeout, seconds
    history_timeout=10.0,  # longer timeout for history reads
    max_retries=2,  # extra retries for eligible requests
    max_retry_delay=10.0,  # total backoff budget per call, seconds
    max_response_bytes=25_000_000,
    language="es",  # Accept-Language for localized names
    headers={"X-Trace-Id": "..."},
    retry=RetryOptions(
        base_delay=0.25,
        max_delay=2.0,
        retry_rate_limited=True,
        on_retry=lambda e: print("retrying", e.path, "in", e.delay, "s"),
    ),
    on_response=lambda e: print(e.meta.status, e.meta.rate_limit.remaining),
)
```

Per-call overrides are accepted on every method (`timeout`, `max_retries`,
`headers`, `language`):

```python
client.rates.list("AR", timeout=2.0, max_retries=0)
```

### Retry policy

Only idempotent (GET) requests are retried. A `429` is retried only when it is a
burst (per-minute) limit, honoring the server's `Retry-After`; a `429` from an
exhausted monthly quota is never retried. Connection and timeout errors, and the
configured 5xx statuses, are retried with exponential backoff and full jitter,
bounded by `max_retries` and the `max_retry_delay` budget.

## Exporting CSV / XML

```python
csv = client.export("/v2/fx/ar/rates", format="csv")
```

## Low-level requests

For anything the typed resources don't cover, including conditional GETs and
response metadata:

```python
result = client.request(method="GET", path="/v2/fx/co/rates/co-trm", if_none_match='"abc"')
print(result.not_modified, result.meta.status, result.data)
```

## Security

- The API key is sent only as the `X-API-Key` header and is never exposed on
  `client.config`, in `repr()` or when logging the client.
- Every request is pinned to the configured origin; a path that resolves to a
  different host is refused, and redirects are never followed — so the key
  cannot leak to another origin.
- Response bodies are capped at `max_response_bytes` to guard against an
  oversized or decompression-bomb response.

Found a security issue? See [SECURITY.md](./SECURITY.md).

## License

[MIT](./LICENSE)
