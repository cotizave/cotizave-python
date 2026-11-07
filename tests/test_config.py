from __future__ import annotations

import pytest

from cotizave import Cotizave, RetryOptions


def test_requires_api_key():
    with pytest.raises(ValueError):
        Cotizave(api_key="")
    with pytest.raises(ValueError):
        Cotizave(api_key=None)


def test_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("COTIZAVE_API_KEY", "ctz_env_key")
    with Cotizave() as c:
        assert c.config.base_url == "https://api.cotizave.com"


def test_public_config_hides_api_key():
    with Cotizave(api_key="ctz_secret") as c:
        assert "ctz_secret" not in repr(c.config)
        assert not hasattr(c.config, "api_key")


def test_http_base_url_requires_opt_in():
    with pytest.raises(ValueError):
        Cotizave(api_key="x", base_url="http://localhost:8080")
    # explicit opt-in is allowed
    with Cotizave(api_key="x", base_url="http://localhost:8080", allow_insecure_http=True) as c:
        assert c.config.base_url == "http://localhost:8080"


def test_invalid_base_url():
    with pytest.raises(ValueError):
        Cotizave(api_key="x", base_url="not a url")


def test_base_url_trailing_slash_stripped():
    with Cotizave(api_key="x", base_url="https://api.cotizave.com/") as c:
        assert c.config.base_url == "https://api.cotizave.com"


def test_reserved_header_rejected():
    with pytest.raises(TypeError):
        Cotizave(api_key="x", headers={"X-API-Key": "sneaky"})


def test_control_characters_in_header_rejected():
    with pytest.raises(TypeError):
        Cotizave(api_key="x", headers={"X-Trace": "a\r\nInjected: y"})


def test_invalid_header_name_rejected():
    with pytest.raises(TypeError):
        Cotizave(api_key="x", headers={"bad header": "v"})


def test_negative_timeout_rejected():
    with pytest.raises((ValueError, TypeError)):
        Cotizave(api_key="x", timeout=-1)


def test_user_agent_appended():
    with Cotizave(api_key="x", user_agent="acme/1.2.3") as c:
        assert c.config.user_agent.endswith("acme/1.2.3")
        assert c.config.user_agent.startswith("cotizave-python/")


def test_retry_options_accepted():
    with Cotizave(api_key="x", retry=RetryOptions(base_delay=0.1, max_delay=0.5)) as c:
        assert c.config.max_retries == 2
