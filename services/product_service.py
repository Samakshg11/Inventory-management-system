"""
services/product_service.py
----------------------------
Business logic for product CRUD operations, including text search
and category filtering.

Key PyMongo concepts demonstrated here:
  - insert_one() with DuplicateKeyError handling (unique SKU index)
  - find() with projection, sort, skip/limit (pagination)
  - $text search using a text index
  - Regex search as fallback
  - update_one() with $set
  - delete_one()
"""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from db.connection import get_collection
from config import PAGE_SIZE


def _now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _products(db_name: str = None):
    """Helper to get the products collection."""
    return get_collection("products", db_name) if db_name else get_collection("products")


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def add_product(
    sku: str,
    name: str,
    category: str,
    price: float,
    quantity: int,
    reorder_level: int = 10,
    supplier_id: Optional[ObjectId] = None,
    tags: Optional[list] = None,
    db_name: str = None,
) -> dict:
    """
    Insert a new product into the 'products' collection.

    Args:
        sku:          Unique stock-keeping unit (will be uppercased).
        name:         Product display name.
        category:     Category string (e.g., "Electronics").
        price:        Unit price (must be > 0).
        quantity:     Initial stock count (>= 0).
        reorder_level: Low-stock alert threshold (default 10).
        supplier_id:  ObjectId of linked supplier, or None.
        tags:         Optional list of tag strings.
        db_name:      Optional DB override for tests.

    Returns:
        dict: {"success": True, "inserted_id": <ObjectId>}
              or {"success": False, "error": <str>}
    """
    col = _products(db_name)
    now = _now()

    doc = {
        "sku": sku.strip().upper(),
        "name": name.strip(),
        "category": category.strip(),
        "price": round(float(price), 2),
        "quantity": int(quantity),
        "reorder_level": int(reorder_level),
        "supplier_id": supplier_id,
        "tags": tags if tags else [],
        "created_at": now,
        "updated_at": now,
    }

    try:
        # insert_one() adds the document; MongoDB generates _id automatically.
        result = col.insert_one(doc)
        return {"success": True, "inserted_id": result.inserted_id}
    except DuplicateKeyError:
        # The unique index on 'sku' prevented duplicate insertion.
        return {"success": False, "error": f"SKU '{sku.upper()}' already exists."}


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_all_products(page: int = 1, db_name: str = None) -> dict:
    """
    Fetch products paginated (PAGE_SIZE rows per page), sorted by SKU.

    Pagination in MongoDB works with .skip() and .limit():
      - skip((page-1) * PAGE_SIZE) jumps past the previous pages.
      - limit(PAGE_SIZE) returns only one page of results.

    Args:
        page:    Page number (1-indexed).
        db_name: Optional DB override.

    Returns:
        dict: {"products": [...], "page": int, "total_pages": int, "total": int}
    """
    col = _products(db_name)

    # count_documents({}) counts ALL documents in the collection.
    total = col.count_documents({})
    total_pages = max(1, -(-total // PAGE_SIZE))  # ceiling division trick

    skip = (page - 1) * PAGE_SIZE

    # find() returns a Cursor; we chain sort/skip/limit and cast to list.
    products = list(
        col.find({})
        .sort("sku", 1)
        .skip(skip)
        .limit(PAGE_SIZE)
    )

    return {
        "products": products,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


def search_products(query: str, db_name: str = None) -> list[dict]:
    """
    Search products by name using the text index, with regex fallback.

    MongoDB $text search:
      - Uses the text index created on the 'name' field.
      - Supports stemming: "laptop" matches "laptops".
      - Much faster than regex on large collections.
      - Regex fallback covers partial word matches the text index might miss.

    Args:
        query:   Search term entered by the user.
        db_name: Optional DB override.

    Returns:
        list[dict]: Matching product documents.
    """
    col = _products(db_name)

    # Try $text search first (uses the text index = fast).
    # textScore sorts by relevance — most relevant documents come first.
    results = list(
        col.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}   # include relevance score
        ).sort([("score", {"$meta": "textScore"})])
    )

    if results:
        return results

    # Fallback: case-insensitive regex search for partial matches.
    # re.IGNORECASE equivalent in MongoDB: $options: "i"
    regex_filter = {"name": {"$regex": query, "$options": "i"}}
    return list(col.find(regex_filter).sort("name", 1))


def filter_by_category(category: str, db_name: str = None) -> list[dict]:
    """
    Return all products in a given category.

    Uses the index on 'category' field for fast lookup.

    Args:
        category: Category name (case-insensitive regex match).
        db_name:  Optional DB override.

    Returns:
        list[dict]: Products matching the category.
    """
    col = _products(db_name)

    # Case-insensitive regex so "electronics" matches "Electronics"
    return list(
        col.find({"category": {"$regex": f"^{category}$", "$options": "i"}})
        .sort("name", 1)
    )


def get_product_by_sku(sku: str, db_name: str = None) -> Optional[dict]:
    """
    Fetch a single product by its SKU (case-insensitive).

    Args:
        sku:     The product SKU to look up.
        db_name: Optional DB override.

    Returns:
        dict | None: The product document or None if not found.
    """
    col = _products(db_name)
    return col.find_one({"sku": sku.strip().upper()})


def get_product_by_id(product_id: str, db_name: str = None) -> Optional[dict]:
    """
    Fetch a single product by its ObjectId string.

    Args:
        product_id: 24-character hex ObjectId string.
        db_name:    Optional DB override.

    Returns:
        dict | None: The product document or None if not found / invalid ID.
    """
    col = _products(db_name)
    try:
        return col.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return None


def get_distinct_categories(db_name: str = None) -> list[str]:
    """
    Return a sorted list of all unique category values.

    distinct() is equivalent to SQL: SELECT DISTINCT category FROM products.

    Args:
        db_name: Optional DB override.

    Returns:
        list[str]: Sorted list of category names.
    """
    col = _products(db_name)
    # distinct() returns a list of unique values for the specified field.
    return sorted(col.distinct("category"))


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_product(sku: str, updates: dict, db_name: str = None) -> dict:
    """
    Update specified fields of a product identified by SKU.

    $set only touches the listed fields; all other fields are left untouched.
    We also always update 'updated_at' to track the modification time.

    Args:
        sku:     SKU of the product to update.
        updates: Dict of field:value pairs to update.
        db_name: Optional DB override.

    Returns:
        dict: {"success": True} or {"success": False, "error": <str>}
    """
    col = _products(db_name)

    # Always stamp the update time
    updates["updated_at"] = _now()

    # update_one() applies $set to the FIRST matching document only.
    result = col.update_one(
        {"sku": sku.strip().upper()},
        {"$set": updates}
    )

    if result.matched_count == 0:
        return {"success": False, "error": f"Product with SKU '{sku.upper()}' not found."}

    return {"success": True}


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_product(sku: str, db_name: str = None) -> dict:
    """
    Permanently delete a product by SKU.

    Note: This does NOT delete related transactions.
    Transactions are kept as historical records even after a product is removed.

    Args:
        sku:     SKU of the product to delete.
        db_name: Optional DB override.

    Returns:
        dict: {"success": True} or {"success": False, "error": <str>}
    """
    col = _products(db_name)

    result = col.delete_one({"sku": sku.strip().upper()})

    if result.deleted_count == 0:
        return {"success": False, "error": f"Product with SKU '{sku.upper()}' not found."}

    return {"success": True}
