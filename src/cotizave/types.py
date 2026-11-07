"""Typed shapes of the Cotizave API v2 responses.

These mirror the OpenAPI v2 contract. Responses are returned as plain ``dict``\\s
at runtime; the :class:`~typing.TypedDict`\\s here exist for editor completion and
static checking only — nothing is validated or coerced. Every field is optional
(``total=False``) because the fields actually present depend on the plan, the
country and the market.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 11):  # pragma: no cover - version shim
    from typing import Literal, TypedDict
else:  # pragma: no cover
    from typing import TypedDict

    try:
        from typing import Literal
    except ImportError:  # 3.7 fallback, not expected
        Literal = Any  # type: ignore

RateType = Literal[
    "reference",
    "interbank",
    "parallel",
    "securities",
    "p2p",
    "crypto_exchange",
    "bank_board",
    "cash",
    "remittance",
    "card",
    "exchange_house",
    "crypto",
]

RateCategory = Literal[
    "official",
    "interbank",
    "parallel",
    "securities",
    "crypto_p2p",
    "crypto_exchange",
    "bank_board",
    "cash",
    "remittance",
    "card",
    "exchange_house",
    "crypto",
]

RequiredPlan = Literal["free", "hobby", "indie", "pro", "pro_extra"]

StablecoinId = Literal["usdt-usd", "usdc-usd", "eurc-usd"]

Granularity = Literal["daily", "raw"]


class ApiErrorBody(TypedDict, total=False):
    """Raw error body returned by the API."""

    code: str
    message: str
    field: str
    details: Dict[str, Any]


class GeoFields(TypedDict, total=False):
    """Country-level fields embedded in several responses (geography is Pro+)."""

    country: str
    currency: str
    continent: str
    country_name: str
    flag: str
    region: str
    region_code: str
    timezone: str


class Rate(GeoFields, total=False):
    """Canonical exchange-rate reference (fields present depend on plan and market)."""

    id: str
    mid: float
    type: RateType
    market: str
    updated_at: str
    ask: Optional[float]
    bid: Optional[float]
    base: str
    quote: str
    name: str
    description: str
    available: bool
    change_24h_pct: Optional[float]
    effective_date: str
    fetched_at: str
    required_plan: RequiredPlan
    stale: bool
    stale_after_sec: float
    staleness_sec: float
    tags: List[str]
    vs_official_pct: Optional[float]


class RateDescriptor(TypedDict, total=False):
    """A restricted VE rate shown without a price (descriptor only)."""

    id: str
    available: bool
    base: str
    description: str
    market: str
    name: str
    quote: str
    required_plan: RequiredPlan
    tags: List[str]
    type: RateType


class RatesResponse(GeoFields, total=False):
    """Response of ``rates.list(cc)``."""

    base: str
    fetched_at: str
    plan: str
    index: Dict[str, Any]
    rates: List[Rate]  # may also contain RateDescriptor entries (VE restricted)


class RatesSnapshotRow(TypedDict, total=False):
    """Close of one rate on a past date (a row of ``rates.snapshot``)."""

    id: str
    market: str
    mid: float
    type: RateType
    updated_at: str
    ask: float
    bid: float


class RatesSnapshotResponse(GeoFields, total=False):
    """The full board of a country on a past date (``rates.snapshot``)."""

    base: str
    count: int
    date: str
    rates: List[RatesSnapshotRow]


class GlobalRateRow(TypedDict, total=False):
    """A single row of the global officials endpoint (``rates.global``)."""

    country: str
    id: str
    mid: float
    quote: str
    stale: bool
    stale_after_sec: float
    updated_at: str


class GlobalRatesList(TypedDict, total=False):
    """Response of ``rates.global``."""

    base: str
    count: int
    date: str
    rates: List[GlobalRateRow]


class HistoryPointRow(TypedDict, total=False):
    """One point inside a history collection."""

    date: str
    mid: float
    fetched_at: str
    updated_at: str
    ask: float
    bid: float
    captured_at: str
    rate: float


class HistoryPoint(TypedDict, total=False):
    """One historical data point (``history.get`` with a ``date``)."""

    id: str
    base: str
    quote: str
    market: str
    date: str
    mid: float
    fetched_at: str
    updated_at: str
    ask: float
    bid: float
    captured_at: str
    rate: float


HistoryCollection = TypedDict(
    "HistoryCollection",
    {
        "base": str,
        "count": int,
        "from": str,
        "to": str,
        "granularity": Granularity,
        "id": str,
        "market": str,
        "quote": str,
        "next_cursor": Optional[str],
        "points": List[HistoryPointRow],
        "truncated": bool,
    },
    total=False,
)
"""A daily or raw history series (``history.daily`` / ``history.raw``)."""


class HistoryStatsPoint(TypedDict, total=False):
    date: str
    mid: float


class HistoryStats(TypedDict, total=False):
    """Aggregates of a period (min, max, avg, moving averages...)."""

    avg: float
    change: float
    change_pct: float
    count: int
    first: HistoryStatsPoint
    last: HistoryStatsPoint
    max: float
    min: float
    stddev: float
    ema: float
    sma: float
    period: int
    vs_ema_pct: float
    vs_sma_pct: float


HistoryStatsResponse = TypedDict(
    "HistoryStatsResponse",
    {
        "base": str,
        "from": str,
        "to": str,
        "granularity": str,
        "id": str,
        "market": str,
        "quote": str,
        "stats": HistoryStats,
    },
    total=False,
)
"""Response of ``history.stats(...)``."""


class HistoricalLimitRow(TypedDict, total=False):
    """Coverage window of a rate's stored history."""

    base: str
    country: str
    days: int
    first: str
    id: str
    last: str
    quote: str


class HistoricalLimitsResponse(TypedDict, total=False):
    """Response of ``history.limits()``."""

    base: str
    count: int
    limits: List[HistoricalLimitRow]


class Amount(TypedDict, total=False):
    """A converted amount."""

    amount: float
    currency: str


ConvertResponse = TypedDict(
    "ConvertResponse",
    {
        "from": Amount,
        "to": Amount,
        "rate": float,
        "market": str,
        "via": str,
        "type": RateType,
        "stale": bool,
        "staleness_sec": float,
        "updated_at": str,
        "date": str,
        "effective_date": str,
    },
    total=False,
)
"""Response of a single ``convert(...)``."""


class BulkConvertItem(TypedDict, total=False):
    """One entry of a bulk conversion result."""

    index: int
    conversion: ConvertResponse
    error: ApiErrorBody


class BulkConvertResponse(TypedDict, total=False):
    """Response of ``convert_bulk(...)``."""

    count: int
    succeeded: int
    failed: int
    results: List[BulkConvertItem]


ConversionDirection = TypedDict(
    "ConversionDirection",
    {"from": str, "to": str},
    total=False,
)


class MarketEntry(TypedDict, total=False):
    """Catalog entry from ``markets(cc)``."""

    id: str
    name: str
    market: str
    base: str
    quote: str
    type: RateType
    available: bool
    required_plan: RequiredPlan
    stale_after_sec: float
    tags: List[str]
    aliases: List[str]
    conversion_directions: List[ConversionDirection]


class MarketsCatalog(TypedDict, total=False):
    """Response of ``markets(cc)`` — ``{ country, markets }``."""

    country: str
    markets: List[MarketEntry]


class SpreadQuote(TypedDict, total=False):
    """A quote inside a spread response."""

    id: str
    market: str
    updated_at: str
    value: float


class SpreadDelta(TypedDict, total=False):
    absolute: float
    direction: str
    percentage: float


class SpreadResponse(TypedDict, total=False):
    """Response of ``spread(cc, ...)``."""

    country: str
    fetched_at: str
    reference: SpreadQuote
    compared: SpreadQuote
    spread: SpreadDelta


class RouteOption(TypedDict, total=False):
    """A single executable option inside a route response."""

    id: str
    market: str
    amount: float
    rate: float
    type: RateType
    staleness_sec: float
    updated_at: str


class RouteSkipped(TypedDict, total=False):
    id: str
    market: str
    reason: str


RouteResponse = TypedDict(
    "RouteResponse",
    {
        "country": str,
        "direction": str,
        "fetched_at": str,
        "from": Amount,
        "best": RouteOption,
        "alternatives": List[RouteOption],
        "skipped": List[RouteSkipped],
    },
    total=False,
)
"""Response of ``route(cc, ...)``."""


class BankRef(TypedDict, total=False):
    code: Optional[str]
    name: str


class BankRate(TypedDict, total=False):
    """A single BCV-published bank quotation."""

    bank: BankRef
    base: str
    quote: str
    mid: float
    ask: Optional[float]
    bid: Optional[float]
    days_behind: int
    effective_date: str
    stale: bool
    stale_after_sec: float
    staleness_sec: float
    updated_at: str
    vs_official_pct: Optional[float]


class BankRatesResponse(TypedDict, total=False):
    """Response of ``bank_rates(cc)``."""

    country: str
    currency: str
    indicator_date: str
    banks: List[BankRate]


class Country(TypedDict, total=False):
    """Country catalog entry."""

    code: str
    continent: str
    currency: str
    flag: str
    name: str
    rates: List[str]
    region: str
    region_code: str
    timezone: str


class CountriesList(TypedDict, total=False):
    """Response of ``countries.list()`` — ``{ countries }``."""

    countries: List[Country]


class Currency(TypedDict, total=False):
    """Currency catalog entry (ISO 4217)."""

    code: str
    minor_unit: int
    name: str
    numeric_code: str
    symbol: str


class CurrenciesList(TypedDict, total=False):
    """Response of ``currencies.list()`` — ``{ currencies }``."""

    currencies: List[Currency]


class Bank(TypedDict, total=False):
    """Bank identity entry."""

    bank_rates: Optional[str]
    code: str
    country: str
    name: str
    type: Optional[str]


class BanksList(TypedDict, total=False):
    """Response of ``banks.list(cc)`` — ``{ banks }``."""

    banks: List[Bank]


class IssuerJurisdiction(TypedDict, total=False):
    countries: List[str]
    currency: str


class IssuerLinks(TypedDict, total=False):
    website: str


class IssuerPublishes(TypedDict, total=False):
    label: str
    rate_id: str
    pair: str
    schedule: str
    source: str
    status: str
    value_date: str


class Issuer(TypedDict, total=False):
    """An official-rate issuing institution."""

    id: str
    name: str
    short_name: str
    kind: str
    jurisdiction: IssuerJurisdiction
    links: IssuerLinks
    publishes: List[IssuerPublishes]
    timezone: str


class IssuersSummary(TypedDict, total=False):
    countries: int
    issuers: int


class IssuerWithout(TypedDict, total=False):
    country: str
    rate_id: str
    reason: str
    status: str


class IssuersResponse(TypedDict, total=False):
    """Response of ``issuers.list()``."""

    issuers: List[Issuer]
    summary: IssuersSummary
    without_issuer: List[IssuerWithout]


Holiday = TypedDict(
    "Holiday",
    {
        "date": str,
        "name": str,
        "local_name": str,
        "fixed": bool,
        "global": bool,
        "type": str,
        "types": List[str],
    },
    total=False,
)
"""A public holiday."""


class HolidaysYear(TypedDict, total=False):
    """Year-mode holidays response."""

    country: str
    year: int
    holidays: List[Holiday]


class HolidayCheck(TypedDict, total=False):
    """Is-holiday response."""

    country: str
    date: str
    is_holiday: bool
    holiday: Optional[Holiday]


NextHoliday = TypedDict(
    "NextHoliday",
    {
        "country": str,
        "from": str,
        "days_until": int,
        "holiday": Holiday,
    },
    total=False,
)
"""Next-holiday response."""


BusinessDaysResult = TypedDict(
    "BusinessDaysResult",
    {
        "country": str,
        "from": str,
        "days": int,
        "result": str,
    },
    total=False,
)
"""Business-days response."""


class CryptoList(TypedDict, total=False):
    """The stablecoin feed — ``{ base, fetched_at, plan, rates }``."""

    base: str
    fetched_at: str
    plan: str
    rates: List[Rate]
