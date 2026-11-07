"""Shared base for resource groups: holds the transport and small helpers."""

from __future__ import annotations

from urllib.parse import quote

from .._transport import Transport


class Resource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport


def cc(code: str) -> str:
    """Normalize an ISO-3166 alpha-2 country code (the API is case-insensitive)."""
    if not isinstance(code, str) or code.strip() == "":
        raise TypeError('A country code (ISO 3166 alpha-2, e.g. "AR") is required.')
    return quote(code.strip().lower(), safe="")


def seg(value: str, label: str) -> str:
    """Encode a single path segment (rate id, bank code, currency code)."""
    if not isinstance(value, str) or value.strip() == "":
        raise TypeError(f"A {label} is required.")
    return quote(value.strip(), safe="")
