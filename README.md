# Inventory Stock Management System

A beginner-friendly, menu-driven CLI application for managing shop inventory built with **Python 3.10+**, **MongoDB**, and **PyMongo**. Created as a college assignment demonstrating MongoDB CRUD, indexing, atomic updates, and aggregation pipelines.

---

## Features

| Feature | Details |
|---------|---------|
| **Product Management** | Add, view (paginated), search (text + regex), filter by category, update, delete |
| **Supplier Management** | Add, list, update, delete — with referential integrity check on delete |
| **Stock IN / OUT** | Atomic updates with `$inc`; Stock OUT uses `$gte` guard to prevent negative stock |
| **Transaction Log** | Every stock movement is recorded with timestamp and optional note |
| **5 Aggregation Reports** | Low stock, category value, supplier summary, monthly movements, top 5 sellers |
| **CSV Export** | Export full product list to a timestamped CSV file |
| **Seed Data** | 10 suppliers + 40 realistic products inserted via idempotent bulk upsert |
| **Unit Tests** | 37 tests across products, stock, and reports using a separate test DB |

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Application language |
| MongoDB | 6.x (local) | Document database |
| PyMongo | 4.7.3 | Official MongoDB Python driver |
| python-dotenv | 1.0.1 | Load config from `.env` |
| tabulate | 0.9.0 | CLI table formatting |
| faker | 25.2.0 | Realistic seed data generation |
| pytest | 8.2.2 | Unit testing framework |

---

## Project Structure

```
inventory-management/
├── main.py                  # CLI entry point
├── config.py                # Environment variable loader
├── requirements.txt
├── .env.example
├── db/
│   ├── connection.py        # MongoClient singleton
│   └── indexes.py           # Index creation on startup
├── models/
│   └── schemas.py           # Dataclasses + document builders
├── services/
│   ├── product_service.py   # Product CRUD + search
│   ├── supplier_service.py  # Supplier CRUD
│   ├── stock_service.py     # Stock IN/OUT atomic updates
│   └── report_service.py    # 5 aggregation pipelines
├── cli/
│   ├── menus.py             # All sub-menu functions
│   └── helpers.py           # Input validation + table printing
├── utils/
│   ├── validators.py        # Pure validation functions
│   └── exporter.py          # CSV export
├── scripts/
│   └── seed_data.py         # Demo data seeder
├── tests/
│   ├── conftest.py          # pytest fixtures
│   ├── test_products.py
│   ├── test_stock.py
│   └── test_reports.py
└── docs/
    ├── PRD.md
    ├── ARCHITECTURE.md
    ├── SCHEMA.md
    └── VIVA_QA.md
```

---

## Setup Steps

### Prerequisites

1. **Python 3.10+** — check with `python3 --version`
2. **MongoDB 6.x running locally** — check with `mongod --version`
   - macOS (Homebrew): `brew services start mongodb-community`
   - Linux: `sudo systemctl start mongod`
   - Windows: Start MongoDB service from Services panel

### Installation

```bash
# 1. Clone the repository (or navigate to the project folder)
cd "inventory management"

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
# Edit .env if your MongoDB runs on a different URI
```

### Environment Variables (`.env`)

```ini
MONGO_URI=mongodb://localhost:27017
DB_NAME=inventory_db
TEST_DB_NAME=inventory_test_db
PAGE_SIZE=10
EXPORT_DIR=exports
```

---

## How to Run

```bash
# Make sure virtual environment is active
source venv/bin/activate

# Start the application
python main.py
```

You'll see the welcome banner and the main menu.

---

## How to Seed Demo Data

Run this ONCE before using the application to populate 10 suppliers and 40 products:

```bash
python scripts/seed_data.py
```

**Output:**
```
🌱  Seeding inventory_db with demo data...

📦  Seeding Suppliers...
  ✔ 10 suppliers ready.

📦  Seeding Products...
  ✔ 40 products inserted, 0 already existed (skipped).

──────────────────────────────────────────────────
✅  Seed complete! Run 'python main.py' to start the app.
──────────────────────────────────────────────────
```

The script is **idempotent** — safe to run multiple times. Existing records are skipped (not duplicated) thanks to `upsert` with `$setOnInsert`.

---

## How to Run Tests

```bash
# Make sure virtual environment is active and MongoDB is running
source venv/bin/activate

# Run all tests with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_stock.py -v

# Run a specific test
pytest tests/test_stock.py::TestStockOut::test_stock_out_insufficient_stock -v
```

Tests use a **separate database** (`inventory_test_db`) and clean up after themselves. Your production data is never touched.

---

## Example CLI Session

```
╔══════════════════════════════════════════════════════╗
║       INVENTORY STOCK MANAGEMENT SYSTEM             ║
║       Python + MongoDB | College Assignment          ║
╚══════════════════════════════════════════════════════╝

[DB] Connected to MongoDB at mongodb://localhost:27017
[DB] All indexes verified / created.

──────────────────────────────────────────────────────────────
  Main Menu
──────────────────────────────────────────────────────────────
  1. Product Management
  2. Supplier Management
  3. Stock Operations  (IN / OUT)
  4. Reports & Analytics
  5. Export Products to CSV
  0. Exit

  Select option: 4

──────────────────────────────────────────────────────────────
  Reports & Analytics
──────────────────────────────────────────────────────────────
  1. Low Stock Report
  2. Category-wise Stock Value
  3. Supplier-wise Summary
  4. Monthly Stock Movement
  5. Top 5 Most Sold Products
  0. Back to Main Menu

  Select option: 2

──────────────────────────────────────────────────────────────
  Category-wise Stock Value
──────────────────────────────────────────────────────────────
╭──────────────────┬──────────┬───────────┬──────────────╮
│ Category         │ Products │ Total Qty │ Stock Value  │
├──────────────────┼──────────┼───────────┼──────────────┤
│ Electronics      │       8  │      294  │ ₹ 4,34,612   │
│ Sports & Fitness │       5  │      118  │ ₹ 1,89,700   │
│ Home & Kitchen   │       5  │      136  │ ₹ 1,12,445   │
│ Books            │       4  │      102  │ ₹ 59,100     │
│ Clothing         │       6  │      260  │ ₹ 52,000     │
│ Food & Grocery   │       5  │      294  │ ₹ 47,200     │
│ Office Supplies  │       4  │      246  │ ₹ 43,000     │
│ Crafts & Gifts   │       3  │       77  │ ₹ 24,000     │
╰──────────────────┴──────────┴───────────┴──────────────╯
```

---

## Key MongoDB Concepts Demonstrated

| Concept | Where Used |
|---------|-----------|
| Unique Index | `sku` in products, `email` in suppliers |
| Text Index | `name` in products (enables `$text` search) |
| Compound Index | `(product_id, timestamp DESC)` in transactions |
| Atomic `$inc` | Stock IN and Stock OUT operations |
| `$gte` guard filter | Prevents negative stock in Stock OUT |
| `$group` aggregation | Category value, monthly movement reports |
| `$lookup` (JOIN) | Supplier summary, top sold products reports |
| `$match`, `$sort`, `$limit` | Top 5 sold products pipeline |
| Bulk upsert | Seed script (`$setOnInsert` with `upsert=True`) |
| `distinct()` | Category dropdown list |
| Pagination | `skip()` + `limit()` on product listing |
| `DuplicateKeyError` | Caught on duplicate SKU/email |

---

## License

MIT — Free to use for educational purposes.
