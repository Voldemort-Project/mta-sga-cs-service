"""Phone number utility functions"""
from typing import Optional


def format_phone_international_id(phone_number: str) -> str:
    """
    Format phone number to international format for Indonesia (with 62 prefix).

    Converts phone numbers from local format (081234567890) to
    international format (6281234567890).

    Args:
        phone_number: Phone number in various formats
            - Local format: "081234567890" (with leading 0)
            - International format: "+6281234567890" or "6281234567890"
            - Other formats will be normalized

    Returns:
        Phone number in international format with 62 prefix (e.g., "6281234567890")

    Examples:
        >>> format_phone_international_id("081234567890")
        "6281234567890"
        >>> format_phone_international_id("6281234567890")
        "6281234567890"
        >>> format_phone_international_id("+6281234567890")
        "6281234567890"
    """
    if not phone_number:
        return phone_number

    # Remove any non-digit characters (spaces, +, -, etc.)
    phone_digits = ''.join(filter(str.isdigit, phone_number))

    if not phone_digits:
        return phone_number

    # Add 62 prefix if not present
    if phone_digits.startswith('62'):
        return phone_digits
    elif phone_digits.startswith('0'):
        # Remove leading 0 and add 62 prefix
        return '62' + phone_digits[1:]
    else:
        # Add 62 prefix if doesn't start with 0 or 62
        return '62' + phone_digits


def format_phone_local_id(phone_number: str) -> str:
    """
    Format phone number to local format for Indonesia (with leading 0).

    Converts phone numbers from international format (6281234567890) to
    local format (081234567890).

    Args:
        phone_number: Phone number in various formats
            - International format: "6281234567890" (with 62 prefix)
            - Local format: "081234567890" (with leading 0)
            - Other formats will be normalized

    Returns:
        Phone number in local format with leading 0 (e.g., "081234567890")

    Examples:
        >>> format_phone_local_id("6281234567890")
        "081234567890"
        >>> format_phone_local_id("081234567890")
        "081234567890"
    """
    if not phone_number:
        return phone_number

    # Remove any non-digit characters
    phone_digits = ''.join(filter(str.isdigit, phone_number))

    if not phone_digits:
        return phone_number

    # Convert from 62 prefix to 0 prefix
    if phone_digits.startswith('62'):
        return '0' + phone_digits[2:]
    elif phone_digits.startswith('0'):
        return phone_digits
    else:
        # If doesn't start with 0 or 62, assume it needs 0 prefix
        return '0' + phone_digits
