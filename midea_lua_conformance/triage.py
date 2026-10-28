"""Human triage decisions applied on top of the automatic review.

:mod:`.review` sorts every ``MISSING``/``DIFFERENT`` finding into a category by
rule. Rules cannot tell an intentional rename from a bug, or know that a field
needs a protocol expert, so a decision recorded here overrides the rule's
category and adds a note. Key: ``(package, area, finding name)`` exactly as the
finding appears in ``REPORT.md``.

A decision whose finding no longer appears is listed under "Resolved since the
last review" in ``DISCREPANCIES.md``; delete it once confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Category(StrEnum):
    """Review sections of ``DISCREPANCIES.md``."""

    BUG = "A"
    VOCABULARY = "B"
    OFFSET = "C"
    MASK = "D"
    FRAMEWORK = "E"
    COMMAND = "G"
    UNPARSED = "H"


@dataclass(frozen=True)
class Decision:
    """A recorded triage decision for one finding."""

    category: Category
    note: str


_B0_LAYOUT = (
    "b0 status/mode parsing is broadly out of step with T_0000_B0_6.lua "
    "(Lua: status = byte[0] & 0x7F, mode = byte[1]); needs a full re-read."
)
_WHOLE_BYTE = (
    "Lua reads the whole byte, midealocal masks the high bits; midealocal is "
    "arguably more correct, low risk."
)
_AC_SCRATCH = "timer-packing scratch variable in the Lua, not a device attribute."
_AC_MULTI_BRANCH = (
    "Lua reads it from a different byte per dataType and midealocal has several "
    "body classes; only one branch is captured on each side."
)
_EA_SHIFT = "+40 is large and suspicious; start the offset review here."

DECISIONS: dict[tuple[str, str, str], Decision] = {
    ("b0", "decode_field", "status"): Decision(Category.BUG, _B0_LAYOUT),
    ("b0", "decode_field", "mode"): Decision(Category.BUG, _B0_LAYOUT),
    ("e1", "enum", "mode[0x00]"): Decision(
        Category.VOCABULARY,
        "neutral_gear -> none is a known intentional rename.",
    ),
    ("e1", "enum", "status[0x04]"): Decision(
        Category.BUG,
        "cancel_order vs error is a real divergence worth a look.",
    ),
    ("cd", "decode_field", "power"): Decision(Category.MASK, _WHOLE_BYTE),
    ("fb", "decode_field", "power"): Decision(Category.MASK, _WHOLE_BYTE),
    ("fd", "decode_field", "fan_speed"): Decision(Category.MASK, _WHOLE_BYTE),
    ("ac", "decode_field", "close_hour"): Decision(Category.FRAMEWORK, _AC_SCRATCH),
    ("ac", "decode_field", "close_step_mintues"): Decision(
        Category.FRAMEWORK,
        _AC_SCRATCH,
    ),
    ("ac", "decode_field", "open_hour"): Decision(Category.FRAMEWORK, _AC_SCRATCH),
    ("ac", "decode_field", "open_step_mintues"): Decision(
        Category.FRAMEWORK,
        _AC_SCRATCH,
    ),
    ("ac", "decode_field", "ptc"): Decision(Category.FRAMEWORK, _AC_SCRATCH),
    ("ac", "decode_field", "small_temperature"): Decision(
        Category.FRAMEWORK,
        _AC_SCRATCH,
    ),
    ("ac", "decode_field", "indoor_temperature"): Decision(
        Category.FRAMEWORK,
        _AC_MULTI_BRANCH,
    ),
    ("ac", "decode_field", "outdoor_temperature"): Decision(
        Category.FRAMEWORK,
        _AC_MULTI_BRANCH,
    ),
    ("ea", "decode_field", "top_temperature"): Decision(Category.OFFSET, _EA_SHIFT),
    ("ea", "decode_field", "bottom_temperature"): Decision(
        Category.OFFSET,
        _EA_SHIFT,
    ),
}
