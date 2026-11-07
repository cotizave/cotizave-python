"""Reference-data catalogs: countries, currencies, banks and issuers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from ..types import (
    Bank,
    BanksList,
    CountriesList,
    Country,
    CurrenciesList,
    Currency,
    IssuersResponse,
)
from ._base import Resource, cc, seg


class CountriesResource(Resource):
    """Country catalog (Pro+)."""

    def list(
        self,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> CountriesList:
        """List published countries (``{ "countries": [...] }``)."""
        return self._transport.get(
            "/v2/countries",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def get(
        self,
        country: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Country:
        """One published country by code."""
        return self._transport.get(
            f"/v2/countries/{cc(country)}",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )


class CurrenciesResource(Resource):
    """Currency catalog (Pro+)."""

    def list(
        self,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> CurrenciesList:
        """List currencies Cotizave quotes (``{ "currencies": [...] }``)."""
        return self._transport.get(
            "/v2/currencies",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def get(
        self,
        code: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Currency:
        """One currency by code (e.g. ``USD``)."""
        return self._transport.get(
            f"/v2/currencies/{seg(code, 'currency code')}",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )


class BanksResource(Resource):
    """Bank identities (no prices)."""

    def list(
        self,
        country: str,
        *,
        q: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> BanksList:
        """List a country's banks (``{ "banks": [...] }``); optional free-text search via ``q``."""
        return self._transport.get(
            f"/v2/banks/{cc(country)}",
            {"q": q},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def get(
        self,
        country: str,
        code: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Bank:
        """One bank by its official code (SUDEBAN in VE)."""
        return self._transport.get(
            f"/v2/banks/{cc(country)}/{seg(code, 'bank code')}",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )


class IssuersResource(Resource):
    """Official-rate issuers directory (all plans)."""

    def list(
        self,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> IssuersResponse:
        """List the institutions that issue official rates."""
        return self._transport.get(
            "/v2/issuers",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
