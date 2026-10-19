# Product Requirements Document (PRD)
## Inventory Stock Management System

**Version:** 1.0  
**Date:** 2026-10-19  
**Author:** College Assignment — Python + MongoDB  

---

## 1. Overview

### Problem Statement
Small retail shops and college stores manually track inventory in spreadsheets or paper registers. This leads to:
- Stockouts (running out of items without warning)
- Overstocking (money tied up in excess goods)
- No audit trail of who added/removed stock
- Difficulty finding which products are low or which supplier provides them

### Goal
Build a **menu-driven CLI application** in Python that lets a shop owner or store manager manage their inventory digitally using MongoDB as the backend database. The system must be simple enough to run locally without an internet connection, yet powerful enough to demonstrate key database concepts (CRUD, indexing, aggregation, atomic updates).

---

## 2. Objectives

1. Provide a clean, easy-to-use CLI for day-to-day inventory management.
2. Store all data persistently in a MongoDB database (`inventory_db`).
3. Demonstrate PyMongo concepts: CRUD, indexes, text search, aggregation pipelines, atomic updates.
4. Generate useful reports using MongoDB aggregation ($group, $lookup, $match, $sort, $limit).
5. Maintain an audit trail of all stock movements (Stock IN / OUT).
6. Be easy for a student to read, understand, and explain in a viva.

---

## 3. Target Users

| User | Role | Primary Need |
|------|------|--------------|
| Shop Owner | Admin | Full control — add/edit/delete products & suppliers, view reports |
| Store Manager | Operator | Record stock IN/OUT, check low-stock alerts, export data |

> For this college assignment both roles share the same CLI menu (no authentication required — kept intentionally simple).

---

## 4. Scope

### In-Scope
- Product management: add, view (paginated), search, update, delete
- Supplier management: add, list, update, delete
- Stock operations: Stock IN (purchase) and Stock OUT (sale) with atomic updates
- Transaction log: every stock movement is recorded
- Aggregation reports: 5 different reports using MongoDB pipelines
- CSV export of product data
- Seed script for demo data (10 suppliers, 40 products)
- Unit tests using pytest with a separate test database
- Documentation: PRD, Architecture, Schema, Viva Q&A

### Out-of-Scope
- User authentication / login
- Web or mobile UI (optional Streamlit bonus only)
- Multi-warehouse / branch management
- Barcode scanning
- Email/SMS notifications
- Cloud deployment

---

## 5. Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR-1** | The system shall allow adding a new product with: SKU (unique), name, category, price (> 0), quantity (>= 0), reorder level, supplier, and optional tags. |
| **FR-2** | The system shall display all products in a paginated table (10 per page) with columns: SKU, Name, Category, Price, Quantity, Reorder Level. |
| **FR-3** | The system shall support searching products by name (text/regex search) and filtering by category. |
| **FR-4** | The system shall allow updating any field of an existing product by SKU. |
| **FR-5** | The system shall allow deleting a product after the user confirms the action. |
| **FR-6** | The system shall allow adding a new supplier with: name, email (unique), phone, and address. |
| **FR-7** | The system shall list all suppliers in a formatted table. |
| **FR-8** | The system shall allow updating and deleting suppliers, but shall prevent deleting a supplier if any product still references them. |
| **FR-9** | The system shall record a **Stock IN** operation: increase product quantity atomically using `$inc` and log a transaction. |
| **FR-10** | The system shall record a **Stock OUT** operation: decrease product quantity **only if** enough stock exists (atomic check-and-update using a filter on `quantity >= requested`). |
| **FR-11** | Every stock operation shall create a record in the `transactions` collection with: product_id, type (IN/OUT), quantity, optional note, timestamp. |
| **FR-12** | The system shall display a **Low Stock Report** listing products where `quantity <= reorder_level`. |
| **FR-13** | The system shall display a **Category-wise Stock Value** report using `$group` aggregation. |
| **FR-14** | The system shall display a **Supplier-wise Product Count and Stock Value** report using `$lookup`. |
| **FR-15** | The system shall display a **Monthly Stock Movement Summary** from the transactions collection. |
| **FR-16** | The system shall display the **Top 5 Most Sold Products** (highest total Stock OUT quantity). |
| **FR-17** | The system shall export the full product list to a CSV file. |
| **FR-18** | The system shall provide a seed script to populate the database with realistic demo data. |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| **NFR-1** | Validation | All user inputs must be validated before hitting the database. |
| **NFR-2** | Error Handling | Duplicate SKU / email, invalid ObjectId, insufficient stock, and MongoDB connection failure must all show friendly error messages — no raw tracebacks. |
| **NFR-3** | Performance | Indexes must be created on startup. Queries on indexed fields should be fast even with thousands of documents. |
| **NFR-4** | Readability | Every file, class, and function must have a docstring. Inline comments must explain every PyMongo-specific concept. |
| **NFR-5** | Testability | Tests must use a separate `inventory_test_db` database and clean up after each test. |
| **NFR-6** | Config | No hardcoded connection strings; all config loaded from `.env` via `python-dotenv`. |
| **NFR-7** | Code Style | PEP 8 compliant; no function longer than ~40 lines; meaningful variable names. |

---

## 7. Data Model

### 7.1 Collection: `products`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | MongoDB document ID |
| `sku` | string | unique, required | Stock Keeping Unit (e.g., "ELEC-001") |
| `name` | string | required | Product display name |
| `category` | string | required | E.g., "Electronics", "Clothing" |
| `price` | float | > 0, required | Unit selling price |
| `quantity` | int | >= 0, required | Current stock count |
| `reorder_level` | int | >= 0, default 10 | Alert threshold |
| `supplier_id` | ObjectId | ref: suppliers | Supplying vendor |
| `tags` | array[string] | optional | Search/filter tags |
| `created_at` | datetime | auto | Document creation time |
| `updated_at` | datetime | auto-update | Last modification time |

**Indexes:**
- `{ "sku": 1 }` — unique
- `{ "category": 1 }` — for category filter queries
- Text index on `name` — for text search

### 7.2 Collection: `suppliers`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | MongoDB document ID |
| `name` | string | required | Supplier company name |
| `email` | string | unique, required | Contact email |
| `phone` | string | optional | Contact phone number |
| `address` | string | optional | Physical address |
| `created_at` | datetime | auto | Document creation time |

**Indexes:**
- `{ "email": 1 }` — unique

### 7.3 Collection: `transactions`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `_id` | ObjectId | auto | MongoDB document ID |
| `product_id` | ObjectId | ref: products, required | Which product moved |
| `type` | string | "IN" or "OUT", required | Direction of movement |
| `quantity` | int | > 0, required | Units moved |
| `note` | string | optional | Reason / PO number / customer |
| `timestamp` | datetime | auto | When the movement occurred |

**Indexes:**
- `{ "product_id": 1, "timestamp": -1 }` — compound index for efficient per-product history queries

### 7.4 Relationships

```
suppliers (1) -------- (many) products (1) -------- (many) transactions
```

Relationships are maintained via ObjectId references, NOT embedded documents, because:
- Products can be queried independently of suppliers.
- Transaction logs grow unboundedly and would bloat product documents if embedded.

---

## 8. User Flows

```
MAIN MENU
+-- 1. Product Management
|   +-- 1. Add Product
|   +-- 2. View All Products  (paginated)
|   +-- 3. Search Products    (by name / category)
|   +-- 4. Update Product
|   +-- 5. Delete Product
|
+-- 2. Supplier Management
|   +-- 1. Add Supplier
|   +-- 2. View All Suppliers
|   +-- 3. Update Supplier
|   +-- 4. Delete Supplier
|
+-- 3. Stock Operations
|   +-- 1. Stock IN  (purchase received)
|   +-- 2. Stock OUT (sale / dispatch)
|
+-- 4. Reports
|   +-- 1. Low Stock Report
|   +-- 2. Category-wise Stock Value
|   +-- 3. Supplier-wise Summary
|   +-- 4. Monthly Movement Summary
|   +-- 5. Top 5 Sold Products
|
+-- 5. Export Products to CSV
+-- 0. Exit
```

---

## 9. Tech Stack and Why

| Tool | Version | Reason |
|------|---------|--------|
| Python | 3.10+ | Modern syntax (type hints); widely taught in colleges |
| MongoDB | 6.x (local) | Document store; flexible schema; excellent aggregation framework |
| PyMongo | latest | Official synchronous Python driver; simple and well-documented |
| python-dotenv | latest | Best practice: keep secrets in `.env`, not source code |
| tabulate | latest | Format CLI output as clean tables |
| pytest | latest | Simple, popular test framework; fixtures make test isolation easy |
| faker | latest | Generate realistic seed data quickly |

**Why MongoDB over SQL?**
Products have variable attributes (tags, flexible categories). MongoDB's document model fits naturally. Aggregation pipelines are powerful and worth demonstrating for academic credit.

---

## 10. Project Structure

```
inventory-management/
+-- README.md
+-- requirements.txt
+-- .env.example
+-- .gitignore
+-- main.py                  # CLI entry point / main menu loop
+-- config.py                # Reads .env, exposes constants
+-- db/
|   +-- __init__.py
|   +-- connection.py        # MongoClient singleton + ping check
|   +-- indexes.py           # create_indexes() called on startup
+-- models/
|   +-- schemas.py           # Dataclasses + builder functions for each collection
+-- services/
|   +-- product_service.py   # Product CRUD + search
|   +-- supplier_service.py  # Supplier CRUD
|   +-- stock_service.py     # Stock IN/OUT + atomic updates
|   +-- report_service.py    # All aggregation pipelines
+-- cli/
|   +-- menus.py             # Sub-menus for each feature area
|   +-- helpers.py           # print_table(), get_input(), pagination
+-- utils/
|   +-- validators.py        # Input validation functions
|   +-- exporter.py          # CSV export
+-- scripts/
|   +-- seed_data.py         # Inserts demo data
+-- tests/
|   +-- conftest.py          # pytest fixtures (test DB setup/teardown)
|   +-- test_products.py
|   +-- test_stock.py
|   +-- test_reports.py
+-- docs/
    +-- PRD.md
    +-- ARCHITECTURE.md
    +-- SCHEMA.md
    +-- VIVA_QA.md
```

---

## 11. Testing Plan

| Test File | What It Tests |
|-----------|---------------|
| `test_products.py` | Add product (valid + duplicate SKU), search, update, delete |
| `test_stock.py` | Stock IN increases quantity, Stock OUT decreases quantity, Stock OUT fails when insufficient |
| `test_reports.py` | Low stock report returns correct items, category aggregation returns correct totals |

**Test Database:** `inventory_test_db`
**Teardown:** Each test function cleans the relevant collections using `collection.delete_many({})` in a pytest fixture.

---

## 12. Future Enhancements

1. **Streamlit Web UI** — replace CLI with a browser-based dashboard
2. **Authentication** — role-based access (admin vs. staff)
3. **Purchase Orders** — generate PDF purchase orders when stock is low
4. **Barcode Integration** — scan barcodes to look up products
5. **Cloud MongoDB** — switch from local to MongoDB Atlas with a config change
6. **REST API** — expose functionality via FastAPI endpoints
7. **Automated Reorder Alerts** — email supplier when stock drops below reorder level
