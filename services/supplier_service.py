"""
services/supplier_service.py
-----------------------------
Business logic for supplier CRUD operations.

All PyMongo operations are here. The CLI layer only calls these functions
and never touches the database directly.
"""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from db.connection import get_collection


def _now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def add_supplier(
    name: str,
    email: str,
    phone: str = "",
    address: str = "",
    db_name: str = None,
) -> dict:
    """
    Insert a new supplier document into the 'suppliers' collection.

    Args:
        name:    Supplier company name.
        email:   Unique contact email (validated before calling).
        phone:   Optional phone number.
        address: Optional physical address.
        db_name: Optional DB override (used in tests).

    Returns:
        dict: {"success": True, "inserted_id": <ObjectId>}
              or {"success": False, "error": <message>}
    """
    col = get_collection("suppliers", db_name) if db_name else get_collection("suppliers")

    doc = {
        "name": name.strip(),
        "email": email.strip().lower(),   # normalise to lowercase
        "phone": phone.strip(),
        "address": address.strip(),
        "created_at": _now(),
    }

    try:
        # insert_one() adds the document and returns an InsertOneResult.
        # result.inserted_id is the auto-generated ObjectId for the new doc.
        result = col.insert_one(doc)
        return {"success": True, "inserted_id": result.inserted_id}
    except DuplicateKeyError:
        # The unique index on 'email' raised this error.
        # We catch it and return a friendly message instead of a traceback.
        return {"success": False, "error": f"A supplier with email '{email}' already exists."}


def get_all_suppliers(db_name: str = None) -> list[dict]:
    """
    Fetch all supplier documents, sorted alphabetically by name.

    Returns:
        list[dict]: List of supplier documents (may be empty).
    """
    col = get_collection("suppliers", db_name) if db_name else get_collection("suppliers")

    # find() with no filter returns all documents.
    # sort() accepts a list of (field, direction) tuples.
    return list(col.find({}).sort("name", 1))


def get_supplier_by_id(supplier_id: str, db_name: str = None) -> Optional[dict]:
    """
    Fetch a single supplier by their ObjectId string.

    Args:
        supplier_id: 24-character hex string ObjectId.
        db_name:     Optional DB override.

    Returns:
        dict | None: The supplier document, or None if not found.
    """
    col = get_collection("suppliers", db_name) if db_name else get_collection("suppliers")

    try:
        # ObjectId() converts the hex string to a BSON ObjectId type.
        # MongoDB _id fields are ObjectIds, not plain strings.
        oid = ObjectId(supplier_id)
    except InvalidId:
        return None

    return col.find_one({"_id": oid})


def update_supplier(supplier_id: str, updates: dict, db_name: str = None) -> dict:
    """
    Update specified fields of an existing supplier.

    Uses $set so only the provided fields are updated —
    other fields in the document remain unchanged.

    Args:
        supplier_id: 24-char hex ObjectId string of the supplier to update.
        updates:     Dict of fields to update, e.g. {"phone": "9876543210"}.
        db_name:     Optional DB override.

    Returns:
        dict: {"success": True} or {"success": False, "error": <message>}
    """
    col = get_collection("suppliers", db_name) if db_name else get_collection("suppliers")

    try:
        oid = ObjectId(supplier_id)
    except InvalidId:
        return {"success": False, "error": "Invalid supplier ID format."}

    # $set only updates the specified fields; other fields stay as-is.
    result = col.update_one({"_id": oid}, {"$set": updates})

    if result.matched_count == 0:
        return {"success": False, "error": "Supplier not found."}

    return {"success": True}


def delete_supplier(supplier_id: str, db_name: str = None) -> dict:
    """
    Delete a supplier ONLY if no products are linked to them.

    Why check products first?
        Referential integrity — if we delete a supplier that products
        still point to, those products will have a dangling supplier_id.
        MongoDB does NOT enforce foreign keys like SQL does, so we
        enforce this rule manually in the service layer.

    Args:
        supplier_id: 24-char hex ObjectId string.
        db_name:     Optional DB override.

    Returns:
        dict: {"success": True} or {"success": False, "error": <message>}
    """
    col = get_collection("suppliers", db_name) if db_name else get_collection("suppliers")
    products_col = get_collection("products", db_name) if db_name else get_collection("products")

    try:
        oid = ObjectId(supplier_id)
    except InvalidId:
        return {"success": False, "error": "Invalid supplier ID format."}

    # Check if any product still references this supplier.
    # count_documents() is more efficient than find() when we only need the count.
    linked_count = products_col.count_documents({"supplier_id": oid})
    if linked_count > 0:
        return {
            "success": False,
            "error": (
                f"Cannot delete: {linked_count} product(s) are still linked to this supplier. "
                "Reassign or delete those products first."
            ),
        }

    result = col.delete_one({"_id": oid})

    if result.deleted_count == 0:
        return {"success": False, "error": "Supplier not found."}

    return {"success": True}
