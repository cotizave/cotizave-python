"""Conversion operations. The arithmetic runs on Cotizave, never in the SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from ..types import BulkConvertResponse, ConvertResponse
from ._base import Resource

#: The maximum number of conversions accepted by a single bulk request.
BULK_CONVERT_MAX = 50


class ConversionResource(Resource):
    def convert(
        self,
        *,
        from_: str,
        to: str,
        amount: float,
        via: Optional[str] = None,
        market: Optional[str] = None,
        date: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> ConvertResponse:
        """Convert one amount between two currencies.

        Example::

            result = client.convert(from_="USD", to="BRL", amount=100)
        """
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            raise TypeError("convert: `amount` must be a number greater than 0.")
        return self._transport.get(
            "/v2/fx/convert",
            {"from": from_, "to": to, "amount": amount, "via": via, "market": market, "date": date},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def convert_bulk(
        self,
        conversions: List[Mapping[str, Any]],
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> BulkConvertResponse:
        """Convert up to 50 items in one request (Pro+). Counts as a single query.

        Each item is a mapping with ``from``/``to``/``amount`` (and optional
        ``via``/``date``). Results keep their input order and carry either a
        ``conversion`` or an ``error`` — a failed item never silently drops.

        Example::

            result = client.convert_bulk([
                {"from": "USD", "to": "ARS", "amount": 100},
                {"from": "USD", "to": "COP", "amount": 250},
            ])
        """
        if not isinstance(conversions, (list, tuple)) or len(conversions) == 0:
            raise TypeError("convert_bulk: `conversions` must be a non-empty list.")
        if len(conversions) > BULK_CONVERT_MAX:
            raise TypeError(
                f"convert_bulk: at most {BULK_CONVERT_MAX} conversions are allowed "
                f"(got {len(conversions)})."
            )
        body: Dict[str, Any] = {"conversions": list(conversions)}
        return self._transport.post(
            "/v2/fx/convert",
            body,
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
