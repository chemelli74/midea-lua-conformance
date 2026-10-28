"""Render mappings and comparisons into human-readable reports.

Two renderers:

* :func:`render_mapping` -- the ``lua/`` <-> ``midealocal/devices`` table.
* :func:`render_report` -- a Markdown conformance report over a list of
  :class:`~midea_lua_conformance.compare.Comparison` objects: a summary table,
  then every ``MISSING`` / ``DIFFERENT`` finding in full, then a collapsed
  index of ``UNKNOWN`` items so nothing is hidden but the report stays short.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import distribution
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from urllib.request import url2pathname

from .compare import Verdict
from .mapping import MatchStatus

if TYPE_CHECKING:
    from .compare import Comparison, Finding
    from .mapping import DeviceMapping

_MIDEA_LOCAL_REPO = "https://github.com/midea-lan/midea-local"
# Squash-merged PRs end their subject with "(#123)".
_MERGED_PR = re.compile(r"\(#(\d+)\)$")

_INTRO = (
    "Verdicts: **MATCH** (agree) / **MISSING** (in Lua, not in midealocal) / "
    "**DIFFERENT** (both implement it, values disagree) / **UNKNOWN** "
    "(not auto-verifiable). A MISSING/DIFFERENT verdict is a *candidate* "
    "discrepancy, not a proven bug -- see README 'Interpreting failures'."
)


def _git_checkout_summary(checkout: Path) -> str | None:
    """Return the commit and latest merged PR of a midea-local git checkout."""
    if (git := shutil.which("git")) is None:
        return None

    def run(*args: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed git arguments
            [git, "-C", str(checkout), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    try:
        commit = run("rev-parse", "--short", "HEAD")
        subjects = run("log", "--format=%s", "-n", "500").splitlines()
        dirty = run("status", "--porcelain", "--", "midealocal")
    except subprocess.CalledProcessError:
        return None
    parts = [f"{commit} + local changes" if dirty else commit]
    pr = next((m[1] for s in subjects if (m := _MERGED_PR.search(s))), None)
    if pr is not None:
        parts.append(f"latest merged PR [#{pr}]({_MIDEA_LOCAL_REPO}/pull/{pr})")
    return ", ".join(parts)


def describe_midea_local() -> str:
    """Describe the installed midea-local the reports are generated against.

    A PyPI release is identified by its version alone; a local checkout or a
    git install also gets its commit, and a checkout its latest merged PR, since
    unreleased code still carries the previous release's version.
    """
    dist = distribution("midea-local")
    text = f"midea-local {dist.version}"
    direct_url = json.loads(dist.read_text("direct_url.json") or "{}")
    if commit := direct_url.get("vcs_info", {}).get("commit_id"):
        return f"{text} ({commit[:7]})"
    if "dir_info" in direct_url:
        checkout = Path(url2pathname(urlparse(direct_url["url"]).path))
        if summary := _git_checkout_summary(checkout):
            return f"{text} ({summary})"
    return text


def generated_line(generated_at: datetime | None, midea_local: str | None) -> str:
    """Return the first line of a report: when, and against which midea-local."""
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC)
    against = midea_local or describe_midea_local()
    return f"_Generated on {timestamp:%Y-%m-%d %H:%M:%S} UTC against {against}_"


def render_mapping(
    rows: list[DeviceMapping],
    *,
    generated_at: datetime | None = None,
    midea_local: str | None = None,
) -> str:
    """Render the device-type mapping as Markdown."""
    out: list[str] = [
        generated_line(generated_at, midea_local),
        "",
        "# LUA <-> midealocal mapping",
        "",
        "| device type | lua | midealocal | status | # lua files | evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    out.extend(
        f"| {row.key} | {row.lua_dir or '-'} | {row.py_package or 'UNMATCHED'} "
        f"| {row.status.value} | {len(row.lua_files)} | {'; '.join(row.evidence)} |"
        for row in sorted(rows, key=lambda r: (r.status.value, r.key))
    )
    summary = Counter(r.status for r in rows)
    matched_files = sum(
        len(r.lua_files) for r in rows if r.status is MatchStatus.MATCHED
    )
    out += ["", "## Summary", ""]
    out += [
        f"- {status.value}: {summary[status]}"
        for status in MatchStatus
        if summary[status]
    ]
    out.append(f"- lua files under mapped device types: {matched_files}")
    return "\n".join(out) + "\n"


def _summary_table(comparisons: list[Comparison]) -> list[str]:
    rows = [
        "| lua file | package | MATCH | MISSING | DIFFERENT | UNKNOWN |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    total: Counter[str] = Counter()
    for cmp in sorted(comparisons, key=lambda c: c.lua_source):
        counts = cmp.counts()
        total.update(counts)
        rows.append(
            f"| {cmp.lua_source} | {cmp.package} | {counts['MATCH']} "
            f"| {counts['MISSING']} | {counts['DIFFERENT']} | {counts['UNKNOWN']} |",
        )
    rows.append(
        f"| **total** | | {total['MATCH']} | {total['MISSING']} "
        f"| {total['DIFFERENT']} | {total['UNKNOWN']} |",
    )
    return rows


def _detail_blocks(pairs: list[tuple[Comparison, Finding]]) -> list[str]:
    if not pairs:
        return ["_none_", ""]
    out: list[str] = []
    for cmp, finding in pairs:
        out += [
            f"### {cmp.package}: {finding.name}",
            "",
            "```",
            str(finding),
            "```",
            "",
        ]
    return out


def render_report(
    comparisons: list[Comparison],
    *,
    title: str = "",
    generated_at: datetime | None = None,
    midea_local: str | None = None,
) -> str:
    """Render a full Markdown conformance report."""
    diff = [(c, f) for c in comparisons for f in c.by_verdict(Verdict.DIFFERENT)]
    missing = [(c, f) for c in comparisons for f in c.by_verdict(Verdict.MISSING)]

    out: list[str] = [
        generated_line(generated_at, midea_local),
        "",
        f"# {title or 'LUA protocol-conformance report'}",
        "",
        _INTRO,
        "",
        "## Summary",
        "",
        *_summary_table(comparisons),
        "",
        "## DIFFERENT",
        "",
        *_detail_blocks(diff),
        "## MISSING",
        "",
        *_detail_blocks(missing),
        "## UNKNOWN (collapsed)",
        "",
    ]
    for cmp in sorted(comparisons, key=lambda c: c.lua_source):
        unknown = cmp.by_verdict(Verdict.UNKNOWN)
        if not unknown:
            continue
        out.append(f"- **{cmp.lua_source}** ({len(unknown)}):")
        out += [f"  - {f.area}/{f.name}: {f.detail}" for f in unknown]
    out.append("")
    return "\n".join(out) + "\n"
