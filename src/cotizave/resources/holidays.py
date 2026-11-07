"""Holiday calendars and business-day math (Basic+ in v2)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from ..types import BusinessDaysResult, HolidayCheck, HolidaysYear, NextHoliday
from ._base import Resource, cc


class HolidaysResource(Resource):
    def list(
        self,
        country: str,
        *,
        year: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HolidaysYear:
        """Holidays for a year (defaults to the current year server-side).

        Example::

            response = client.holidays.list("AR", year=2026)
        """
        return self._transport.get(
            f"/v2/holidays/{cc(country)}",
            {"year": year},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def check(
        self,
        country: str,
        date: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> HolidayCheck:
        """Whether a given date is a holiday."""
        return self._transport.get(
            f"/v2/holidays/{cc(country)}",
            {"date": date},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def next(
        self,
        country: str,
        from_: str,
        *,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> NextHoliday:
        """The next holiday on or after ``from_``."""
        return self._transport.get(
            f"/v2/holidays/{cc(country)}",
            {"from": from_},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )

    def business_days(
        self,
        country: str,
        *,
        days: int,
        from_: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> BusinessDaysResult:
        """The date reached by adding ``days`` business days to ``from_``.

        Example::

            result = client.holidays.business_days("VE", from_="2026-10-01", days=5)
        """
        if isinstance(days, bool) or not isinstance(days, int) or days < 0:
            raise TypeError("business_days: `days` must be a non-negative integer.")
        return self._transport.get(
            f"/v2/holidays/{cc(country)}/business-days",
            {"from": from_, "days": days},
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
            language=language,
        )
