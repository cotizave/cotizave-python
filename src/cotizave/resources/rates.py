"""Exchange-rate reads: per-country list, single rate by id, and the global feed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import List, Optional, Union

from ..types import (
    GlobalRatesList,
    Rate,
    RateCategory,
    RatesResponse,
    RatesSnapshotResponse,
)
from ._base import Resource, cc, seg


class RatesResource(Resource):
    def list(
        self,
        country: str,
        *,
        tag: Optional[str] = None,
        category: Optional[RateCategory] = None,
        base: Optional[str] = None,
        quote: Optional[str] = None,
        markup: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> RatesResponse:
        """List every rate published for a country.

        Example::

            response = client.rates.list("AR")
            for rate in response["rates"]:
                print(rate["id"], rate.get("mid"))
        """
        return self._transport.get(
            f"/v2/fx/{cc(country)}/rates",
            {"tag": tag, "category": category, "base": base, "quote": quote, "markup": markup},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def get(
        self,
        country: str,
        rate_id: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Rate:
        """Fetch one rate by its canonical id.

        Example::

            trm = client.rates.get("CO", "co-trm")
        """
        return self._transport.get(
            f"/v2/fx/{cc(country)}/rates/{seg(rate_id, 'rate id')}",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def snapshot(
        self,
        country: str,
        date: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> RatesSnapshotResponse:
        """The full board of a country as it closed on a past day (subject to retention).

        Example::

            board = client.rates.snapshot("AR", "2026-10-01")
        """
        return self._transport.get(
            f"/v2/fx/{cc(country)}/rates",
            {"date": seg(date, "date")},
            timeout=timeout if timeout is not None else self._transport.history_timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def global_(
        self,
        *,
        symbols: Optional[Union[List[str], str]] = None,
        base: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> GlobalRatesList:
        """The official rate of every published country in a single call.

        Example::

            feed = client.rates.global_(symbols=["BRL", "EUR"])
        """
        joined = ",".join(symbols) if isinstance(symbols, (list, tuple)) else symbols
        return self._transport.get(
            "/v2/fx/rates",
            {"symbols": joined, "base": base},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
