"""Historical reads: point-in-time, daily series, raw captures, and coverage."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Optional

from ..types import (
    HistoricalLimitsResponse,
    HistoryCollection,
    HistoryPoint,
    HistoryPointRow,
    HistoryStatsResponse,
)
from ._base import Resource, cc, seg


class HistoryResource(Resource):
    def _path(self, country: str, rate_id: str) -> str:
        return f"/v2/fx/{cc(country)}/rates/{seg(rate_id, 'rate id')}/history"

    def _timeout(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._transport.history_timeout

    def get(
        self,
        country: str,
        rate_id: str,
        date: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HistoryPoint:
        """The rate that ruled on a specific day.

        Example::

            point = client.history.get("CO", "co-trm", "2026-10-01")
        """
        return self._transport.get(
            self._path(country, rate_id),
            {"date": date},
            timeout=self._timeout(timeout),
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def daily(
        self,
        country: str,
        rate_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HistoryCollection:
        """A daily series between ``from_`` and ``to``.

        Example::

            series = client.history.daily("AR", "ar-official", from_="2026-09-01", to="2026-09-30")
        """
        return self._transport.get(
            self._path(country, rate_id),
            {"granularity": "daily", "from": from_, "to": to},
            timeout=self._timeout(timeout),
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def stats(
        self,
        country: str,
        rate_id: str,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        moving_average: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HistoryStatsResponse:
        """Aggregates of a date range, computed by Cotizave over the daily closes.

        Example::

            result = client.history.stats(
                "AR", "ar-official", from_="2026-09-01", to="2026-09-30", moving_average=7
            )
        """
        return self._transport.get(
            self._path(country, rate_id),
            {"stats": 1, "from": from_, "to": to, "ma": moving_average},
            timeout=self._timeout(timeout),
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def raw(
        self,
        country: str,
        rate_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HistoryCollection:
        """One page of raw (intraday) captures. Pass the previous page's ``next_cursor``."""
        return self._transport.get(
            self._path(country, rate_id),
            {"granularity": "raw", "cursor": cursor, "limit": limit},
            timeout=self._timeout(timeout),
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def iterate(
        self,
        country: str,
        rate_id: str,
        *,
        limit: Optional[int] = None,
        max_pages: int = 50,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> Iterator[HistoryPointRow]:
        """Iterator over raw captures, following cursors for you.

        Bounded by ``max_pages`` (default 50) so it never silently downloads an
        entire history. Break out of the loop at any time to stop fetching.

        Example::

            for point in client.history.iterate("VE", "ve-bcv"):
                print(point["date"], point.get("mid"))
        """
        cursor: Optional[str] = None
        for _ in range(max_pages):
            page = self.raw(
                country,
                rate_id,
                cursor=cursor,
                limit=limit,
                timeout=timeout,
                max_retries=max_retries,
                headers=headers,
                language=language,
            )
            yield from page.get("points", [])
            cursor = page.get("next_cursor")
            if not cursor:
                return

    def limits(
        self,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HistoricalLimitsResponse:
        """Coverage (first/last/days) of the stored history for every rate the plan can see."""
        return self._transport.get(
            "/v2/fx/historical-limits",
            timeout=self._timeout(timeout),
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
