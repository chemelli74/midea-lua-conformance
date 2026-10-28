"""Write the discrepancies review from a run's findings.

Every ``MISSING``/``DIFFERENT`` finding is sorted into a review category by a
rule, then the decisions recorded in :mod:`.triage` override the category and
add a note. The result is ``DISCREPANCIES.md``, regenerated on every run so it
always describes the current midea-local and Lua corpus.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import cache
from typing import TYPE_CHECKING

from .compare import Comparison, Finding, Verdict
from .mapping import MatchStatus
from .py_introspect import introspect_device
from .report import generated_line
from .triage import DECISIONS, Category

if TYPE_CHECKING:
    from datetime import datetime

    from .ir import DecodeField
    from .mapping import DeviceMapping

# Enum names this similar differ by a letter or two, e.g. hot_steam/host_steam.
_TYPO_SIMILARITY = 0.85
_HIDDEN_ATTRIBUTE = (
    "midealocal exposes this attribute, but the framework cannot see where it is parsed"
)
_EQUIVALENT_SHIFT = "same bits: whole byte >> N vs (byte & top bits) >> N"
_INTRO = (
    "Every `MISSING` / `DIFFERENT` finding of "
    "[`REPORT.md`](REPORT.md), sorted into a category by rule "
    "and merged over the Lua files of each device type. Decisions recorded in "
    "`midea_lua_conformance/triage.py` override the rule and are marked "
    "**recorded**; add one there and regenerate to record a new decision."
)
_RESOLVED_INTRO = (
    "Recorded decisions whose finding no longer appears; delete them from "
    "`triage.py` once confirmed."
)

_TITLES = {
    Category.BUG: "A. Likely genuine midealocal bugs or gaps — worth an issue/PR",
    Category.VOCABULARY: "B. Different logical vocabulary — probably intentional",
    Category.OFFSET: "C. Byte-offset shifts — needs a protocol expert per device",
    Category.MASK: "D. Mask/bit differences on the same byte",
    Category.FRAMEWORK: (
        "E. Framework false positives / known limitations (do not act on these)"
    ),
    Category.COMMAND: "G. Requests the Lua builds that midealocal never sends",
    Category.UNPARSED: "H. Fields the Lua reads that midealocal does not parse",
}


@dataclass
class ReviewEntry:
    """One distinct finding of a device type, merged over its Lua files."""

    package: str
    finding: Finding
    category: Category
    reason: str
    recorded: bool
    lua_files: int = 1

    @property
    def key(self) -> tuple[str, str, str]:
        """Return the ``(package, area, name)`` key used by :mod:`.triage`."""
        return (self.package, self.finding.area, self.finding.name)


@cache
def _attributes(package: str) -> frozenset[str]:
    return introspect_device(package).attributes


def _classify_missing_decode(package: str, finding: Finding) -> tuple[Category, str]:
    if finding.name in _attributes(package):
        return Category.FRAMEWORK, _HIDDEN_ATTRIBUTE
    return Category.UNPARSED, "the Lua reads it; midealocal does not parse it"


def _classify_decode(package: str, finding: Finding) -> tuple[Category, str]:
    if finding.verdict is Verdict.MISSING:
        return _classify_missing_decode(package, finding)
    lua, py = finding.lua_field, finding.py_field
    if lua is None or py is None:
        return Category.BUG, finding.detail
    if lua.byte != py.byte:
        return Category.OFFSET, "read from a different byte"
    if (
        lua.mask == 0xFF
        and lua.shift == py.shift
        and py.mask == (0xFF << py.shift) & 0xFF
    ):
        return Category.FRAMEWORK, _EQUIVALENT_SHIFT
    return Category.MASK, "same byte, different mask or shift"


def classify(package: str, finding: Finding) -> tuple[Category, str]:
    """Return the rule-based category of a ``MISSING``/``DIFFERENT`` finding."""
    if finding.area == "decode_field":
        return _classify_decode(package, finding)
    if finding.area == "enum" and finding.verdict is Verdict.DIFFERENT:
        lua, py = finding.lua_label or "", finding.py_label or ""
        if SequenceMatcher(None, lua, py).ratio() >= _TYPO_SIMILARITY:
            return Category.BUG, "names differ by a letter or two: likely a typo"
        return Category.VOCABULARY, "same protocol value, different name"
    if finding.area == "enum":
        return Category.BUG, "the Lua defines a value midealocal has no name for"
    if finding.area == "command":
        return Category.COMMAND, "no midealocal message emits this body type"
    return Category.BUG, finding.detail


def build_review(comparisons: list[Comparison]) -> list[ReviewEntry]:
    """Classify and merge every ``MISSING``/``DIFFERENT`` finding of a run."""
    entries: dict[tuple[str, str, str], ReviewEntry] = {}
    for cmp in sorted(comparisons, key=lambda c: c.lua_source):
        for finding in cmp.findings:
            if finding.verdict not in (Verdict.MISSING, Verdict.DIFFERENT):
                continue
            key = (cmp.package, finding.area, finding.name)
            if (entry := entries.get(key)) is not None:
                entry.lua_files += 1
                continue
            if (decision := DECISIONS.get(key)) is not None:
                category, reason, recorded = decision.category, decision.note, True
            else:
                category, reason = classify(cmp.package, finding)
                recorded = False
            entries[key] = ReviewEntry(cmp.package, finding, category, reason, recorded)
    return sorted(entries.values(), key=lambda e: e.key)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _field(field: DecodeField | None) -> str:
    if field is None:
        return "-"
    return f"`byte[{field.byte}] & 0x{field.mask:02X} >> {field.shift}`"


def _sides(finding: Finding) -> tuple[str, str]:
    if finding.area == "enum":
        return (
            f"`{finding.lua_label}`" if finding.lua_label else finding.lua_repr or "-",
            f"`{finding.py_label}`" if finding.py_label else "-",
        )
    if finding.area == "decode_field":
        return _field(finding.lua_field), _field(finding.py_field)
    return finding.lua_repr or "-", finding.py_repr or "-"


def _why(entry: ReviewEntry) -> str:
    return f"**recorded:** {entry.reason}" if entry.recorded else entry.reason


def _table(entries: list[ReviewEntry]) -> list[str]:
    if not entries:
        return ["_none_", ""]
    out = [
        "| device | finding | Lua | midealocal | Lua files | why |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lua, py = _sides(entry.finding)
        why = _cell(_why(entry))
        out.append(
            f"| `{entry.package}` | {entry.finding.area} `{entry.finding.name}` "
            f"| {_cell(lua)} | {_cell(py)} | {entry.lua_files} | {why} |",
        )
    return [*out, ""]


def _offset_table(entries: list[ReviewEntry]) -> list[str]:
    by_package: dict[str, list[ReviewEntry]] = defaultdict(list)
    for entry in entries:
        by_package[entry.package].append(entry)
    if not by_package:
        return ["_none_", ""]
    out = [
        "| device | shift (midealocal - Lua) | fields | why |",
        "| --- | --- | --- | --- |",
    ]
    for package, rows in by_package.items():
        shifts: list[str] = []
        fields: list[str] = []
        for entry in rows:
            lua, py = entry.finding.lua_field, entry.finding.py_field
            if lua is None or py is None:
                continue
            shift = f"{py.byte - lua.byte:+d}"
            if shift not in shifts:
                shifts.append(shift)
            fields.append(f"`{entry.finding.name}` {lua.byte}→{py.byte}")
        recorded = [entry for entry in rows if entry.recorded]
        notes = sorted({_why(entry) for entry in recorded or rows})
        out.append(
            f"| `{package}` | {' / '.join(shifts)} | {', '.join(fields)} "
            f"| {_cell('; '.join(notes))} |",
        )
    return [*out, ""]


def _grouped_list(entries: list[ReviewEntry], *, with_reason: bool) -> list[str]:
    if not entries:
        return ["_none_", ""]
    groups: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        reason = _why(entry) if with_reason else ""
        groups[reason][entry.package].append(f"`{entry.finding.name}`")
    out: list[str] = []
    for reason, packages in groups.items():
        if reason:
            out += [reason if reason.startswith("**") else f"_{reason}_", ""]
        out += [
            f"- `{package}` ({len(names)}): {', '.join(names)}"
            for package, names in packages.items()
        ]
        out.append("")
    return out


def _coverage(comparisons: list[Comparison], mapping: list[DeviceMapping]) -> list[str]:
    unknown: dict[str, int] = defaultdict(int)
    for cmp in comparisons:
        for finding in cmp.by_verdict(Verdict.UNKNOWN):
            unknown[finding.area] += 1
    no_python = [r.key for r in mapping if r.status is MatchStatus.UNMATCHED_NO_PYTHON]
    no_lua = [r.key for r in mapping if r.status is MatchStatus.UNMATCHED_NO_LUA]
    return [
        "UNKNOWN findings (not auto-verifiable) by area: "
        + ", ".join(f"{area} {count}" for area, count in sorted(unknown.items())),
        "",
        f"- {len(no_python)} Lua device types have no midealocal package: "
        + (" ".join(f"`{key}`" for key in no_python) or "none"),
        f"- {len(no_lua)} midealocal packages have no Lua: "
        + (" ".join(f"`{key}`" for key in no_lua) or "none"),
        "",
    ]


def render_review(
    comparisons: list[Comparison],
    mapping: list[DeviceMapping],
    *,
    generated_at: datetime | None = None,
    midea_local: str | None = None,
) -> str:
    """Render ``DISCREPANCIES.md`` for a run."""
    entries = build_review(comparisons)
    by_category: dict[Category, list[ReviewEntry]] = defaultdict(list)
    for entry in entries:
        by_category[entry.category].append(entry)
    found = {entry.key for entry in entries}
    resolved = [
        (key, decision) for key, decision in DECISIONS.items() if key not in found
    ]
    totals = Comparison("", "")
    for cmp in comparisons:
        totals.findings.extend(cmp.findings)
    counts = totals.counts()
    scope = (
        f"Run scope: {len(comparisons)} comparisons. Totals — MATCH "
        f"{counts['MATCH']}, MISSING {counts['MISSING']}, DIFFERENT "
        f"{counts['DIFFERENT']}, UNKNOWN {counts['UNKNOWN']}; {len(entries)} "
        "distinct findings reviewed below."
    )

    out: list[str] = [
        generated_line(generated_at, midea_local),
        "",
        "# Discrepancies review",
        "",
        _INTRO,
        "",
        scope,
        "",
        f"## {_TITLES[Category.BUG]}",
        "",
        *_table(by_category[Category.BUG]),
        f"## {_TITLES[Category.VOCABULARY]}",
        "",
        *_table(by_category[Category.VOCABULARY]),
        f"## {_TITLES[Category.OFFSET]}",
        "",
        *_offset_table(by_category[Category.OFFSET]),
        f"## {_TITLES[Category.MASK]}",
        "",
        *_table(by_category[Category.MASK]),
        f"## {_TITLES[Category.FRAMEWORK]}",
        "",
        *_grouped_list(by_category[Category.FRAMEWORK], with_reason=True),
        "## F. Coverage gaps (UNKNOWN, not discrepancies)",
        "",
        *_coverage(comparisons, mapping),
        f"## {_TITLES[Category.COMMAND]}",
        "",
        *_grouped_list(by_category[Category.COMMAND], with_reason=False),
        f"## {_TITLES[Category.UNPARSED]}",
        "",
        *_grouped_list(by_category[Category.UNPARSED], with_reason=False),
        "## Resolved since the last review",
        "",
        _RESOLVED_INTRO,
        "",
    ]
    out += [
        f"- `{package}` {area} `{name}`: {decision.note}"
        for (package, area, name), decision in resolved
    ] or ["_none_"]
    return "\n".join(out) + "\n"
