"""
cli/menus.py
-------------
All sub-menu functions for the inventory management CLI.

This module is the "controller" in a simple MVC sense:
  - It calls helper functions to get user input.
  - It calls service functions to perform operations.
  - It formats and displays the results.

It does NOT contain any MongoDB queries — those are in the service layer.
"""

from bson import ObjectId

from cli.helpers import (
    print_header, print_success, print_error, print_warning, print_info,
    print_table, get_input, get_optional_input, get_int_input, get_float_input,
    confirm, format_object_id, format_currency, paginate_prompt, BOLD, RESET, CYAN
)
from services import supplier_service, product_service, stock_service, report_service
from utils.validators import is_valid_email, is_non_empty_string, parse_tags
from utils.exporter import export_products_to_csv

import calendar


# ============================================================
# SUPPLIER MENUS
# ============================================================

def menu_add_supplier() -> None:
    """Prompt user for supplier details and insert into DB."""
    print_header("Add New Supplier")

    name = get_input("Supplier Name:", lambda v: len(v.strip()) >= 2,
                     "Name must be at least 2 characters.")
    email = get_input("Email:", is_valid_email, "Please enter a valid email address.")
    phone = get_optional_input("Phone Number:")
    address = get_optional_input("Address:")

    result = supplier_service.add_supplier(name, email, phone, address)

    if result["success"]:
        print_success(f"Supplier '{name}' added. ID: {result['inserted_id']}")
    else:
        print_error(result["error"])


def menu_list_suppliers() -> None:
    """Fetch and display all suppliers in a table."""
    print_header("All Suppliers")

    suppliers = supplier_service.get_all_suppliers()
    if not suppliers:
        print_warning("No suppliers found. Add one first.")
        return

    rows = []
    for s in suppliers:
        rows.append({
            "id": str(s["_id"]),
            "name": s.get("name", "-"),
            "email": s.get("email", "-"),
            "phone": s.get("phone") or "-",
            "address": s.get("address") or "-",
        })

    print_table(rows, {
        "id": "Supplier ID",
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "address": "Address",
    })
    print_info(f"Total: {len(suppliers)} supplier(s)")


def menu_update_supplier() -> None:
    """Prompt for supplier ID and fields to update."""
    print_header("Update Supplier")

    menu_list_suppliers()
    supplier_id = get_input("Enter Supplier ID to update:")

    sup = supplier_service.get_supplier_by_id(supplier_id)
    if not sup:
        print_error("Supplier not found or invalid ID.")
        return

    print_info(f"Updating: {sup['name']} ({sup['email']})")
    print_info("Press Enter to keep existing value.")

    updates = {}
    name = input(f"  {CYAN}New Name [{sup['name']}]: {RESET}").strip()
    if name:
        updates["name"] = name

    phone = input(f"  {CYAN}New Phone [{sup.get('phone', '')}]: {RESET}").strip()
    if phone:
        updates["phone"] = phone

    address = input(f"  {CYAN}New Address [{sup.get('address', '')}]: {RESET}").strip()
    if address:
        updates["address"] = address

    if not updates:
        print_warning("No changes made.")
        return

    result = supplier_service.update_supplier(supplier_id, updates)
    if result["success"]:
        print_success("Supplier updated successfully.")
    else:
        print_error(result["error"])


def menu_delete_supplier() -> None:
    """Prompt for supplier ID and confirm before deleting."""
    print_header("Delete Supplier")

    menu_list_suppliers()
    supplier_id = get_input("Enter Supplier ID to delete:")

    sup = supplier_service.get_supplier_by_id(supplier_id)
    if not sup:
        print_error("Supplier not found or invalid ID.")
        return

    if not confirm(f"Delete supplier '{sup['name']}'? This cannot be undone."):
        print_info("Deletion cancelled.")
        return

    result = supplier_service.delete_supplier(supplier_id)
    if result["success"]:
        print_success("Supplier deleted.")
    else:
        print_error(result["error"])


def supplier_menu() -> None:
    """Supplier management sub-menu loop."""
    while True:
        print_header("Supplier Management")
        print("  1. Add Supplier")
        print("  2. View All Suppliers")
        print("  3. Update Supplier")
        print("  4. Delete Supplier")
        print("  0. Back to Main Menu")

        choice = input(f"\n  {CYAN}Select option: {RESET}").strip()
        if choice == "1":
            menu_add_supplier()
        elif choice == "2":
            menu_list_suppliers()
        elif choice == "3":
            menu_update_supplier()
        elif choice == "4":
            menu_delete_supplier()
        elif choice == "0":
            break
        else:
            print_error("Invalid option. Enter 1-4 or 0.")

        input(f"\n  {CYAN}Press Enter to continue...{RESET}")


# ============================================================
# PRODUCT MENUS
# ============================================================

def _pick_supplier() -> tuple[ObjectId | None, str]:
    """
    Show supplier list and let user pick one by ID.

    Returns:
        tuple: (ObjectId | None, supplier_name_str)
    """
    suppliers = supplier_service.get_all_suppliers()
    if not suppliers:
        print_warning("No suppliers in database. Product will have no supplier.")
        return None, "None"

    print_info("Available Suppliers:")
    for s in suppliers:
        print(f"    {str(s['_id'])}  →  {s['name']} ({s['email']})")

    raw_id = get_optional_input("Supplier ID (leave blank for none):")
    if not raw_id:
        return None, "None"

    sup = supplier_service.get_supplier_by_id(raw_id)
    if not sup:
        print_error("Invalid supplier ID — no supplier assigned.")
        return None, "None"

    return sup["_id"], sup["name"]


def menu_add_product() -> None:
    """Prompt for product details and insert into DB."""
    print_header("Add New Product")

    sku = get_input("SKU (e.g., ELEC-001):", is_non_empty_string, "SKU cannot be empty.")
    name = get_input("Product Name:", is_non_empty_string, "Name cannot be empty.")
    category = get_input("Category (e.g., Electronics):", is_non_empty_string)
    price = get_float_input("Price (e.g., 499.99):", min_val=0.01)
    quantity = get_int_input("Initial Quantity:", min_val=0)
    reorder_level = get_int_input("Reorder Level [default 10]:", min_val=0)
    if reorder_level == 0:
        reorder_level = 10

    raw_tags = get_optional_input("Tags (comma-separated, e.g., 'gadget, wireless'):")
    tags = parse_tags(raw_tags) if raw_tags else []

    supplier_id, supplier_name = _pick_supplier()

    result = product_service.add_product(
        sku=sku, name=name, category=category, price=price,
        quantity=quantity, reorder_level=reorder_level,
        supplier_id=supplier_id, tags=tags,
    )

    if result["success"]:
        print_success(f"Product '{name}' added (SKU: {sku.upper()}) | Supplier: {supplier_name}")
    else:
        print_error(result["error"])


def _display_product_table(products: list[dict]) -> None:
    """Format and print a product list table."""
    rows = []
    for p in products:
        qty = p.get("quantity", 0)
        reorder = p.get("reorder_level", 10)
        # Mark low-stock items with a warning symbol
        qty_display = f"⚠ {qty}" if qty <= reorder else str(qty)
        rows.append({
            "sku": p.get("sku", "-"),
            "name": p.get("name", "-"),
            "category": p.get("category", "-"),
            "price": format_currency(p.get("price", 0)),
            "quantity": qty_display,
            "reorder": str(reorder),
        })

    print_table(rows, {
        "sku": "SKU",
        "name": "Name",
        "category": "Category",
        "price": "Price",
        "quantity": "Qty (⚠=low)",
        "reorder": "Reorder Lvl",
    })


def menu_view_products() -> None:
    """Display all products with pagination."""
    print_header("All Products")

    page = 1
    while True:
        data = product_service.get_all_products(page=page)

        if not data["products"]:
            print_warning("No products found.")
            return

        _display_product_table(data["products"])
        print_info(
            f"Page {data['page']} of {data['total_pages']} | "
            f"Total products: {data['total']}"
        )

        if data["total_pages"] <= 1:
            break

        nav = paginate_prompt(page, data["total_pages"])
        if nav == "n" and page < data["total_pages"]:
            page += 1
        elif nav == "p" and page > 1:
            page -= 1
        else:
            break


def menu_search_products() -> None:
    """Search or filter products by name or category."""
    print_header("Search Products")
    print("  1. Search by Name")
    print("  2. Filter by Category")

    choice = input(f"\n  {CYAN}Select option: {RESET}").strip()

    if choice == "1":
        query = get_input("Enter search term:")
        results = product_service.search_products(query)
        print_info(f"Found {len(results)} result(s) for '{query}':")
        _display_product_table(results)

    elif choice == "2":
        categories = product_service.get_distinct_categories()
        if categories:
            print_info("Available categories: " + ", ".join(categories))
        category = get_input("Enter category name:")
        results = product_service.filter_by_category(category)
        print_info(f"Found {len(results)} product(s) in '{category}':")
        _display_product_table(results)
    else:
        print_error("Invalid option.")


def menu_update_product() -> None:
    """Update product fields by SKU."""
    print_header("Update Product")

    sku = get_input("Enter SKU of product to update:")
    product = product_service.get_product_by_sku(sku)

    if not product:
        print_error(f"Product with SKU '{sku.upper()}' not found.")
        return

    print_info(f"Updating: {product['name']} | Current Price: {format_currency(product['price'])}"
               f" | Qty: {product['quantity']}")
    print_info("Press Enter to keep current value.")

    updates = {}

    name = input(f"  {CYAN}New Name [{product['name']}]: {RESET}").strip()
    if name:
        updates["name"] = name

    category = input(f"  {CYAN}New Category [{product['category']}]: {RESET}").strip()
    if category:
        updates["category"] = category

    price_raw = input(f"  {CYAN}New Price [{product['price']}]: {RESET}").strip()
    if price_raw:
        try:
            new_price = float(price_raw)
            if new_price > 0:
                updates["price"] = round(new_price, 2)
            else:
                print_error("Price must be > 0. Skipped.")
        except ValueError:
            print_error("Invalid price. Skipped.")

    reorder_raw = input(
        f"  {CYAN}New Reorder Level [{product['reorder_level']}]: {RESET}"
    ).strip()
    if reorder_raw:
        try:
            updates["reorder_level"] = int(reorder_raw)
        except ValueError:
            print_error("Invalid reorder level. Skipped.")

    tags_raw = input(
        f"  {CYAN}New Tags (comma-sep) [{', '.join(product.get('tags', []))}]: {RESET}"
    ).strip()
    if tags_raw:
        updates["tags"] = parse_tags(tags_raw)

    if not updates:
        print_warning("No changes entered.")
        return

    result = product_service.update_product(sku, updates)
    if result["success"]:
        print_success("Product updated successfully.")
    else:
        print_error(result["error"])


def menu_delete_product() -> None:
    """Delete a product after confirmation."""
    print_header("Delete Product")

    sku = get_input("Enter SKU of product to delete:")
    product = product_service.get_product_by_sku(sku)

    if not product:
        print_error(f"Product with SKU '{sku.upper()}' not found.")
        return

    if not confirm(f"Permanently delete '{product['name']}' (SKU: {sku.upper()})?"):
        print_info("Deletion cancelled.")
        return

    result = product_service.delete_product(sku)
    if result["success"]:
        print_success(f"Product '{sku.upper()}' deleted.")
    else:
        print_error(result["error"])


def product_menu() -> None:
    """Product management sub-menu loop."""
    while True:
        print_header("Product Management")
        print("  1. Add Product")
        print("  2. View All Products (paginated)")
        print("  3. Search / Filter Products")
        print("  4. Update Product")
        print("  5. Delete Product")
        print("  0. Back to Main Menu")

        choice = input(f"\n  {CYAN}Select option: {RESET}").strip()
        if choice == "1":
            menu_add_product()
        elif choice == "2":
            menu_view_products()
        elif choice == "3":
            menu_search_products()
        elif choice == "4":
            menu_update_product()
        elif choice == "5":
            menu_delete_product()
        elif choice == "0":
            break
        else:
            print_error("Invalid option. Enter 1-5 or 0.")

        input(f"\n  {CYAN}Press Enter to continue...{RESET}")


# ============================================================
# STOCK OPERATION MENUS
# ============================================================

def menu_stock_in() -> None:
    """Record a Stock IN (purchase / goods received) operation."""
    print_header("Stock IN — Goods Received")

    sku = get_input("Product SKU:")
    qty = get_int_input("Quantity received:", min_val=1)
    note = get_optional_input("Note (e.g., PO number):")

    result = stock_service.stock_in(sku, qty, note)

    if result["success"]:
        print_success(
            f"Stock IN recorded for '{result['product_name']}' | "
            f"+{qty} units | New Qty: {result['new_quantity']}"
        )
    else:
        print_error(result["error"])


def menu_stock_out() -> None:
    """Record a Stock OUT (sale / dispatch) operation."""
    print_header("Stock OUT — Goods Dispatched")

    sku = get_input("Product SKU:")
    qty = get_int_input("Quantity dispatched:", min_val=1)
    note = get_optional_input("Note (e.g., customer name, invoice):")

    result = stock_service.stock_out(sku, qty, note)

    if result["success"]:
        print_success(
            f"Stock OUT recorded for '{result['product_name']}' | "
            f"-{qty} units | New Qty: {result['new_quantity']}"
        )
    else:
        print_error(result["error"])


def stock_menu() -> None:
    """Stock operations sub-menu loop."""
    while True:
        print_header("Stock Operations")
        print("  1. Stock IN  (goods received / purchase)")
        print("  2. Stock OUT (goods dispatched / sale)")
        print("  0. Back to Main Menu")

        choice = input(f"\n  {CYAN}Select option: {RESET}").strip()
        if choice == "1":
            menu_stock_in()
        elif choice == "2":
            menu_stock_out()
        elif choice == "0":
            break
        else:
            print_error("Invalid option.")

        input(f"\n  {CYAN}Press Enter to continue...{RESET}")


# ============================================================
# REPORT MENUS
# ============================================================

def menu_low_stock_report() -> None:
    """Display products at or below their reorder level."""
    print_header("Low Stock Report")

    results = report_service.low_stock_report()
    if not results:
        print_success("All products are adequately stocked!")
        return

    print_warning(f"{len(results)} product(s) need restocking:")
    _display_product_table(results)


def menu_category_value_report() -> None:
    """Display category-wise stock value using aggregation."""
    print_header("Category-wise Stock Value")

    results = report_service.category_stock_value_report()
    if not results:
        print_warning("No data available.")
        return

    rows = []
    for r in results:
        rows.append({
            "category": r.get("category", "-"),
            "products": str(r.get("total_products", 0)),
            "quantity": str(r.get("total_quantity", 0)),
            "value": format_currency(r.get("total_value", 0)),
        })

    print_table(rows, {
        "category": "Category",
        "products": "Products",
        "quantity": "Total Qty",
        "value": "Stock Value",
    })


def menu_supplier_summary_report() -> None:
    """Display supplier-wise product count and stock value."""
    print_header("Supplier-wise Summary")

    results = report_service.supplier_summary_report()
    if not results:
        print_warning("No data available.")
        return

    rows = []
    for r in results:
        rows.append({
            "supplier": r.get("supplier_name", "-"),
            "email": r.get("supplier_email", "-"),
            "products": str(r.get("product_count", 0)),
            "qty": str(r.get("total_quantity", 0)),
            "value": format_currency(r.get("total_value", 0)),
        })

    print_table(rows, {
        "supplier": "Supplier",
        "email": "Email",
        "products": "Products",
        "qty": "Total Qty",
        "value": "Stock Value",
    })


def menu_monthly_movement_report() -> None:
    """Display monthly stock movement summary."""
    print_header("Monthly Stock Movement Summary")

    results = report_service.monthly_movement_report()
    if not results:
        print_warning("No transaction data available. Run some Stock IN/OUT operations first.")
        return

    rows = []
    for r in results:
        month_name = calendar.month_abbr[r.get("month", 1)]
        rows.append({
            "period": f"{month_name} {r.get('year', '-')}",
            "type": r.get("type", "-"),
            "qty": str(r.get("total_quantity", 0)),
            "txns": str(r.get("transaction_count", 0)),
        })

    print_table(rows, {
        "period": "Month",
        "type": "Type",
        "qty": "Total Units",
        "txns": "Transactions",
    })


def menu_top_sold_report() -> None:
    """Display top 5 most sold products."""
    print_header("Top 5 Most Sold Products")

    results = report_service.top_sold_products_report()
    if not results:
        print_warning("No sales data available. Record some Stock OUT operations first.")
        return

    rows = []
    for i, r in enumerate(results, 1):
        rows.append({
            "rank": str(i),
            "sku": r.get("sku", "-"),
            "name": r.get("product_name", "-"),
            "category": r.get("category", "-"),
            "sold": str(r.get("total_sold", 0)),
            "txns": str(r.get("transaction_count", 0)),
        })

    print_table(rows, {
        "rank": "#",
        "sku": "SKU",
        "name": "Product",
        "category": "Category",
        "sold": "Total Sold",
        "txns": "Transactions",
    })


def reports_menu() -> None:
    """Reports sub-menu loop."""
    while True:
        print_header("Reports & Analytics")
        print("  1. Low Stock Report")
        print("  2. Category-wise Stock Value")
        print("  3. Supplier-wise Summary")
        print("  4. Monthly Stock Movement")
        print("  5. Top 5 Most Sold Products")
        print("  0. Back to Main Menu")

        choice = input(f"\n  {CYAN}Select option: {RESET}").strip()
        if choice == "1":
            menu_low_stock_report()
        elif choice == "2":
            menu_category_value_report()
        elif choice == "3":
            menu_supplier_summary_report()
        elif choice == "4":
            menu_monthly_movement_report()
        elif choice == "5":
            menu_top_sold_report()
        elif choice == "0":
            break
        else:
            print_error("Invalid option. Enter 1-5 or 0.")

        input(f"\n  {CYAN}Press Enter to continue...{RESET}")


# ============================================================
# EXPORT MENU
# ============================================================

def menu_export_csv() -> None:
    """Export products to a CSV file."""
    print_header("Export Products to CSV")

    result = export_products_to_csv()
    if result["success"]:
        print_success(
            f"Exported {result['count']} products to:\n"
            f"  {result['filepath']}"
        )
    else:
        print_error(result["error"])
