#!/usr/bin/env python3
"""Tests for UUID formatting utilities."""

import pytest

from utils import (
    format_uuid_string,
    strip_uuid_hyphens,
    is_valid_uuid_format,
    is_valid_hex_string,
    safe_format_uuid_string,
)


VALID_HEX = "550e8400e29b41d4a716446655440000"
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
INVALID_LENGTH = "550e8400e29b41d4a716446655440"  # 31 chars
INVALID_CHARS = "550e8400g29b41d4a716446655440000"  # contains 'g'


@pytest.mark.parametrize(
    "hex_input",
    [
        VALID_HEX,
        VALID_HEX.upper(),
        "550E8400e29B41d4A716446655440000",  # mixed case
    ],
)
def test_format_uuid_string_success(hex_input: str) -> None:
    """Formatting any case variation of a valid hex string should succeed."""
    assert format_uuid_string(hex_input) == VALID_UUID


@pytest.mark.parametrize(
    "bad_value, expected_message",
    [
        (INVALID_LENGTH, "exactly 32 characters"),
        (INVALID_CHARS, "valid hexadecimal characters"),
    ],
)
def test_format_uuid_string_invalid_hex(bad_value: str, expected_message: str) -> None:
    """Invalid hex strings should raise with helpful messages."""
    with pytest.raises(ValueError) as error:
        format_uuid_string(bad_value)
    assert expected_message in str(error.value)


@pytest.mark.parametrize("non_string", [123456789, None, object()])
def test_format_uuid_string_rejects_non_strings(non_string: object) -> None:
    """Non-string inputs must be rejected."""
    with pytest.raises(ValueError, match="must be a string"):
        format_uuid_string(non_string)  # type: ignore[arg-type]


def test_strip_uuid_hyphens_success() -> None:
    """Stripping hyphens should yield the canonical lowercase hex string."""
    assert strip_uuid_hyphens(VALID_UUID) == VALID_HEX


@pytest.mark.parametrize(
    "bad_uuid",
    [
        "invalid-uuid-format",
        "550e8400-e29b-41d4-a716-44665544",  # too short after stripping
        "550e8400-e29b-41d4-a716-44665544zzzz",  # invalid hex chars
        123,
        None,
    ],
)
def test_strip_uuid_hyphens_invalid_inputs(bad_uuid: object) -> None:
    """Invalid UUID strings should raise ValueError when stripping hyphens."""
    with pytest.raises(ValueError):
        strip_uuid_hyphens(bad_uuid)  # type: ignore[arg-type]


def test_round_trip_conversion() -> None:
    """Formatting and then stripping should return the original hex."""
    round_tripped = strip_uuid_hyphens(format_uuid_string(VALID_HEX))
    assert round_tripped == VALID_HEX


@pytest.mark.parametrize(
    "candidate, expected",
    [
        (VALID_UUID, True),
        ("550e8400-e29b-41d4-a716", False),
        ("not-a-uuid-at-all", False),
        (VALID_HEX, False),  # missing hyphens
        (None, False),
        (123, False),
    ],
)
def test_is_valid_uuid_format(candidate: object, expected: bool) -> None:
    """UUID format validation should handle both valid and invalid inputs."""
    assert is_valid_uuid_format(candidate) is expected


@pytest.mark.parametrize(
    "candidate, expected",
    [
        (VALID_HEX, True),
        (VALID_UUID, False),
        (INVALID_LENGTH, False),
        (INVALID_CHARS, False),
        (" 550e8400e29b41d4a716446655440000 ", False),
        (None, False),
        (123, False),
    ],
)
def test_is_valid_hex_string(candidate: object, expected: bool) -> None:
    """Hex validation should only pass for exact 32-character hex strings."""
    assert is_valid_hex_string(candidate) is expected


def test_safe_format_uuid_string_returns_value_or_none() -> None:
    """safe_format_uuid_string should wrap format failures without raising."""
    assert safe_format_uuid_string(VALID_HEX) == VALID_UUID
    assert safe_format_uuid_string(INVALID_CHARS) is None
    assert safe_format_uuid_string(INVALID_LENGTH) is None
    assert safe_format_uuid_string(123) is None  # type: ignore[arg-type]
