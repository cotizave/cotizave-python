"""Stablecoin references (USDT, USDC, EURC) priced in USD. Growth+."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from ..types import CryptoList, Rate, StablecoinId
from ._base import Resource, seg


class CryptoResource(Resource):
    def list(
        self,
        *,
        tag: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> CryptoList:
        """List the published stablecoins. Optional ``tag`` filter (e.g. ``usdt``)."""
        return self._transport.get(
            "/v2/crypto",
            {"tag": tag},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def get(
        self,
        crypto_id: StablecoinId,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Rate:
        """One stablecoin by its canonical id (e.g. ``usdt-usd``)."""
        return self._transport.get(
            f"/v2/crypto/{seg(crypto_id, 'crypto id')}",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
