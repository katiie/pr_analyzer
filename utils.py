"""Utility functions for string manipulation and formatting."""

import re
from typing import Optional


def format_uuid_string(hex_string: str) -> str:
    """
    Convert a 32-character hexadecimal string to UUID format (8-4-4-4-12).

    Args:
        hex_string (str): A 32-character hexadecimal string

    Returns:
        str: Formatted UUID string in 8-4-4-4-12 format

    Raises:
        ValueError: If input is not exactly 32 characters or contains invalid hex characters

    Example:
        >>> format_uuid_string("550e8400e29b41d4a716446655440000")
        "550e8400-e29b-41d4-a716-446655440000"
    """
    if not isinstance(hex_string, str):
        raise ValueError("Input must be a string")

    if len(hex_string) != 32:
        raise ValueError(f"Input must be exactly 32 characters, got {len(hex_string)}")

    # Validate that the string contains only valid hexadecimal characters
    if not re.match(r'^[0-9a-fA-F]{32}$', hex_string):
        raise ValueError("Input must contain only valid hexadecimal characters (0-9, a-f, A-F)")

    # Convert to lowercase for consistency
    hex_string = hex_string.lower()

    # Format as 8-4-4-4-12
    formatted = f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:]}"

    return formatted


def strip_uuid_hyphens(uuid_string: str) -> str:
    """
    Remove hyphens from a UUID string to get a 32-character hex string.

    Args:
        uuid_string (str): A UUID string in 8-4-4-4-12 format

    Returns:
        str: 32-character hexadecimal string without hyphens

    Raises:
        ValueError: If input is not a valid UUID format

    Example:
        >>> strip_uuid_hyphens("550e8400-e29b-41d4-a716-446655440000")
        "550e8400e29b41d4a716446655440000"
    """
    if not isinstance(uuid_string, str):
        raise ValueError("Input must be a string")

    # Remove hyphens
    hex_string = uuid_string.replace('-', '')

    # Validate the result
    if len(hex_string) != 32:
        raise ValueError(f"UUID string must result in exactly 32 characters when hyphens are removed, got {len(hex_string)}")

    if not re.match(r'^[0-9a-fA-F]{32}$', hex_string):
        raise ValueError("UUID string must contain only valid hexadecimal characters")

    return hex_string.lower()


def is_valid_uuid_format(uuid_string: str) -> bool:
    """
    Check if a string is in valid UUID format (8-4-4-4-12).

    Args:
        uuid_string (str): String to validate

    Returns:
        bool: True if string is in valid UUID format, False otherwise

    Example:
        >>> is_valid_uuid_format("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> is_valid_uuid_format("550e8400e29b41d4a716446655440000")
        False
    """
    if not isinstance(uuid_string, str):
        return False

    # Check if it matches the UUID pattern: 8-4-4-4-12
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return bool(re.match(pattern, uuid_string))


def is_valid_hex_string(hex_string: str) -> bool:
    """
    Check if a string is a valid 32-character hexadecimal string.

    Args:
        hex_string (str): String to validate

    Returns:
        bool: True if string is valid 32-char hex string, False otherwise

    Example:
        >>> is_valid_hex_string("550e8400e29b41d4a716446655440000")
        True
        >>> is_valid_hex_string("550e8400-e29b-41d4-a716-446655440000")
        False
    """
    if not isinstance(hex_string, str):
        return False

    return len(hex_string) == 32 and bool(re.match(r'^[0-9a-fA-F]{32}$', hex_string))


def safe_format_uuid_string(hex_string: str) -> Optional[str]:
    """
    Safely convert a 32-character hexadecimal string to UUID format.
    Returns None if the input is invalid instead of raising an exception.

    Args:
        hex_string (str): A 32-character hexadecimal string

    Returns:
        Optional[str]: Formatted UUID string or None if invalid input

    Example:
        >>> safe_format_uuid_string("550e8400e29b41d4a716446655440000")
        "550e8400-e29b-41d4-a716-446655440000"
        >>> safe_format_uuid_string("invalid")
        None
    """
    try:
        return format_uuid_string(hex_string)
    except ValueError:
        return None
