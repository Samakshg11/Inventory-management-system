"""
utils/exporter.py
------------------
CSV export utility for the products collection.

Uses Python's built-in 'csv' module — no extra packages needed.
Saves the exported file to the EXPORT_DIR directory (from config).
"""

import csv
import os
from datetime import datetime

from db.connection import get_collection
from config import EXPORT_DIR


def export_products_to_csv(db_name: str = None) -> dict:
    """
    Export all products from the database to a CSV file.

    The CSV file is named with the current timestamp so multiple exports
    don't overwrite each other (e.g., products_20261019_114500.csv).

    Fields exported:
        SKU, Name, Category, Price, Quantity, Reorder Level, Tags, Created At

    Args:
        db_name: Optional DB override (for tests).

    Returns:
        dict: {"success": True, "filepath": str, "count": int}
              or {"success": False, "error": str}
    """
    col = get_collection("products", db_name) if db_name else get_collection("products")

    # Fetch all products sorted by SKU
    products = list(col.find({}).sort("sku", 1))

    if not products:
        return {"success": False, "error": "No products found to export."}

    # Create the exports directory if it doesn't exist
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Build a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"products_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    # CSV column headers
    fieldnames = [
        "SKU", "Name", "Category", "Price",
        "Quantity", "Reorder Level", "Tags", "Created At"
    ]

    try:
        # newline="" is required on Windows to prevent extra blank lines.
        # On macOS/Linux it has no effect but is still good practice.
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for product in products:
                writer.writerow({
                    "SKU": product.get("sku", ""),
                    "Name": product.get("name", ""),
                    "Category": product.get("category", ""),
                    "Price": product.get("price", 0),
                    "Quantity": product.get("quantity", 0),
                    "Reorder Level": product.get("reorder_level", 10),
                    # Join list of tags into comma-separated string
                    "Tags": ", ".join(product.get("tags", [])),
                    "Created At": product.get("created_at", "").strftime("%Y-%m-%d %H:%M")
                    if product.get("created_at") else "",
                })

        return {"success": True, "filepath": filepath, "count": len(products)}

    except OSError as e:
        return {"success": False, "error": f"Could not write file: {e}"}
