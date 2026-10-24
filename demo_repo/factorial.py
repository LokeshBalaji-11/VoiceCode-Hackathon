def factorial(n: int) -> int:
    """Return the factorial of a non‑negative integer ``n``.

    Args:
        n (int): A non‑negative integer whose factorial is to be computed.

    Returns:
        int: The factorial of ``n``.

    Raises:
        ValueError: If ``n`` is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative integers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# --- Agent Auto-Patch ---
def factorial(n: int) -> int:
    """Return the factorial of a non‑negative integer *n*.

    Args:
        n: A non‑negative integer whose factorial is to be computed.

    Returns:
        The factorial of *n* as an integer.

    Raises:
        ValueError: If *n* is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
