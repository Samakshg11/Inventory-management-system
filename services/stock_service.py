"""
services/stock_service.py
--------------------------
Handles Stock IN and Stock OUT operations with atomic MongoDB updates.

KEY CONCEPT — Atomic Stock OUT:
    The naive approach (find → check quantity → update) has a race condition:
    two simultaneous OUT operations could both see enough stock, both proceed,
    and drive the quantity negative.

    The correct approach combines the check and update into ONE atomic operation
    by embedding the guard condition INSIDE the filter:

        update_one(
            {"_id": pid, "quantity": {"$gte": requested_qty}},  # guard
            {"$inc": {"quantity": -requested_qty}}              # update
        )

    If matched_count == 0 after this call, the product either doesn't exist
    OR it had insufficient stock — either way the update did not happen.
    MongoDB guarantees no other write can slip in between the filter and update.
"""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from db.connection import get_collection


def _now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def stock_in(
    sku: str,
    quantity: int,
    note: str = "",
    db_name: str = None,
) -> dict:
    """
    Increase a product's stock quantity (Stock IN / purchase received).

    Steps:
        1. Look up the product by SKU to get its ObjectId.
        2. Atomically increment quantity using $inc.
        3. Log the movement in the transactions collection.

    $inc operator:
        {"$inc": {"quantity": qty}} adds qty to the current value.
        If quantity = 50 and qty = 20, after $inc quantity = 70.
        $inc is atomic — no two operations can corrupt the value.

    Args:
        sku:      Product SKU to restock.
        quantity: Number of units received (must be > 0).
        note:     Optional note (e.g., "PO-1042 from supplier").
        db_name:  Optional DB override for tests.

    Returns:
        dict: {"success": True, "new_quantity": int}
              or {"success": False, "error": str}
    """
    products_col = get_collection("products", db_name) if db_name else get_collection("products")
    transactions_col = (
        get_collection("transactions", db_name) if db_name else get_collection("transactions")
    )

    # Step 1: Find the product to get its _id and current quantity.
    product = products_col.find_one({"sku": sku.strip().upper()})
    if not product:
        return {"success": False, "error": f"Product with SKU '{sku.upper()}' not found."}

    # Step 2: Atomically increment quantity using $inc.
    # We also update 'updated_at' with $set in the same operation —
    # MongoDB allows mixing multiple update operators in one call.
    now = _now()
    products_col.update_one(
        {"_id": product["_id"]},
        {
            "$inc": {"quantity": quantity},          # add quantity to current stock
            "$set": {"updated_at": now},             # update timestamp
        }
    )

    new_quantity = product["quantity"] + quantity

    # Step 3: Log the transaction.
    transactions_col.insert_one({
        "product_id": product["_id"],   # store as ObjectId, not string
        "type": "IN",
        "quantity": quantity,
        "note": note.strip(),
        "timestamp": now,
    })

    return {"success": True, "new_quantity": new_quantity, "product_name": product["name"]}


def stock_out(
    sku: str,
    quantity: int,
    note: str = "",
    db_name: str = None,
) -> dict:
    """
    Decrease a product's stock quantity atomically (Stock OUT / sale).

    THE ATOMIC TRICK (very important — explain this in your viva):
        The filter {"_id": pid, "quantity": {"$gte": quantity}} ensures
        that the update ONLY happens if the current quantity is enough.
        The check and the update happen as a single atomic MongoDB operation.

        If matched_count == 0:
          → Either the product _id was wrong (shouldn't happen after find_one)
          → Or the quantity was insufficient (stock would go negative)
        We treat both as "insufficient stock".

    Args:
        sku:      Product SKU to deduct stock from.
        quantity: Number of units dispatched (must be > 0).
        note:     Optional note (e.g., customer name, invoice number).
        db_name:  Optional DB override for tests.

    Returns:
        dict: {"success": True, "new_quantity": int}
              or {"success": False, "error": str}
    """
    products_col = get_collection("products", db_name) if db_name else get_collection("products")
    transactions_col = (
        get_collection("transactions", db_name) if db_name else get_collection("transactions")
    )

    # Step 1: Find the product.
    product = products_col.find_one({"sku": sku.strip().upper()})
    if not product:
        return {"success": False, "error": f"Product with SKU '{sku.upper()}' not found."}

    now = _now()

    # Step 2: Atomic check-and-decrement.
    # Filter includes "quantity": {"$gte": quantity} as a guard condition.
    # $inc with a negative value decreases the quantity.
    result = products_col.update_one(
        {
            "_id": product["_id"],
            "quantity": {"$gte": quantity},   # GUARD: only match if enough stock
        },
        {
            "$inc": {"quantity": -quantity},   # negative $inc = decrement
            "$set": {"updated_at": now},
        }
    )

    # Step 3: Check if the update happened.
    if result.matched_count == 0:
        # The guard condition failed: current stock < requested quantity.
        return {
            "success": False,
            "error": (
                f"Insufficient stock. Current quantity: {product['quantity']}, "
                f"Requested: {quantity}."
            ),
        }

    new_quantity = product["quantity"] - quantity

    # Step 4: Log the transaction.
    transactions_col.insert_one({
        "product_id": product["_id"],
        "type": "OUT",
        "quantity": quantity,
        "note": note.strip(),
        "timestamp": now,
    })

    return {"success": True, "new_quantity": new_quantity, "product_name": product["name"]}


def get_transaction_history(
    sku: str,
    limit: int = 20,
    db_name: str = None,
) -> list[dict]:
    """
    Fetch recent transaction history for a product.

    Uses the compound index (product_id ASC, timestamp DESC) for fast retrieval.

    Args:
        sku:     Product SKU to look up history for.
        limit:   Maximum number of transactions to return (default 20).
        db_name: Optional DB override.

    Returns:
        list[dict]: Transaction documents, newest first.
    """
    products_col = get_collection("products", db_name) if db_name else get_collection("products")
    transactions_col = (
        get_collection("transactions", db_name) if db_name else get_collection("transactions")
    )

    product = products_col.find_one({"sku": sku.strip().upper()})
    if not product:
        return []

    # The compound index (product_id, timestamp DESC) makes this query fast.
    return list(
        transactions_col.find({"product_id": product["_id"]})
        .sort("timestamp", -1)   # -1 = DESCENDING = newest first
        .limit(limit)
    )
