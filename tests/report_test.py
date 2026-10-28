"""Tests for the midea-local description in the report header."""

from __future__ import annotations

import shutil
import subprocess
from importlib.metadata import version
from typing import TYPE_CHECKING

import pytest

from midea_lua_conformance.report import _git_checkout_summary, describe_midea_local

if TYPE_CHECKING:
    from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    assert git is not None
    return subprocess.run(  # noqa: S603 - fixed git arguments
        [git, "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """Create a midea-local-like checkout whose last merged PR is #956."""
    (tmp_path / "midealocal").mkdir()
    (tmp_path / "midealocal" / "device.py").write_text("x = 1\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "feat(fan)!: move fan options (#956)")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "Merge branch 'main'")
    return tmp_path


def test_git_checkout_summary(checkout: Path) -> None:
    """The commit and the latest PR found in the history are reported."""
    commit = _git(checkout, "rev-parse", "--short", "HEAD")
    assert _git_checkout_summary(checkout) == (
        f"{commit}, latest merged PR "
        "[#956](https://github.com/midea-lan/midea-local/pull/956)"
    )


def test_git_checkout_summary_local_changes(checkout: Path) -> None:
    """Uncommitted changes to midealocal are flagged."""
    (checkout / "midealocal" / "device.py").write_text("x = 2\n")
    commit = _git(checkout, "rev-parse", "--short", "HEAD")
    summary = _git_checkout_summary(checkout)
    assert summary is not None
    assert summary.startswith(f"{commit} + local changes, ")


def test_git_checkout_summary_not_a_checkout(tmp_path: Path) -> None:
    """A directory outside git yields no summary instead of failing."""
    assert _git_checkout_summary(tmp_path) is None


def test_describe_midea_local_reports_installed_version() -> None:
    """The installed midea-local version is always part of the description."""
    assert describe_midea_local().startswith(f"midea-local {version('midea-local')}")
