"""
cli/helpers.py
--------------
Reusable helper functions for the CLI layer.

Responsibilities:
  - Prompt the user for input and re-prompt on invalid input.
  - Print formatted tables using tabulate.
  - Display consistent success/error messages with colour codes.
  - Pagination helpers for product listing.

IMPORTANT: This module does NOT call any service functions.
It only handles input/output formatting.
"""

from tabulate import tabulate
from bson import ObjectId


# ANSI colour codes for a friendlier terminal experience
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_success(message: str) -> None:
    """Print a green success message."""
    print(f"{GREEN}✔  {message}{RESET}")


def print_error(message: str) -> None:
    """Print a red error message."""
    print(f"{RED}✘  {message}{RESET}")


def print_warning(message: str) -> None:
    """Print a yellow warning message."""
    print(f"{YELLOW}⚠  {message}{RESET}")


def print_info(message: str) -> None:
    """Print a cyan informational message."""
    print(f"{CYAN}ℹ  {message}{RESET}")


def print_header(title: str) -> None:
    """Print a bold section header with a separator line."""
    width = 60
    print(f"\n{BOLD}{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * width}{RESET}")


def print_table(rows: list[dict], headers: dict) -> None:
    """
    Print a list of dicts as a formatted table using tabulate.

    Args:
        rows:    List of dicts to display.
        headers: Mapping of dict key → column header string.
                 Example: {"sku": "SKU", "name": "Product Name"}
    """
    if not rows:
        print_warning("No records found.")
        return

    # Build list of lists for tabulate from the dict rows
    table_data = []
    for row in rows:
        table_data.append([row.get(key, "-") for key in headers])

    print(tabulate(table_data, headers=list(headers.values()), tablefmt="rounded_outline"))


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def get_input(prompt: str, validator=None, error_msg: str = "Invalid input.") -> str:
    """
    Prompt the user for input and re-prompt until valid.

    Args:
        prompt:    The prompt string to display.
        validator: Optional callable(str) -> bool. If None, accepts any non-empty input.
        error_msg: Message shown when validation fails.

    Returns:
        str: The validated, stripped input string.
    """
    while True:
        raw = input(f"  {CYAN}{prompt}{RESET} ").strip()
        if validator is None:
            if raw:
                return raw
            print_error("Input cannot be empty.")
        else:
            if validator(raw):
                return raw
            print_error(error_msg)


def get_optional_input(prompt: str) -> str:
    """
    Prompt the user for optional input. Returns empty string if skipped.

    Args:
        prompt: The prompt string to display.

    Returns:
        str: The stripped input (may be empty).
    """
    raw = input(f"  {CYAN}{prompt} (press Enter to skip){RESET} ").strip()
    return raw


def get_int_input(prompt: str, min_val: int = 0) -> int:
    """
    Prompt for an integer input >= min_val. Re-prompts until valid.

    Args:
        prompt:  Display prompt.
        min_val: Minimum acceptable value (default 0).

    Returns:
        int: The validated integer.
    """
    while True:
        raw = input(f"  {CYAN}{prompt}{RESET} ").strip()
        try:
            value = int(raw)
            if value >= min_val:
                return value
            print_error(f"Value must be >= {min_val}.")
        except ValueError:
            print_error("Please enter a valid whole number.")


def get_float_input(prompt: str, min_val: float = 0.01) -> float:
    """
    Prompt for a float input > min_val. Re-prompts until valid.

    Args:
        prompt:  Display prompt.
        min_val: Minimum acceptable value (default 0.01).

    Returns:
        float: The validated float.
    """
    while True:
        raw = input(f"  {CYAN}{prompt}{RESET} ").strip()
        try:
            value = float(raw)
            if value >= min_val:
                return round(value, 2)
            print_error(f"Value must be >= {min_val}.")
        except ValueError:
            print_error("Please enter a valid number (e.g., 9.99).")


def confirm(prompt: str) -> bool:
    """
    Ask the user to confirm an action (yes/no).

    Args:
        prompt: The question to ask.

    Returns:
        bool: True if the user entered 'y' or 'yes'.
    """
    answer = input(f"  {YELLOW}{prompt} [y/N]{RESET} ").strip().lower()
    return answer in ("y", "yes")


def format_object_id(oid) -> str:
    """
    Safely convert an ObjectId or None to a display string.

    Args:
        oid: ObjectId instance or None.

    Returns:
        str: Hex string like "507f..." or "-" if None.
    """
    return str(oid) if oid else "-"


def format_currency(value: float) -> str:
    """
    Format a float as a currency string with rupee symbol.

    Args:
        value: Numeric value to format.

    Returns:
        str: e.g., "₹ 1,234.56"
    """
    return f"₹ {value:,.2f}"


def paginate_prompt(current_page: int, total_pages: int) -> str:
    """
    Display pagination info and ask user for navigation choice.

    Args:
        current_page: Current page number (1-indexed).
        total_pages:  Total number of pages.

    Returns:
        str: 'n' (next), 'p' (previous), or 'q' (quit pagination).
    """
    parts = []
    if current_page > 1:
        parts.append("[P]rev")
    if current_page < total_pages:
        parts.append("[N]ext")
    parts.append("[Q]uit")

    print(f"\n  Page {current_page} of {total_pages}   {' | '.join(parts)}")
    choice = input(f"  {CYAN}Navigation: {RESET}").strip().lower()
    return choice
