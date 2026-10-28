"""Tests for the report-generation drivers."""

from __future__ import annotations

import pytest

from midea_lua_conformance.run import iter_pairs, main


def test_iter_pairs_rejects_negative_limit() -> None:
    """A negative limit would silently drop the last lua files of each type."""
    with pytest.raises(ValueError, match="limit_per_dir must be >= 0"):
        iter_pairs(limit_per_dir=-1)


def test_iter_pairs_zero_limit_yields_nothing() -> None:
    """Zero is a valid limit and compares no files."""
    assert iter_pairs(limit_per_dir=0) == []


def test_cli_rejects_negative_limit(capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI refuses a negative limit before writing any report."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--limit-per-dir", "-1"])
    assert exc_info.value.code == 2
    assert "must be >= 0" in capsys.readouterr().err
