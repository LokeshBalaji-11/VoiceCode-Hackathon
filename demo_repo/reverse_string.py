#!/usr/bin/env python3
"""Utility script that reads a string from the command line or standard input and prints its reversal.

Usage examples:
  $ python reverse_string.py "Hello World"
  $ echo "Hello" | python reverse_string.py
"""
import sys

def main() -> None:
    # If arguments are supplied, treat them as the input string (joined by spaces)
    if len(sys.argv) > 1:
        input_str = " ".join(sys.argv[1:])
    else:
        # Otherwise, read the entire stdin payload
        input_str = sys.stdin.read().rstrip("\n")
    # Output the reversed string
    print(input_str[::-1])

if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
#!/usr/bin/env python3
"""
reverse_string.py

A simple script that reads a string from standard input (or the command line)
and prints the reversed string.
"""

def reverse_string(s: str) -> str:
    """Return the reversed version of the input string."""
    return s[::-1]

def main() -> None:
    import sys
    # If arguments are provided, use the first argument as the string.
    if len(sys.argv) > 1:
        input_str = " ".join(sys.argv[1:])
    else:
        # Otherwise read from stdin.
        input_str = sys.stdin.read().rstrip("\n")
    print(reverse_string(input_str))

if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
'''reverse_string.py

A simple script that reverses a given string and prints the result.
It accepts the string as a command‑line argument; if none is provided, it prompts the user for input.
'''

import sys


def reverse_string(s: str) -> str:
    """Return the reversed version of *s*.

    Uses Python slicing to reverse the string efficiently.
    """
    return s[::-1]


def main() -> None:
    """Entry point for the script.

    - If a command‑line argument is supplied, it is used as the string to reverse.
    - Otherwise, the user is prompted to enter a string via ``input``.
    The reversed string is then printed to stdout.
    """
    if len(sys.argv) > 1:
        original = sys.argv[1]
    else:
        original = input("Enter a string to reverse: ")
    print(reverse_string(original))


if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
#!/usr/bin/env python3\n\"\"\"Utility to reverse a string.\n\nProvides a reusable :func:`reverse_string` function and a command‑line\ninterface that reads a string from the first argument or from standard\ninput when no argument is given, then prints the reversed string.\n\"\"\"\n\nfrom __future__ import annotations\nimport sys\n\ndef reverse_string(s: str) -> str:\n    \"\"\"Return the reverse of *s*.\n\n    The function works with any string, preserving Unicode characters.\n    It is a thin wrapper around slicing for clarity and testability.\n    \"\"\"\n    return s[::-1]\n\ndef _main() -> None:\n    \"\"\"Entry point for the script.\n\n    If a command‑line argument is supplied, it is used as the input string.\n    Otherwise the script reads the entire contents of ``stdin``.  The\n    reversed string is printed to ``stdout`` without an additional newline\n    (``print`` adds one by default).\n    \"\"\"\n    if len(sys.argv) > 1:\n        input_str = sys.argv[1]\n    else:\n        # Read from stdin, stripping the trailing newline for consistency.\n        input_str = sys.stdin.read().rstrip(\"\\n\")\n    print(reverse_string(input_str))\n\nif __name__ == \"__main__\":\n    _main()

# --- Agent Auto-Patch ---
#!/usr/bin/env python3
"""reverse_string.py

Standalone script that reads a string from a command‑line argument or standard input
and outputs the reversed string.

Usage examples:
    python reverse_string.py "Hello World"
    echo "Hello World" | python reverse_string.py
"""
import sys

def get_input() -> str:
    """Return the input string.

    Preference order:
    1. First command‑line argument (after the script name).
    2. If no argument, read from standard input until EOF.
    """
    if len(sys.argv) > 1:
        # Join all arguments after the script name to allow spaces without quoting
        return " ".join(sys.argv[1:])
    # Read from stdin; strip trailing newlines but preserve other whitespace
    return sys.stdin.read().rstrip("\n")

def reverse_string(s: str) -> str:
    """Return the reversed version of *s*."""
    return s[::-1]

def main() -> None:
    input_str = get_input()
    # If no input provided (empty string), just output nothing
    if input_str == "":
        return
    print(reverse_string(input_str))

if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
def reverse_string(s: str) -> str:
    """Return the reversal of the input string `s`."""
    return s[::-1]


if __name__ == "__main__":
    import sys
    # If a command‑line argument is provided, use it; otherwise read from stdin.
    if len(sys.argv) > 1:
        input_str = sys.argv[1]
    else:
        input_str = sys.stdin.read().strip()
    print(reverse_string(input_str))


# --- Agent Auto-Patch ---
#!/usr/bin/env python3
"""reverse_string.py

A simple utility that reads a string (either from a command‑line argument or from standard input) and prints its reversed version.

Usage:
  python reverse_string.py "hello"
  echo "hello" | python reverse_string.py
"""

import argparse
import sys


def _get_input_string() -> str:
    """Return the string to reverse.

    Preference order:
    1. Positional command‑line argument if provided.
    2. Entire contents of standard input otherwise.
    """
    parser = argparse.ArgumentParser(description="Reverse a given string.")
    parser.add_argument(
        "input_string",
        nargs="?",
        help="String to reverse. If omitted, the script reads from stdin.",
    )
    args = parser.parse_args()
    if args.input_string is not None:
        return args.input_string
    # Read from stdin; strip trailing newlines but keep other whitespace.
    return sys.stdin.read().rstrip("\n")


def main() -> None:
    original = _get_input_string()
    reversed_str = original[::-1]
    print(reversed_str)


if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
#!/usr/bin/env python3
"""
Utility script to reverse a given string.

Usage:
    python reverse_string.py "hello"
    echo "hello" | python reverse_string.py
"""

import sys

def reverse_string(s: str) -> str:
    """Return the reversed version of the input string."""
    return s[::-1]


def main():
    # If an argument is provided, use it; otherwise read from stdin.
    if len(sys.argv) > 1:
        input_str = " ".join(sys.argv[1:])
    else:
        input_str = sys.stdin.read().strip()
    print(reverse_string(input_str))


if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
import sys

def reverse_string(s: str) -> str:
    """Return the reversed version of the input string."""
    return s[::-1]

def main() -> None:
    # If arguments are provided, join them as the input string.
    if len(sys.argv) > 1:
        input_str = " ".join(sys.argv[1:])
    else:
        # Otherwise read from stdin.
        input_str = sys.stdin.read().rstrip("\n")
    print(reverse_string(input_str))

if __name__ == "__main__":
    main()


# --- Agent Auto-Patch ---
#!/usr/bin/env python3
"""
reverse_string.py

Provides a function to reverse a string and a command-line interface
that reads a string from standard input and prints the reversed string.
"""

def reverse_string(s: str) -> str:
    """
    Return the reversed version of the given string.

    Args:
        s: The string to reverse.

    Returns:
        The reversed string.
    """
    return s[::-1]


def _main() -> None:
    import sys
    # Read entire input and strip trailing newline characters
    input_str = sys.stdin.read().rstrip("\n")
    print(reverse_string(input_str))


if __name__ == "__main__":
    _main()


# --- Agent Auto-Patch ---
def reverse_string(s: str) -> str:
    """Return the reversed version of the input string `s`.

    Args:
        s: The string to reverse.

    Returns:
        A new string with characters in reverse order.
    """
    return s[::-1]
