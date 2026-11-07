"""The Cotizave API v2 client."""

from __future__ import annotations

import os
from collections.abc import Mapping
from types import TracebackType
from typing import Any, List, Optional, Type

import httpx

from ._transport import RawResult, Transport
from .config import (
    API_KEY_ENV_VAR,
    DEFAULT_BASE_URL,
    DEFAULT_HISTORY_TIMEOUT,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    PublicConfig,
    RetryOptions,
    resolve_config,
)
from .resources import (
    BanksResource,
    ConversionResource,
    CountriesResource,
    CryptoResource,
    CurrenciesResource,
    FxToolsResource,
    HistoryResource,
    HolidaysResource,
    IssuersResource,
    RatesResource,
)
from .types import (
    BankRatesResponse,
    BulkConvertResponse,
    ConvertResponse,
    MarketsCatalog,
    RouteResponse,
    SpreadResponse,
)


class Cotizave:
    """The Cotizave API v2 client.

    Example::

        from cotizave import Cotizave

        client = Cotizave()  # reads COTIZAVE_API_KEY from the environment
        response = client.rates.list("AR")
        trm = client.rates.get("CO", "co-trm")
        result = client.convert(from_="USD", to="BRL", amount=100)

    The client holds a pooled HTTP connection. Reuse one instance, and call
    :meth:`close` (or use it as a context manager) when done.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        history_timeout: float = DEFAULT_HISTORY_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        retry: Optional[RetryOptions] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
        user_agent: Optional[str] = None,
        allow_insecure_http: bool = False,
        on_response: Optional[Any] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if api_key is None:
            api_key = os.environ.get(API_KEY_ENV_VAR)
        resolved = resolve_config(
            api_key=api_key,  # type: ignore[arg-type]
            base_url=base_url,
            timeout=timeout,
            history_timeout=history_timeout,
            max_retries=max_retries,
            max_retry_delay=max_retry_delay,
            max_response_bytes=max_response_bytes,
            retry=retry,
            headers=headers,
            language=language,
            user_agent=user_agent,
            allow_insecure_http=allow_insecure_http,
            on_response=on_response,
        )

        #: Resolved, validated configuration (read-only). The API key is left out,
        #: so logging or serializing the client never exposes it.
        self.config: PublicConfig = resolved.to_public()

        transport = Transport(resolved, http_client=http_client)
        self._transport = transport
        self._conversion = ConversionResource(transport)
        self._fx = FxToolsResource(transport)

        #: Per-country rate reads and the global officials feed.
        self.rates = RatesResource(transport)
        #: Point-in-time, daily and raw history, plus coverage limits.
        self.history = HistoryResource(transport)
        #: Published countries catalog (Pro+).
        self.countries = CountriesResource(transport)
        #: Currencies catalog (Pro+).
        self.currencies = CurrenciesResource(transport)
        #: Bank identities, with optional search.
        self.banks = BanksResource(transport)
        #: Official-rate issuers directory.
        self.issuers = IssuersResource(transport)
        #: Holiday calendars and business-day math.
        self.holidays = HolidaysResource(transport)
        #: Stablecoin references priced in USD.
        self.crypto = CryptoResource(transport)

    # -- convenience top-level operations -----------------------------------

    def convert(self, **kwargs: Any) -> ConvertResponse:
        """Convert a single amount. See :meth:`ConversionResource.convert`."""
        return self._conversion.convert(**kwargs)

    def convert_bulk(
        self, conversions: List[Mapping[str, Any]], **kwargs: Any
    ) -> BulkConvertResponse:
        """Convert up to 50 items in one call. See :meth:`ConversionResource.convert_bulk`."""
        return self._conversion.convert_bulk(conversions, **kwargs)

    def markets(self, country: str, **kwargs: Any) -> MarketsCatalog:
        """The country's rate catalog (no prices). Growth+."""
        return self._fx.markets(country, **kwargs)

    def spread(self, country: str, **kwargs: Any) -> SpreadResponse:
        """Spread of the official rate against another market. Growth+."""
        return self._fx.spread(country, **kwargs)

    def route(self, country: str, **kwargs: Any) -> RouteResponse:
        """Best executable rate for an amount. Pro+."""
        return self._fx.route(country, **kwargs)

    def bank_rates(self, country: str, **kwargs: Any) -> BankRatesResponse:
        """BCV per-bank quotations (all plans)."""
        return self._fx.bank_rates(country, **kwargs)

    # -- low-level escape hatches -------------------------------------------

    def request(self, *, method: str = "GET", path: str, **kwargs: Any) -> RawResult:
        """Low-level request with full response metadata (status, headers,
        rate-limit info) and support for conditional GETs (``if_none_match``) and
        non-JSON bodies (``parse="text"``). Most code should use the typed
        resources above.
        """
        return self._transport.request(method=method, path=path, **kwargs)

    def export(self, path: str, *, format: str, **query: Any) -> str:
        """Fetch a resource as CSV or XML and return the raw body text.

        Example::

            csv = client.export("/v2/fx/ar/rates", format="csv")
        """
        if format not in ("csv", "xml"):
            raise ValueError("export: `format` must be 'csv' or 'xml'.")
        accept = "text/csv" if format == "csv" else "application/xml"
        result = self._transport.request(
            method="GET",
            path=path,
            query={**query, "format": format},
            accept=accept,
            parse="text",
        )
        return result.data or ""

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._transport.close()

    def __enter__(self) -> Cotizave:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()
