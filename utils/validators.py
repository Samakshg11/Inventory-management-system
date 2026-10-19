"""
utils/validators.py
-------------------
Pure validation functions used by the CLI helpers layer.

"Pure" means they take an input and return True/False (or raise ValueError).
They do NOT access the database — that is the service layer's job.

Having validators here (not inside the CLI or service) means:
- The CLI can call them to show nice error prompts.
- Tests can test validation logic without a MongoDB connection.
"""

import re
from bson import ObjectId
from bson.errors import InvalidId


def is_positive_float(value: str) -> bool:
    """
    Check if a string represents a float greater than zero.

    Args:
        value: The raw string entered by the user.

    Returns:
        bool: True if value can be parsed as float > 0.

    Example:
        >>> is_positive_float("9.99")
        True
        >>> is_positive_float("-1")
        False
        >>> is_positive_float("abc")
        False
    """
    try:
        return float(value) > 0
    except ValueError:
        return False


def is_non_negative_int(value: str) -> bool:
    """
    Check if a string represents an integer >= 0.

    Args:
        value: The raw string entered by the user.

    Returns:
        bool: True if value can be parsed as int >= 0.

    Example:
        >>> is_non_negative_int("0")
        True
        >>> is_non_negative_int("50")
        True
        >>> is_non_negative_int("-3")
        False
    """
    try:
        return int(value) >= 0
    except ValueError:
        return False


def is_positive_int(value: str) -> bool:
    """
    Check if a string represents an integer strictly greater than 0.

    Used for stock movement quantities (you cannot move 0 units).

    Args:
        value: The raw string entered by the user.

    Returns:
        bool: True if value can be parsed as int > 0.
    """
    try:
        return int(value) > 0
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    """
    Check if a string looks like a valid email address.

    Uses a simple regex — sufficient for a college project.
    Does NOT actually send an email or check DNS.

    Args:
        email: The email string to validate.

    Returns:
        bool: True if the email matches the pattern.

    Example:
        >>> is_valid_email("supplier@example.com")
        True
        >>> is_valid_email("notanemail")
        False
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def is_valid_object_id(oid_str: str) -> bool:
    """
    Check if a string is a valid MongoDB ObjectId (24-character hex string).

    PyMongo raises bson.errors.InvalidId if you pass a bad string to ObjectId().
    This function catches that and returns False instead.

    Args:
        oid_str: The string to test.

    Returns:
        bool: True if the string is a valid ObjectId hex string.

    Example:
        >>> is_valid_object_id("507f1f77bcf86cd799439011")
        True
        >>> is_valid_object_id("notanobjectid")
        False
    """
    try:
        ObjectId(oid_str)
        return True
    except (InvalidId, TypeError):
        return False


def is_non_empty_string(value: str) -> bool:
    """
    Check if a string is not empty or whitespace-only.

    Args:
        value: The string to check.

    Returns:
        bool: True if the string has at least one non-whitespace character.
    """
    return bool(value and value.strip())


def parse_tags(raw: str) -> list[str]:
    """
    Parse a comma-separated string of tags into a cleaned list.

    Args:
        raw: Raw string like "  electronics, gadgets , new  ".

    Returns:
        list[str]: Cleaned list like ["electronics", "gadgets", "new"].
                   Empty strings are filtered out.

    Example:
        >>> parse_tags("laptop, electronics, ,  ")
        ['laptop', 'electronics']
    """
    return [tag.strip().lower() for tag in raw.split(",") if tag.strip()]
