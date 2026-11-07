from __future__ import annotations

import pathlib
import re

import cotizave


def test_version_matches_pyproject():
    root = pathlib.Path(__file__).resolve().parent.parent
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    # version is dynamic (read from _version.py), so assert the module value is
    # a valid semver and that _version.py is the declared source.
    assert re.match(r"^\d+\.\d+\.\d+", cotizave.__version__)
    assert 'path = "src/cotizave/_version.py"' in text


def test_retry_defaults_documented():
    # A light guard that defaults stay the published values.
    from cotizave.config import (
        DEFAULT_HISTORY_TIMEOUT,
        DEFAULT_MAX_RETRIES,
        DEFAULT_TIMEOUT,
    )

    assert DEFAULT_TIMEOUT == 5.0
    assert DEFAULT_HISTORY_TIMEOUT == 10.0
    assert DEFAULT_MAX_RETRIES == 2
