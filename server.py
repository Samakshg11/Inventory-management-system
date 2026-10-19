"""
server.py
---------
Flask REST API server for the Inventory Stock Management System.

Wraps existing service functions and serves the frontend.

Run with:
    python server.py
"""

import sys
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from bson import ObjectId

from db.connection import get_client, close_connection
from db.indexes import create_indexes
from services.product_service import (
    add_product,
    get_all_products,
    search_products,
    filter_by_category,
    get_product_by_sku,
    get_product_by_id,
    get_distinct_categories,
    update_product,
    delete_product,
)
from services.supplier_service import (
    add_supplier,
    get_all_suppliers,
    get_supplier_by_id,
    update_supplier,
    delete_supplier,
)
from services.stock_service import stock_in, stock_out, get_transaction_history
from services.report_service import (
    low_stock_report,
    category_stock_value_report,
    supplier_summary_report,
    monthly_movement_report,
    top_sold_products_report,
)
from utils.exporter import export_products_to_csv

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)


# ---------------------------------------------------------------------------
# JSON Serialization helper
# ---------------------------------------------------------------------------

def serialize(doc):
    """Convert MongoDB document to JSON-safe dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, dict):
                result[k] = serialize(v)
            elif isinstance(v, list):
                result[k] = [serialize(i) if isinstance(i, dict) else
                             str(i) if isinstance(i, ObjectId) else i
                             for i in v]
            else:
                result[k] = v
        return result
    return doc


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


# ---------------------------------------------------------------------------
# Product Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/products", methods=["GET"])
def api_get_products():
    """Get paginated products. Query params: page, search, category."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    if search:
        products = search_products(search)
        return jsonify({"products": serialize(products), "total": len(products),
                        "page": 1, "total_pages": 1})
    elif category:
        products = filter_by_category(category)
        return jsonify({"products": serialize(products), "total": len(products),
                        "page": 1, "total_pages": 1})
    else:
        result = get_all_products(page)
        result["products"] = serialize(result["products"])
        return jsonify(result)


@app.route("/api/products", methods=["POST"])
def api_add_product():
    """Add a new product."""
    data = request.get_json()
    supplier_id = data.get("supplier_id")
    if supplier_id:
        supplier_id = ObjectId(supplier_id)

    result = add_product(
        sku=data["sku"],
        name=data["name"],
        category=data["category"],
        price=float(data["price"]),
        quantity=int(data["quantity"]),
        reorder_level=int(data.get("reorder_level", 10)),
        supplier_id=supplier_id,
        tags=data.get("tags", []),
    )
    if result["success"]:
        result["inserted_id"] = str(result["inserted_id"])
    return jsonify(result), 201 if result["success"] else 400


@app.route("/api/products/<sku>", methods=["GET"])
def api_get_product(sku):
    """Get a single product by SKU."""
    product = get_product_by_sku(sku)
    if product:
        return jsonify(serialize(product))
    return jsonify({"error": "Product not found"}), 404


@app.route("/api/products/<sku>", methods=["PUT"])
def api_update_product(sku):
    """Update product fields by SKU."""
    data = request.get_json()
    updates = {}
    for field in ["name", "category", "price", "quantity", "reorder_level", "tags"]:
        if field in data:
            if field == "price":
                updates[field] = float(data[field])
            elif field in ("quantity", "reorder_level"):
                updates[field] = int(data[field])
            else:
                updates[field] = data[field]

    if "supplier_id" in data:
        updates["supplier_id"] = ObjectId(data["supplier_id"]) if data["supplier_id"] else None

    result = update_product(sku, updates)
    return jsonify(result), 200 if result["success"] else 404


@app.route("/api/products/<sku>", methods=["DELETE"])
def api_delete_product(sku):
    """Delete a product by SKU."""
    result = delete_product(sku)
    return jsonify(result), 200 if result["success"] else 404


@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    """Get all distinct categories."""
    return jsonify(get_distinct_categories())


# ---------------------------------------------------------------------------
# Supplier Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/suppliers", methods=["GET"])
def api_get_suppliers():
    """Get all suppliers."""
    suppliers = get_all_suppliers()
    return jsonify(serialize(suppliers))


@app.route("/api/suppliers", methods=["POST"])
def api_add_supplier():
    """Add a new supplier."""
    data = request.get_json()
    result = add_supplier(
        name=data["name"],
        email=data["email"],
        phone=data.get("phone", ""),
        address=data.get("address", ""),
    )
    if result["success"]:
        result["inserted_id"] = str(result["inserted_id"])
    return jsonify(result), 201 if result["success"] else 400


@app.route("/api/suppliers/<supplier_id>", methods=["GET"])
def api_get_supplier(supplier_id):
    """Get a single supplier by ID."""
    supplier = get_supplier_by_id(supplier_id)
    if supplier:
        return jsonify(serialize(supplier))
    return jsonify({"error": "Supplier not found"}), 404


@app.route("/api/suppliers/<supplier_id>", methods=["PUT"])
def api_update_supplier(supplier_id):
    """Update supplier fields."""
    data = request.get_json()
    updates = {}
    for field in ["name", "email", "phone", "address"]:
        if field in data:
            updates[field] = data[field]
    result = update_supplier(supplier_id, updates)
    return jsonify(result), 200 if result["success"] else 404


@app.route("/api/suppliers/<supplier_id>", methods=["DELETE"])
def api_delete_supplier(supplier_id):
    """Delete a supplier by ID."""
    result = delete_supplier(supplier_id)
    return jsonify(result), 200 if result["success"] else 400


# ---------------------------------------------------------------------------
# Stock Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/stock/in", methods=["POST"])
def api_stock_in():
    """Perform stock IN operation."""
    data = request.get_json()
    result = stock_in(
        sku=data["sku"],
        quantity=int(data["quantity"]),
        note=data.get("note", ""),
    )
    return jsonify(result), 200 if result["success"] else 400


@app.route("/api/stock/out", methods=["POST"])
def api_stock_out():
    """Perform stock OUT operation."""
    data = request.get_json()
    result = stock_out(
        sku=data["sku"],
        quantity=int(data["quantity"]),
        note=data.get("note", ""),
    )
    return jsonify(result), 200 if result["success"] else 400


@app.route("/api/stock/history/<sku>", methods=["GET"])
def api_transaction_history(sku):
    """Get transaction history for a product by SKU."""
    limit = request.args.get("limit", 20, type=int)
    history = get_transaction_history(sku, limit)
    return jsonify(serialize(history))


# ---------------------------------------------------------------------------
# Report Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/reports/low-stock", methods=["GET"])
def api_low_stock():
    return jsonify(serialize(low_stock_report()))


@app.route("/api/reports/category-value", methods=["GET"])
def api_category_value():
    return jsonify(serialize(category_stock_value_report()))


@app.route("/api/reports/supplier-summary", methods=["GET"])
def api_supplier_summary():
    return jsonify(serialize(supplier_summary_report()))


@app.route("/api/reports/monthly-movement", methods=["GET"])
def api_monthly_movement():
    return jsonify(serialize(monthly_movement_report()))


@app.route("/api/reports/top-sold", methods=["GET"])
def api_top_sold():
    return jsonify(serialize(top_sold_products_report()))


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@app.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    """Export products to CSV."""
    result = export_products_to_csv()
    return jsonify(result), 200 if result["success"] else 400


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Return summary stats for the dashboard."""
    from db.connection import get_collection
    products_col = get_collection("products")
    suppliers_col = get_collection("suppliers")
    transactions_col = get_collection("transactions")

    total_products = products_col.count_documents({})
    total_suppliers = suppliers_col.count_documents({})
    total_transactions = transactions_col.count_documents({})

    # Total inventory value
    pipeline = [
        {"$group": {
            "_id": None,
            "total_value": {"$sum": {"$multiply": ["$price", "$quantity"]}},
            "total_units": {"$sum": "$quantity"},
        }}
    ]
    agg = list(products_col.aggregate(pipeline))
    total_value = round(agg[0]["total_value"], 2) if agg else 0
    total_units = agg[0]["total_units"] if agg else 0

    # Low stock count
    low_stock_count = products_col.count_documents(
        {"$expr": {"$lte": ["$quantity", "$reorder_level"]}}
    )

    return jsonify({
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_transactions": total_transactions,
        "total_value": total_value,
        "total_units": total_units,
        "low_stock_count": low_stock_count,
    })


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        get_client()
    except SystemExit:
        sys.exit(1)

    create_indexes()
    print("\n[SERVER] Starting Flask server at http://localhost:5000")
    app.run(debug=True, port=5000)
