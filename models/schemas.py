"""
models/schemas.py
-----------------
Defines the shape of each MongoDB document using Python dataclasses
and provides builder functions that return ready-to-insert dictionaries.

Why dataclasses?
    - Give us type hints and IDE autocompletion without a heavy ORM.
    - We store data in MongoDB as plain dicts, so these are only used
      for in-memory representation and documentation — not for ORM mapping.

Why builder functions?
    - They set default values (timestamps, reorder_level) automatically.
    - They ensure every document has the same required fields.
    - Services call build_*() to create docs before inserting into MongoDB.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Dataclasses — for type hints and IDE support
# ---------------------------------------------------------------------------

@dataclass
class Product:
    """Represents a product document in the 'products' collection."""
    sku: str
    name: str
    category: str
    price: float
    quantity: int
    reorder_level: int = 10
    supplier_id: Optional[ObjectId] = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class Supplier:
    """Represents a supplier document in the 'suppliers' collection."""
    name: str
    email: str
    phone: str = ""
    address: str = ""
    created_at: datetime = field(default_factory=_now)


@dataclass
class Transaction:
    """Represents a stock movement record in the 'transactions' collection."""
    product_id: ObjectId
    type: str          # "IN" or "OUT"
    quantity: int
    note: str = ""
    timestamp: datetime = field(default_factory=_now)


# ---------------------------------------------------------------------------
# Builder functions — return plain dicts ready for insert_one()
# ---------------------------------------------------------------------------

def build_product_doc(
    sku: str,
    name: str,
    category: str,
    price: float,
    quantity: int,
    reorder_level: int = 10,
    supplier_id: Optional[ObjectId] = None,
    tags: Optional[list[str]] = None,
) -> dict:
    """
    Build a product document dict ready to be passed to insert_one().

    Args:
        sku: Unique stock-keeping unit identifier (e.g., "ELEC-001").
        name: Display name of the product.
        category: Product category (e.g., "Electronics").
        price: Unit price; must be > 0 (validated before calling this).
        quantity: Initial stock count; must be >= 0.
        reorder_level: Alert threshold; defaults to 10.
        supplier_id: ObjectId of the linked supplier (or None).
        tags: Optional list of search tags.

    Returns:
        dict: A MongoDB-ready document with timestamps set to UTC now.
    """
    now = _now()
    return {
        "sku": sku.strip().upper(),          # normalise SKU to uppercase
        "name": name.strip(),
        "category": category.strip(),
        "price": round(float(price), 2),     # store as rounded float
        "quantity": int(quantity),
        "reorder_level": int(reorder_level),
        "supplier_id": supplier_id,           # ObjectId or None
        "tags": tags if tags else [],         # default to empty list
        "created_at": now,
        "updated_at": now,
    }


def build_supplier_doc(
    name: str,
    email: str,
    phone: str = "",
    address: str = "",
) -> dict:
    """
    Build a supplier document dict ready for insert_one().

    Args:
        name: Supplier company name.
        email: Unique contact email.
        phone: Contact phone number (optional).
        address: Physical address (optional).

    Returns:
        dict: A MongoDB-ready supplier document.
    """
    return {
        "name": name.strip(),
        "email": email.strip().lower(),   # normalise email to lowercase
        "phone": phone.strip(),
        "address": address.strip(),
        "created_at": _now(),
    }


def build_transaction_doc(
    product_id: ObjectId,
    movement_type: str,
    quantity: int,
    note: str = "",
) -> dict:
    """
    Build a transaction (stock movement) document ready for insert_one().

    Args:
        product_id: ObjectId of the product that moved.
        movement_type: "IN" (stock received) or "OUT" (stock dispatched).
        quantity: Number of units moved; must be > 0.
        note: Optional note (e.g., PO number, customer name).

    Returns:
        dict: A MongoDB-ready transaction document.
    """
    return {
        "product_id": product_id,     # stored as ObjectId (not string)
        "type": movement_type.upper(),
        "quantity": int(quantity),
        "note": note.strip(),
        "timestamp": _now(),
    }
