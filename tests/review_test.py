"""Tests for the generated discrepancies review."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from midea_lua_conformance.compare import Comparison, Finding, Verdict
from midea_lua_conformance.ir import DecodeField
from midea_lua_conformance.review import build_review, classify, render_review
from midea_lua_conformance.triage import DECISIONS, Category


def _enum(verdict: Verdict, lua: str, py: str | None = None) -> Finding:
    return Finding(verdict, "enum", "mode[0x06]", "", lua_label=lua, py_label=py)


def _decode(
    verdict: Verdict,
    lua: DecodeField,
    py: DecodeField | None = None,
    name: str = "power",
) -> Finding:
    return Finding(verdict, "decode_field", name, "", lua_field=lua, py_field=py)


@pytest.mark.parametrize(
    ("package", "finding", "expected"),
    [
        pytest.param(
            "b0",
            _enum(Verdict.DIFFERENT, "hot_steam", "host_steam"),
            Category.BUG,
            id="enum_typo",
        ),
        pytest.param(
            "b0",
            _enum(Verdict.DIFFERENT, "fast_baking", "baking"),
            Category.VOCABULARY,
            id="enum_vocabulary",
        ),
        pytest.param(
            "b0",
            _enum(Verdict.MISSING, "baking"),
            Category.BUG,
            id="enum_missing_value",
        ),
        pytest.param(
            "b1",
            Finding(Verdict.MISSING, "command", "body_type 0x22", ""),
            Category.COMMAND,
            id="command_missing",
        ),
        pytest.param(
            "ea",
            _decode(Verdict.DIFFERENT, DecodeField("t", 20), DecodeField("t", 60)),
            Category.OFFSET,
            id="decode_offset",
        ),
        pytest.param(
            "b6",
            _decode(
                Verdict.DIFFERENT,
                DecodeField("p", 3, 0x0F),
                DecodeField("p", 3, 0xFF),
            ),
            Category.MASK,
            id="decode_mask",
        ),
        pytest.param(
            "da",
            _decode(
                Verdict.DIFFERENT,
                DecodeField("r", 5, 0xFF, 4),
                DecodeField("r", 5, 0xF0, 4),
            ),
            Category.FRAMEWORK,
            id="decode_equivalent_shift",
        ),
        pytest.param(
            "fa",
            _decode(Verdict.MISSING, DecodeField("modeValue", 3), name="mode"),
            Category.FRAMEWORK,
            id="decode_missing_known_attribute",
        ),
        pytest.param(
            "b1",
            _decode(Verdict.MISSING, DecodeField("hour", 9), name="hour"),
            Category.UNPARSED,
            id="decode_missing_unparsed",
        ),
    ],
)
def test_classify(package: str, finding: Finding, expected: Category) -> None:
    """Each rule sorts its kind of finding into the expected category."""
    assert classify(package, finding)[0] is expected


def test_build_review_merges_lua_files_and_applies_decisions() -> None:
    """A finding repeated over Lua files is one entry; a recorded decision wins."""
    vocabulary = Finding(
        Verdict.DIFFERENT,
        "enum",
        "mode[0x00]",
        "",
        lua_label="neutral_gear",
        py_label="none",
    )
    comparisons = [
        Comparison("lua/e1/a.lua", "e1", [vocabulary]),
        Comparison("lua/e1/b.lua", "e1", [vocabulary]),
    ]
    [entry] = build_review(comparisons)
    assert entry.lua_files == 2
    assert entry.recorded
    assert entry.reason == DECISIONS["e1", "enum", "mode[0x00]"].note


def test_render_review() -> None:
    """The review has its header, every section and the resolved decisions."""
    text = render_review(
        [],
        [],
        generated_at=datetime(2026, 10, 28, 9, 30, 15, tzinfo=UTC),
        midea_local="midea-local 14.0.0",
    )
    lines = text.splitlines()
    assert (
        lines[0] == "_Generated on 2026-10-28 09:30:15 UTC against midea-local 14.0.0_"
    )
    for section in "ABCDEFGH":
        assert f"## {section}. " in text
    # with no findings at all, every recorded decision is reported as resolved
    resolved = text.split("## Resolved since the last review", 1)[1]
    assert resolved.count("\n- `") == len(DECISIONS)
