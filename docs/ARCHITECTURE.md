# Architecture Document
## Inventory Stock Management System

**Version:** 1.0  
**Date:** 2026-10-19  

---

## 1. High-Level Architecture

The system follows a classic **3-layer architecture** adapted for a CLI application:

```
+----------------------------------------------------------+
|                    CLI Layer                              |
|   main.py  -->  cli/menus.py  -->  cli/helpers.py         |
|   (Entry point, menu loop, user input/output)            |
+----------------------------------------------------------+
                          |
                          | calls
                          v
+----------------------------------------------------------+
|                  Service Layer                            |
|   services/product_service.py                            |
|   services/supplier_service.py                           |
|   services/stock_service.py                              |
|   services/report_service.py                             |
|   (Business logic, validation, PyMongo operations)       |
+----------------------------------------------------------+
                          |
                          | uses
                          v
+----------------------------------------------------------+
|                 Database Layer                            |
|   db/connection.py  (MongoClient singleton)              |
|   db/indexes.py     (index creation on startup)          |
|   (No business logic here — only connection management)  |
+----------------------------------------------------------+
                          |
                          | connects to
                          v
+----------------------------------------------------------+
|              MongoDB (local instance)                    |
|   Database: inventory_db                                 |
|   Collections: products, suppliers, transactions         |
+----------------------------------------------------------+
```

**Key design decision:** The CLI layer NEVER touches PyMongo directly. It only calls service functions. This means you can swap the CLI for a web UI later without rewriting any business logic.

---

## 2. Layer Responsibilities

### 2.1 CLI Layer (`main.py`, `cli/`)

- Display menus and prompts to the user
- Read raw string input from the terminal
- Call `cli/helpers.py` to validate/convert input types
- Pass validated data to the service layer
- Display results returned from services (using `tabulate`)
- Handle `KeyboardInterrupt` (Ctrl+C) gracefully

**Does NOT:** Contain any MongoDB queries or business rules.

### 2.2 Service Layer (`services/`)

- Receive clean, validated inputs from the CLI layer
- Apply business rules (e.g., "quantity must not go below 0")
- Construct MongoDB documents (using builder functions from `models/schemas.py`)
- Execute PyMongo CRUD operations and aggregation pipelines
- Return plain Python dicts/lists to the CLI layer
- Raise or catch PyMongo exceptions and convert to user-friendly messages

**Does NOT:** Print anything to the terminal.

### 2.3 Database Layer (`db/`)

- `connection.py`: Creates and caches a single `MongoClient` instance (singleton pattern)
- `indexes.py`: Creates all indexes on application startup via `create_indexes()`
- Exposes helper functions `get_db()` and `get_collection(name)` used by services

**Does NOT:** Execute business queries.

### 2.4 Models (`models/schemas.py`)

- Defines Python `dataclass` structures for type hints and IDE support
- Provides builder functions (`build_product_doc()`, etc.) that return ready-to-insert dicts with `datetime.utcnow()` timestamps and default values

### 2.5 Utils (`utils/`)

- `validators.py`: Pure functions that validate inputs (e.g., `is_valid_email()`, `is_positive_float()`)
- `exporter.py`: CSV export logic using the built-in `csv` module

---

## 3. Data Flow Examples

### 3.1 Adding a Product

```
User types product details
        |
        v
cli/menus.py  -- calls --> cli/helpers.py (validate input types)
        |
        v
services/product_service.py
    build_product_doc()           # from models/schemas.py
    db.products.insert_one(doc)   # PyMongo insert
    handle DuplicateKeyError      # catch & return error message
        |
        v
cli/menus.py  -- prints --> "Product added successfully!"
```

### 3.2 Stock OUT (Atomic Update)

```
User enters: SKU="ELEC-001", quantity=5
        |
        v
services/stock_service.py
    # Step 1: Find product by SKU to get its _id
    product = db.products.find_one({"sku": "ELEC-001"})

    # Step 2: Atomic check-and-update (single operation, no race condition)
    result = db.products.update_one(
        {"_id": product["_id"], "quantity": {"$gte": 5}},  # filter = guard
        {"$inc": {"quantity": -5}, "$set": {"updated_at": now}}
    )

    # Step 3: If matched_count == 0, stock was insufficient
    if result.matched_count == 0:
        return error "Insufficient stock"

    # Step 4: Log transaction
    db.transactions.insert_one({
        "product_id": product["_id"],
        "type": "OUT",
        "quantity": 5,
        "timestamp": now
    })
        |
        v
cli/menus.py -- prints --> "Stock OUT successful. New quantity: 45"
```

### 3.3 Aggregation Report (Category-wise Stock Value)

```
services/report_service.py
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "total_products": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_value": {
                    "$sum": {"$multiply": ["$price", "$quantity"]}
                }
            }
        },
        {"$sort": {"total_value": -1}}
    ]
    results = list(db.products.aggregate(pipeline))
        |
        v
cli/menus.py -- tabulate(results) --> formatted table
```

---

## 4. Database Connection — Singleton Pattern

```python
# db/connection.py
_client = None  # module-level cache

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
        _client.admin.command("ping")  # fail fast if MongoDB is down
    return _client

def get_db(db_name: str = DB_NAME) -> Database:
    return get_client()[db_name]
```

**Why singleton?** Creating a new `MongoClient` on every function call is expensive. PyMongo's `MongoClient` manages an internal connection pool; one client instance per process is the recommended pattern.

---

## 5. Index Strategy

| Collection | Index | Type | Purpose |
|------------|-------|------|---------|
| products | sku | Unique | Enforce uniqueness; fast lookup by SKU |
| products | category | Regular | Fast category filter queries |
| products | name | Text | Full-text search by name |
| suppliers | email | Unique | Enforce uniqueness; fast lookup by email |
| transactions | (product_id, timestamp desc) | Compound | Fast retrieval of a product's transaction history |

**Indexes are created once** via `create_indexes()` called from `main.py` on startup. MongoDB is idempotent for index creation — calling it multiple times is safe.

---

## 6. Error Handling Strategy

| Error | Source | How Handled |
|-------|--------|-------------|
| `DuplicateKeyError` | pymongo.errors | Caught in service layer; friendly message returned |
| `ConnectionFailure` | pymongo.errors | Caught in `connection.py`; app exits with clear message |
| Insufficient stock | Business logic | `matched_count == 0` after atomic update |
| Invalid ObjectId | bson.errors | Caught with `bson.errors.InvalidId`; friendly message |
| Empty collection | Business logic | Check `if not results:` and print "No records found" |
| Invalid input | CLI helpers | Validate before calling service; re-prompt user |

---

## 7. Atomic Update — Why It Matters

Without atomicity, a naive Stock OUT implementation would be:
```python
# WRONG — race condition possible in concurrent scenarios
product = db.products.find_one({"sku": sku})
if product["quantity"] >= qty:
    db.products.update_one({"sku": sku}, {"$inc": {"quantity": -qty}})
```
Between the `find_one` and `update_one`, another process could also reduce the quantity, leading to **negative stock**.

The correct approach combines the check and update into **one atomic operation**:
```python
# CORRECT — filter acts as a guard condition
result = db.products.update_one(
    {"_id": pid, "quantity": {"$gte": qty}},  # only match if enough stock
    {"$inc": {"quantity": -qty}}
)
# If matched_count == 0, either the product doesn't exist OR stock was insufficient
```
MongoDB guarantees that no other write can slip in between the filter check and the update.

---

## 8. Module Dependency Map

```
main.py
  |-- config.py
  |-- db/connection.py
  |-- db/indexes.py
  |-- cli/menus.py
        |-- cli/helpers.py
        |-- services/product_service.py
        |     |-- db/connection.py
        |     |-- models/schemas.py
        |     |-- utils/validators.py
        |-- services/supplier_service.py
        |     |-- db/connection.py
        |     |-- models/schemas.py
        |-- services/stock_service.py
        |     |-- db/connection.py
        |     |-- models/schemas.py
        |-- services/report_service.py
              |-- db/connection.py
  |-- utils/exporter.py
        |-- db/connection.py
```

No circular imports. The DB layer is at the bottom and imported by all services. Services are imported only by the CLI layer.

---

## 9. Configuration Management

All environment-specific values live in `.env`:

```ini
MONGO_URI=mongodb://localhost:27017
DB_NAME=inventory_db
TEST_DB_NAME=inventory_test_db
PAGE_SIZE=10
```

`config.py` loads these with `python-dotenv` and exposes them as module-level constants. Every other module imports from `config.py` — never from `.env` directly. This means switching from local MongoDB to Atlas only requires changing one line in `.env`.

---

## 10. Testing Architecture

```
tests/
  conftest.py          # Shared fixtures:
                       #   - get test DB client
                       #   - yield collections
                       #   - delete_many({}) teardown after each test
  test_products.py     # Unit tests for product_service functions
  test_stock.py        # Unit tests for stock_service (IN, OUT, insufficient)
  test_reports.py      # Unit tests for report_service aggregations
```

**Key principle:** Tests import service functions directly and pass a test collection object. Tests do NOT go through the CLI. This isolates the business logic and makes tests fast.

---

## 11. Sequence Diagram — Application Startup

```
main.py
  |
  +-- config.py: load .env values
  |
  +-- db/connection.py: MongoClient("mongodb://localhost:27017")
  |       |
  |       +-- ping MongoDB server (raises ConnectionFailure if down)
  |
  +-- db/indexes.py: create_indexes()
  |       |
  |       +-- products: unique sku, category, text name
  |       +-- suppliers: unique email
  |       +-- transactions: compound (product_id, timestamp desc)
  |
  +-- cli/menus.py: show_main_menu() -- infinite loop until user exits
```

---

## 12. Key Design Decisions Summary

| Decision | Rationale |
|----------|-----------|
| CLI over Web UI | Simpler to implement; no HTML/JS; easier to explain in viva |
| MongoDB singleton | Efficient connection pooling; one client per process |
| References over embedding | Transactions grow unboundedly; products need independent queries |
| Atomic $inc with filter | Prevents negative stock without transactions or locks |
| Separate test DB | Tests don't pollute production data; easy cleanup |
| Dataclasses for models | Type hints and IDE support without heavy ORM overhead |
| Aggregation for reports | Demonstrates MongoDB's most powerful feature for academic credit |
