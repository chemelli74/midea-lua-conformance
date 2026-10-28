"""Unit tests for ``midealocal`` device introspection."""

from __future__ import annotations

import ast

import pytest

from midea_lua_conformance.ir import DecodeField
from midea_lua_conformance.py_introspect import _parser_field, introspect_device


def test_introspect_e1_decode_fields() -> None:
    """AST analysis recovers the E1 response-body field map with masks."""
    py = introspect_device("e1")
    assert py.device_type == 0xE1

    by_name = {f.name: f for f in py.decode_fields}
    assert by_name["status"].signature() == (1, 0xFF, 0)
    assert by_name["mode"].signature() == (2, 0xFF, 0)
    assert by_name["child_lock"].signature() == (5, 0x10, 0)
    assert by_name["temperature"].signature() == (11, 0xFF, 0)
    assert by_name["door"].boolean is True


def test_introspect_e1_enums_from_class_vars() -> None:
    """Class-level lookup tables (``_modes`` / ``_status``) lower into enums."""
    py = introspect_device("e1")
    modes = py.enum("modes")
    assert modes is not None
    assert modes.members["eco_wash"] == 0x04
    status = py.enum("status")
    assert status is not None
    assert status.members["running"] == 0x03


def test_introspect_e1_request_bytes() -> None:
    """Request classes are instantiated and their body bytes captured."""
    py = introspect_device("e1")
    by_name = {c.name: c for c in py.commands}
    assert by_name["MessageQuery"].body_type == 0x00
    assert by_name["MessageLock"].body_type == 0x83
    # MessageLock default body: [0x83, 0x04, 0x00 * 36]  (0x04 == "unlocked")
    assert by_name["MessageLock"].body[1] == 0x04


def test_introspect_unknown_package_is_soft_failure() -> None:
    """An unknown device folder yields notes, not an exception."""
    py = introspect_device("zz")
    assert py.device_type is None
    assert py.notes


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "BoolParser(DeviceAttributes.power, 1, bit=0)",
            DecodeField("power", 1, 0x01, 0, boolean=True),
            id="bool_bit_keyword",
        ),
        pytest.param(
            'BoolParser("power", 1, 3)',
            DecodeField("power", 1, 0x08, 3, boolean=True),
            id="bool_bit_positional",
        ),
        pytest.param(
            "IntParser(DeviceAttributes.fan_speed, 3, byte_mask=0x7F)",
            DecodeField("fan_speed", 3, 0x7F, 0),
            id="int_byte_mask_not_shifted",
        ),
        pytest.param(
            "IntParser('target', 4, 100)",
            DecodeField("target", 4, 0xFF, 0),
            id="int_third_positional_is_max_value",
        ),
        pytest.param(
            "FloatParser('indoor_temperature', 7, 2, transform_func=parse_temp)",
            DecodeField(
                "indoor_temperature",
                7,
                0xFF,
                0,
                transform="2 bytes; parse_temp",
            ),
            id="float_multi_byte_with_transform",
        ),
    ],
)
def test_parser_declarations_become_decode_fields(
    source: str,
    expected: DecodeField,
) -> None:
    """Midealocal BodyParser declarations lower to the same IR as body[...] reads."""
    call = ast.parse(source, mode="eval").body
    assert isinstance(call, ast.Call)
    assert _parser_field(call) == expected


def test_non_parser_call_is_ignored() -> None:
    """Only the known parser classes are lowered."""
    call = ast.parse("SomethingElse('power', 1)", mode="eval").body
    assert isinstance(call, ast.Call)
    assert _parser_field(call) is None


def test_introspect_parser_based_package() -> None:
    """A package declaring its fields with parsers is no longer empty."""
    by_name = {(f.name, f.byte): f for f in introspect_device("ac").decode_fields}
    assert by_name["power", 1].signature() == (1, 0x01, 0)
    assert by_name["swing_horizontal", 7].signature() == (7, 0x03, 0)
