from __future__ import annotations

import httpx
import pytest
import respx

from cotizave import Cotizave

BASE = "https://api.cotizave.com"


@pytest.fixture
def client():
    c = Cotizave(api_key="ctz_test_key", max_retry_delay=5.0)
    yield c
    c.close()


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


__all__ = ["BASE", "httpx"]
