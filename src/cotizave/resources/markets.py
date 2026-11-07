"""Advanced per-country FX tools: catalog, spread, best route, bank rates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from ..types import BankRatesResponse, MarketsCatalog, RouteResponse, SpreadResponse
from ._base import Resource, cc


class FxToolsResource(Resource):
    def markets(
        self,
        country: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> MarketsCatalog:
        """The country's rate catalog (no prices). Growth+."""
        return self._transport.get(
            f"/v2/fx/{cc(country)}/markets",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def spread(
        self,
        country: str,
        *,
        against: Optional[str] = None,
        base: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> SpreadResponse:
        """The spread of the official rate against another market. Growth+."""
        return self._transport.get(
            f"/v2/fx/{cc(country)}/spread",
            {"against": against, "base": base},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def route(
        self,
        country: str,
        *,
        from_: str,
        to: str,
        amount: float,
        direction: Optional[str] = None,
        max_staleness: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> RouteResponse:
        """The best executable rate for an amount. Pro+.

        The backend resolves the route — the SDK never computes it.
        """
        return self._transport.get(
            f"/v2/fx/{cc(country)}/route",
            {
                "from": from_,
                "to": to,
                "amount": amount,
                "direction": direction,
                "max_staleness": max_staleness,
            },
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def bank_rates(
        self,
        country: str,
        *,
        bank: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> BankRatesResponse:
        """BCV per-bank quotations (all plans). Optionally filtered by bank code."""
        return self._transport.get(
            f"/v2/fx/{cc(country)}/bank-rates",
            {"bank": bank},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
