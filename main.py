"""
main.py
--------
Entry point for the Inventory Stock Management System CLI.

Responsibilities:
  1. Load configuration from .env
  2. Connect to MongoDB (fail fast if not running)
  3. Create indexes on startup (idempotent — safe to run every time)
  4. Display the main menu and route to sub-menus

Run with:
    python main.py
    # or with the virtual environment active:
    python3 main.py
"""

import sys

from db.connection import get_client
from db.indexes import create_indexes
from cli.helpers import print_header, print_error, BOLD, RESET, CYAN, GREEN
from cli.menus import (
    supplier_menu,
    product_menu,
    stock_menu,
    reports_menu,
    menu_export_csv,
)


BANNER = f"""
{BOLD}{GREEN}
╔══════════════════════════════════════════════════════╗
║       INVENTORY STOCK MANAGEMENT SYSTEM             ║
║       Python + MongoDB | College Assignment          ║
╚══════════════════════════════════════════════════════╝
{RESET}"""


def main() -> None:
    """
    Application entry point.

    1. Prints the welcome banner.
    2. Connects to MongoDB (exits with a clear error if unavailable).
    3. Creates indexes.
    4. Runs the main menu loop until the user exits.
    """
    print(BANNER)

    # Step 1: Connect to MongoDB — get_client() pings the server.
    # If MongoDB is not running, it prints a friendly error and calls SystemExit.
    try:
        get_client()
    except SystemExit:
        sys.exit(1)

    # Step 2: Ensure all indexes exist (idempotent — runs every startup).
    create_indexes()

    # Step 3: Main menu loop
    while True:
        print_header("Main Menu")
        print("  1. Product Management")
        print("  2. Supplier Management")
        print("  3. Stock Operations  (IN / OUT)")
        print("  4. Reports & Analytics")
        print("  5. Export Products to CSV")
        print("  0. Exit")

        choice = input(f"\n  {CYAN}Select option: {RESET}").strip()

        if choice == "1":
            product_menu()
        elif choice == "2":
            supplier_menu()
        elif choice == "3":
            stock_menu()
        elif choice == "4":
            reports_menu()
        elif choice == "5":
            menu_export_csv()
            input(f"\n  {CYAN}Press Enter to continue...{RESET}")
        elif choice == "0":
            print(f"\n{BOLD}{GREEN}  Goodbye! Closing connection...{RESET}\n")
            from db.connection import close_connection
            close_connection()
            sys.exit(0)
        else:
            print_error("Invalid option. Please enter 1-5 or 0.")


if __name__ == "__main__":
    main()
