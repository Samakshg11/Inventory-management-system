"""
db/indexes.py
-------------
Creates all MongoDB indexes required by the application.

Why indexes matter:
    Without indexes, MongoDB does a full "collection scan" — it reads every
    document to find matches. With indexes, lookups are O(log n) instead of O(n).

    For example, finding a product by SKU without an index on 10,000 products
    means reading 10,000 documents. With a unique index on `sku`, it is
    an instant B-tree lookup.

This module is called ONCE on application startup. MongoDB's create_index()
is idempotent — calling it multiple times with the same definition is safe;
it only creates the index if it does not already exist.

Usage:
    from db.indexes import create_indexes
    create_indexes()
"""

from pymongo import ASCENDING, DESCENDING, TEXT
from db.connection import get_db


def create_indexes(db_name: str | None = None) -> None:
    """
    Create all required indexes across products, suppliers, and transactions.

    Calls collection.create_index() which:
      - Creates the index if it doesn't exist
      - Returns the index name if it already exists (no-op, safe to re-call)

    Args:
        db_name: Optional database name override (used in tests to point
                 to inventory_test_db instead of inventory_db).
    """
    # get_db() returns the Database object; pass db_name if provided
    db = get_db(db_name) if db_name else get_db()

    _create_product_indexes(db)
    _create_supplier_indexes(db)
    _create_transaction_indexes(db)

    print("[DB] All indexes verified / created.")


def _create_product_indexes(db) -> None:
    """
    Create indexes on the 'products' collection.

    Indexes:
        - Unique index on 'sku': ensures no two products share the same SKU.
          MongoDB raises DuplicateKeyError on insert/update if violated.
        - Regular index on 'category': speeds up category-filter queries.
        - Text index on 'name': enables $text search (full-word matching).
          A collection can have only ONE text index; it can cover multiple fields.
    """
    products = db["products"]

    # UNIQUE INDEX on sku — unique=True tells MongoDB to reject duplicate values
    products.create_index(
        [("sku", ASCENDING)],
        unique=True,
        name="idx_products_sku_unique"
    )

    # REGULAR INDEX on category — speeds up queries like:
    # db.products.find({"category": "Electronics"})
    products.create_index(
        [("category", ASCENDING)],
        name="idx_products_category"
    )

    # TEXT INDEX on name — enables queries like:
    # db.products.find({"$text": {"$search": "laptop"}})
    # TEXT indexes tokenise and stem words (e.g., "laptops" matches "laptop").
    products.create_index(
        [("name", TEXT)],
        name="idx_products_name_text"
    )


def _create_supplier_indexes(db) -> None:
    """
    Create indexes on the 'suppliers' collection.

    Indexes:
        - Unique index on 'email': each supplier must have a unique email.
    """
    suppliers = db["suppliers"]

    # UNIQUE INDEX on email
    suppliers.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="idx_suppliers_email_unique"
    )


def _create_transaction_indexes(db) -> None:
    """
    Create indexes on the 'transactions' collection.

    Indexes:
        - COMPOUND index on (product_id ASC, timestamp DESC):
          This speeds up the most common transaction query:
          "Show me the latest stock movements for product X."
          A compound index is stored as a single B-tree keyed on BOTH fields.
          The DESC on timestamp means MongoDB can walk the index in natural
          order for newest-first results without an extra sort step.
    """
    transactions = db["transactions"]

    # COMPOUND INDEX: sort by product_id first, then timestamp newest-first
    transactions.create_index(
        [("product_id", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_transactions_product_time"
    )
