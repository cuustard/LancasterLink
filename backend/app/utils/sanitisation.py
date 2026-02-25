"""
Input sanitisation utilities (NFR-SDP-03).

Ensures user-supplied strings are safe before they reach the database
or are reflected in API responses.
"""

import re


def sanitise_string(value: str, max_length: int = 255) -> str:
    """Strip dangerous characters and enforce a length limit.

    Args:
        value: Raw user input.
        max_length: Maximum allowed length.

    Returns:
        Cleaned string.
    """
    # Remove control characters (except space)
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", value)
    # Collapse whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned[:max_length]


def sanitise_atco_code(code: str) -> str:
    """Validate and normalise a NaPTAN ATCO code.

    ATCO codes are alphanumeric, typically 12 characters.
    """
    cleaned = re.sub(r"[^A-Za-z0-9]", "", code)
    if not cleaned:
        raise ValueError("Invalid ATCO code: empty after sanitisation.")
    return cleaned[:20]


def sanitise_search_term(term: str, max_length: int = 100) -> str:
    """Sanitise a free-text search term (e.g. stop name lookup).

    Prevents SQL injection via parameterised queries, but we still
    strip obviously dangerous patterns as defence-in-depth.
    """
    cleaned = sanitise_string(term, max_length)
    # Remove SQL-injection-style patterns (belt-and-braces)
    cleaned = re.sub(r"(--|;|/\*|\*/|')", "", cleaned)
    return cleaned
