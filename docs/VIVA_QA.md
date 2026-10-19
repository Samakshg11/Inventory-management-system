# VIVA Q&A — Inventory Stock Management System
## 25 Likely Viva Questions with Detailed Answers

---

### Section 1: MongoDB Basics

**Q1. What is MongoDB and how is it different from a relational database (SQL)?**

MongoDB is a NoSQL document database that stores data as JSON-like documents (BSON).

| Feature | MongoDB | SQL (MySQL/PostgreSQL) |
|---------|---------|------------------------|
| Data format | BSON documents | Rows in tables |
| Schema | Flexible (schema-less) | Fixed schema |
| Joins | $lookup aggregation stage | JOIN keyword |
| Relationships | Manual via ObjectId references | Foreign keys enforced |
| Scaling | Horizontal (sharding) | Vertical (bigger server) |
| Transactions | Multi-document ACID (v4+) | Full ACID |

We chose MongoDB because our products have flexible attributes (tags, varying fields per category) that fit naturally into a document model.

---

**Q2. What is BSON? How is it different from JSON?**

BSON stands for **Binary JSON**. MongoDB stores documents internally as BSON, which:
- Supports more data types than JSON (e.g., ObjectId, DateTime, int32, int64, Decimal128)
- Is binary-encoded, making it faster for MongoDB to parse than text-based JSON
- Supports additional types like `Date`, `Binary`, `Regex` that JSON doesn't have natively

When you retrieve documents in Python via PyMongo, BSON is automatically converted to Python dicts.

---

**Q3. What is an ObjectId in MongoDB?**

An ObjectId is MongoDB's default value for the `_id` field. It is a 12-byte (24 hex character) value composed of:
- **4 bytes**: Unix timestamp of creation
- **5 bytes**: Random value (unique per machine/process)
- **3 bytes**: Auto-incrementing counter

ObjectId guarantees global uniqueness without requiring a central counter. In this project, `supplier_id` in products is stored as an ObjectId reference to the supplier's `_id`.

---

**Q4. What is the difference between `find()` and `find_one()` in PyMongo?**

- `find_one(filter)`: Returns the **first** matching document as a dict, or `None` if not found.
- `find(filter)`: Returns a **Cursor** object (lazy iterator) over all matching documents.

```python
# find_one — returns one dict
product = db.products.find_one({"sku": "ELEC-001"})

# find — returns Cursor, cast to list to get all docs
all_products = list(db.products.find({"category": "Electronics"}))
```

We use `find_one` when looking up by a unique field (SKU, email) and `find` when expecting multiple results.

---

### Section 2: Indexes

**Q5. What are indexes in MongoDB and why are they important?**

An index is a data structure (B-tree) that MongoDB maintains alongside a collection. It stores a sorted copy of selected field values with pointers to the actual documents.

**Without an index:** MongoDB scans every document (collection scan) — O(n).  
**With an index:** MongoDB walks the B-tree — O(log n).

In this project:
- `sku` index means finding a product by SKU is instant even with 100,000 products.
- `category` index speeds up category filter queries.
- Text index on `name` enables `$text` search.

---

**Q6. What is a Unique Index? Give an example from your project.**

A unique index enforces that no two documents in a collection have the same value for the indexed field. MongoDB raises a `DuplicateKeyError` if you try to insert a duplicate.

In this project:
```python
products.create_index([("sku", ASCENDING)], unique=True)
suppliers.create_index([("email", ASCENDING)], unique=True)
```
If you try to add a second product with SKU "ELEC-001", MongoDB rejects it. We catch this in `product_service.py` and show a friendly error.

---

**Q7. What is a Compound Index? Why did you use one on transactions?**

A compound index covers **multiple fields** in a single B-tree. It is useful for queries that filter or sort on multiple fields together.

In this project:
```python
transactions.create_index([("product_id", ASCENDING), ("timestamp", DESCENDING)])
```
This index is optimal for the most common transaction query: "Give me the latest 20 transactions for product X." Both the filter (`product_id`) and sort (`timestamp DESC`) are covered by one index — no separate sort step needed.

---

**Q8. What is a Text Index in MongoDB? How did you use it?**

A text index tokenises string fields and stores stemmed words for full-text search.

```python
products.create_index([("name", TEXT)])
```
Allows queries like:
```python
db.products.find({"$text": {"$search": "keyboard"}})
```
Text search is case-insensitive and stem-aware ("keyboards" matches "keyboard"). A collection can only have ONE text index, but it can span multiple fields. We added a regex fallback for partial matches.

---

### Section 3: CRUD Operations

**Q9. How does `insert_one()` work in PyMongo? What does it return?**

`insert_one(document)` sends a single document to MongoDB and returns an `InsertOneResult` object.

```python
result = db.products.insert_one({"sku": "ELEC-001", "name": "Headphones"})
print(result.inserted_id)  # The auto-generated ObjectId
```
MongoDB automatically adds `_id` to the document if not provided.

---

**Q10. What is `update_one()` with `$set`? How is it different from replacing the document?**

`update_one(filter, update)` modifies the **first** matching document.

- `$set` only updates the specified fields; all other fields remain unchanged.
- `replace_one()` replaces the entire document except `_id`.

```python
# Only updates 'price' — other fields untouched
db.products.update_one({"sku": "ELEC-001"}, {"$set": {"price": 2999.0}})

# Replaces EVERYTHING in the document
db.products.replace_one({"sku": "ELEC-001"}, {"sku": "ELEC-001", "price": 2999.0})
```

In this project we always use `$set` so a partial update doesn't accidentally erase other fields.

---

**Q11. What is `$inc` and where did you use it?**

`$inc` atomically increments (or decrements) a numeric field by a given amount.

```python
# Add 20 to quantity — atomic, no read needed first
db.products.update_one({"_id": pid}, {"$inc": {"quantity": 20}})

# Subtract 5 from quantity (using negative value)
db.products.update_one({"_id": pid}, {"$inc": {"quantity": -5}})
```
We use `$inc` for Stock IN and Stock OUT because it is atomic — it guarantees the quantity changes by exactly the requested amount even if multiple operations happen simultaneously.

---

### Section 4: Atomic Operations

**Q12. What is the race condition problem in Stock OUT? How did you solve it atomically?**

**The problem:** A naive approach reads the quantity, checks if it's enough, then updates:
```python
# WRONG — vulnerable to race conditions
product = db.products.find_one({"sku": sku})
if product["quantity"] >= qty:
    db.products.update_one({"sku": sku}, {"$inc": {"quantity": -qty}})
```
Between `find_one` and `update_one`, another process could also read the quantity and both updates would proceed, driving quantity negative.

**The solution:** Embed the guard condition inside the filter:
```python
# CORRECT — atomic check-and-update
result = db.products.update_one(
    {"_id": pid, "quantity": {"$gte": qty}},  # guard: only match if enough stock
    {"$inc": {"quantity": -qty}}
)
if result.matched_count == 0:
    # guard failed — insufficient stock
```
MongoDB guarantees this is a single atomic operation — no other write can slip between the filter check and the update.

---

**Q13. What does `matched_count` vs `modified_count` mean in an update result?**

`UpdateResult` from `update_one()` has two important properties:
- `matched_count`: How many documents matched the filter (0 or 1 for `update_one`).
- `modified_count`: How many documents were actually changed.

They can differ: if the new value equals the old value, `matched_count=1` but `modified_count=0`.

In the Stock OUT atomic update, we check `matched_count`:
- `matched_count == 0` → Either the product doesn't exist OR stock was insufficient.
- `matched_count == 1` → Update succeeded.

---

### Section 5: Aggregation Pipelines

**Q14. What is an Aggregation Pipeline in MongoDB? How does it work?**

An aggregation pipeline is an array of stages. Each stage transforms the documents flowing through it and passes the result to the next stage — like a Unix pipe.

```python
pipeline = [
    {"$match": {"type": "OUT"}},            # Stage 1: filter
    {"$group": {"_id": "$product_id",       # Stage 2: group and sum
                "total": {"$sum": "$quantity"}}},
    {"$sort": {"total": -1}},               # Stage 3: sort
    {"$limit": 5},                          # Stage 4: top 5
]
results = list(db.transactions.aggregate(pipeline))
```

---

**Q15. Explain the `$group` stage with an example from your project.**

`$group` is equivalent to SQL's `GROUP BY`. It groups documents by `_id` and computes aggregated values.

```python
{
    "$group": {
        "_id": "$category",                       # GROUP BY category
        "total_products": {"$sum": 1},            # COUNT(*)
        "total_quantity": {"$sum": "$quantity"},   # SUM(quantity)
        "total_value": {
            "$sum": {"$multiply": ["$price", "$quantity"]}  # SUM(price*qty)
        }
    }
}
```
This computes category-wise stock value in one MongoDB operation — no Python loop needed.

---

**Q16. What is `$lookup`? Give an example from your project.**

`$lookup` is MongoDB's equivalent of SQL's LEFT JOIN. It joins documents from another collection.

```python
{
    "$lookup": {
        "from": "suppliers",      # join this collection
        "localField": "_id",      # field in current doc (supplier_id after $group)
        "foreignField": "_id",    # field in suppliers doc
        "as": "supplier_info",    # result stored as array in this field
    }
}
```
After this stage, each document has a `supplier_info` array containing the matched supplier(s). We then use `$unwind` to flatten this array into a single document.

---

**Q17. What is `$unwind`? Why is it needed after `$lookup`?**

`$lookup` adds an array field to each document. `$unwind` deconstructs that array — it creates one output document per array element.

```python
{"$unwind": {"path": "$supplier_info", "preserveNullAndEmptyArrays": True}}
```

`preserveNullAndEmptyArrays: True` keeps products that have no matching supplier (otherwise they'd be dropped from the results, like an INNER JOIN instead of LEFT JOIN).

---

**Q18. What pipeline operators did you use in the Top 5 Sold Products report?**

```
$match (filter OUT only) →
$group (sum qty per product) →
$sort (highest sold first) →
$limit (top 5) →
$lookup (join product name from products collection) →
$unwind (flatten the joined array) →
$project (clean output fields)
```
This demonstrates 7 different pipeline stages in one query — a great example for exam marks.

---

### Section 6: Schema Design

**Q19. Why did you use references (ObjectId) instead of embedded documents for the supplier-product relationship?**

Two reasons:
1. **Independent queries**: We often need to list all products regardless of supplier, or list all suppliers independently. With embedding, you'd have to scan all products to list suppliers.
2. **Unbounded growth**: Transactions grow continuously. If embedded inside product documents, a product document would grow without bound, hitting MongoDB's 16MB document limit.

The rule of thumb: **embed when you always access data together; reference when you access data independently or when one side can grow unboundedly**.

---

**Q20. What is the difference between `created_at` and `updated_at` fields? How do you maintain `updated_at`?**

- `created_at`: Set once at insert time (`datetime.utcnow()`) and never changed.
- `updated_at`: Set at insert time, then updated via `$set` every time the document is modified.

In `product_service.update_product()`:
```python
updates["updated_at"] = datetime.now(timezone.utc)
result = col.update_one({"sku": sku}, {"$set": updates})
```
MongoDB does NOT auto-update timestamps — we handle this in the service layer.

---

### Section 7: PyMongo and Python

**Q21. What is the Singleton pattern used in `db/connection.py`? Why is it important?**

Singleton ensures only ONE `MongoClient` instance is created for the entire application lifetime.

```python
_client = None  # module-level cache

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client
```

**Why important?** `MongoClient` manages an internal **connection pool** (multiple TCP connections to MongoDB). Creating a new `MongoClient` on every function call wastes resources and is much slower. The PyMongo documentation explicitly recommends one client per process.

---

**Q22. What is `DuplicateKeyError` and when is it raised?**

`pymongo.errors.DuplicateKeyError` is raised when an insert or update violates a unique index.

```python
from pymongo.errors import DuplicateKeyError

try:
    db.products.insert_one({"sku": "ELEC-001", ...})
except DuplicateKeyError:
    print("SKU already exists!")
```

In this project, unique indexes on `sku` (products) and `email` (suppliers) cause this error. We always wrap inserts in try/except and return a user-friendly message instead of letting the exception crash the app.

---

**Q23. What is `count_documents()` and when did you use it?**

`count_documents(filter)` returns the number of documents matching the filter — more efficient than fetching all documents and counting in Python.

Usage in this project:
```python
# Check if any products are linked to a supplier before deleting
linked_count = products_col.count_documents({"supplier_id": oid})
if linked_count > 0:
    return {"error": f"{linked_count} products still linked"}
```
We also use it for pagination: `total = col.count_documents({})` to compute total pages.

---

**Q24. What is `distinct()` in PyMongo?**

`distinct(field)` returns a list of all unique values for a given field across the entire collection — equivalent to `SELECT DISTINCT field FROM collection`.

```python
categories = db.products.distinct("category")
# Returns: ["Books", "Clothing", "Electronics", ...]
```
We use this to show the user available categories when searching/filtering.

---

**Q25. How did you implement pagination in the product listing? Explain skip and limit.**

Pagination in MongoDB uses `.skip()` and `.limit()` on a cursor:

```python
PAGE_SIZE = 10
skip = (page - 1) * PAGE_SIZE      # e.g., page 3 → skip 20

products = list(
    db.products.find({})
    .sort("sku", 1)
    .skip(skip)                     # jump past previous pages
    .limit(PAGE_SIZE)               # return only PAGE_SIZE documents
)
```

**Total pages formula:**
```python
total = db.products.count_documents({})
total_pages = ceil(total / PAGE_SIZE)   # or: -(-total // PAGE_SIZE) in Python
```

**Limitation:** `skip()` reads and discards the skipped documents, so it becomes slower on very large collections (page 1000 of 10000). For production, cursor-based pagination (using `_id > last_seen_id`) is preferred. For a college project, skip/limit is perfectly fine.

---

*End of VIVA Q&A — Good luck with your presentation!*
