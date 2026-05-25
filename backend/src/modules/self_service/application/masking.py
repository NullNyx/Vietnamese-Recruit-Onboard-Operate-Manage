"""Sensitive field masking utility for the Employee Self-Service module.

Masks sensitive fields (id_number, tax_code) by preserving only the last 4 characters
and replacing the rest with asterisks.
"""


def mask_sensitive_field(value: str | None) -> str | None:
    """Mask a sensitive string field, preserving only the last 4 characters.

    Args:
        value: The string to mask, or None.

    Returns:
        The masked string, or None if input is None.

    Rules:
        - For None input: returns None
        - For strings of length N >= 4: replaces first (N-4) chars with '*', preserves last 4
        - For strings shorter than 4 characters: masks entirely with '*'

    Examples:
        >>> mask_sensitive_field("123456789012")
        '********9012'
        >>> mask_sensitive_field("1234")
        '1234'
        >>> mask_sensitive_field("abc")
        '***'
        >>> mask_sensitive_field("a")
        '*'
        >>> mask_sensitive_field(None)
        None
    """
    if value is None:
        return None

    length = len(value)

    if length < 4:
        return "*" * length

    return "*" * (length - 4) + value[-4:]
