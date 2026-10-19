"""
scripts/seed_data.py
---------------------
Seed script to populate the inventory_db with realistic demo data.

Inserts:
  - 10 suppliers across different industries
  - 40 products spread across 8 categories

Usage:
    python scripts/seed_data.py

Run this ONCE before using the application for the first time.
It is safe to re-run — existing records with the same SKU/email
will be skipped (not duplicated) thanks to upsert logic.

Requires:
    pip install faker  (already in requirements.txt)
"""

import sys
import os

# Allow running this script directly from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from faker import Faker
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne

from db.connection import get_db, get_client
from db.indexes import create_indexes

fake = Faker("en_IN")   # Indian locale for realistic names/addresses


def seed_suppliers(db) -> list[dict]:
    """
    Insert 10 realistic suppliers using upsert on email (idempotent).

    Upsert = UPDATE if exists, INSERT if not.
    In PyMongo: update_one(..., upsert=True)

    Args:
        db: The pymongo Database object.

    Returns:
        list[dict]: The supplier documents after insertion (with their _ids).
    """
    suppliers_col = db["suppliers"]

    supplier_data = [
        {"name": "TechSupply India Pvt Ltd", "email": "contact@techsupply.in",
         "phone": "9876543210", "address": "12, Tech Park, Bengaluru, KA 560001"},
        {"name": "GlobalElec Distributors", "email": "sales@globalelec.com",
         "phone": "9123456780", "address": "45, Nehru Street, Chennai, TN 600001"},
        {"name": "FashionHub Wholesale", "email": "orders@fashionhub.in",
         "phone": "9988776655", "address": "78, Linking Road, Mumbai, MH 400050"},
        {"name": "HomeNest Suppliers", "email": "supply@homenest.in",
         "phone": "8877665544", "address": "22, MG Road, Pune, MH 411001"},
        {"name": "FreshFarm Organics", "email": "fresh@farmorganics.in",
         "phone": "9001122334", "address": "Farm Road, Amritsar, PB 143001"},
        {"name": "SportZone Trading Co", "email": "trade@sportzone.in",
         "phone": "9112233445", "address": "55, Sports Complex, Delhi, DL 110001"},
        {"name": "OfficeWorld Supplies", "email": "info@officeworld.in",
         "phone": "9223344556", "address": "Block B, Cyber City, Gurugram, HR 122001"},
        {"name": "BookBridge Publishers", "email": "wholesale@bookbridge.in",
         "phone": "9334455667", "address": "Publisher Lane, Kolkata, WB 700001"},
        {"name": "NutriPack Foods Ltd", "email": "nutripack@foods.in",
         "phone": "9445566778", "address": "Industrial Area, Ahmedabad, GJ 380001"},
        {"name": "CraftCircle Artisans", "email": "hello@craftcircle.in",
         "phone": "9556677889", "address": "Handicraft Zone, Jaipur, RJ 302001"},
    ]

    now = datetime.now(timezone.utc)
    supplier_ids = []

    for s in supplier_data:
        s["created_at"] = now
        # upsert=True: if a supplier with this email exists, update it;
        # otherwise insert a new document. This makes the script idempotent.
        suppliers_col.update_one(
            {"email": s["email"]},          # filter: match by unique email
            {"$setOnInsert": s},            # only set fields when INSERTING (not updating)
            upsert=True
        )

    # Retrieve all suppliers with their generated _ids
    suppliers = list(suppliers_col.find({"email": {"$in": [s["email"] for s in supplier_data]}}))
    print(f"  ✔ {len(suppliers)} suppliers ready.")
    return suppliers


def seed_products(db, suppliers: list[dict]) -> None:
    """
    Insert 40 realistic products spread across 8 categories.

    Uses bulk upsert: update_many with upsert on SKU (idempotent).

    Args:
        db:        pymongo Database object.
        suppliers: List of supplier documents (with _id fields).
    """
    products_col = db["products"]
    now = datetime.now(timezone.utc)

    # Map supplier names to their ObjectIds for easy reference
    sup = {s["name"]: s["_id"] for s in suppliers}

    products = [
        # ── Electronics (8 products) ──────────────────────────────────────
        {"sku": "ELEC-001", "name": "Wireless Bluetooth Headphones",
         "category": "Electronics", "price": 2499.00, "quantity": 45,
         "reorder_level": 10, "supplier_id": sup["TechSupply India Pvt Ltd"],
         "tags": ["audio", "wireless", "bluetooth"]},
        {"sku": "ELEC-002", "name": "USB-C Fast Charger 65W",
         "category": "Electronics", "price": 899.00, "quantity": 120,
         "reorder_level": 20, "supplier_id": sup["TechSupply India Pvt Ltd"],
         "tags": ["charging", "usb-c", "fast-charge"]},
        {"sku": "ELEC-003", "name": "Mechanical Gaming Keyboard",
         "category": "Electronics", "price": 3499.00, "quantity": 8,
         "reorder_level": 10, "supplier_id": sup["GlobalElec Distributors"],
         "tags": ["gaming", "keyboard", "mechanical"]},
        {"sku": "ELEC-004", "name": "27-inch 4K Monitor",
         "category": "Electronics", "price": 22999.00, "quantity": 15,
         "reorder_level": 5, "supplier_id": sup["GlobalElec Distributors"],
         "tags": ["monitor", "4k", "display"]},
        {"sku": "ELEC-005", "name": "Noise Cancelling Earbuds",
         "category": "Electronics", "price": 1999.00, "quantity": 3,
         "reorder_level": 15, "supplier_id": sup["TechSupply India Pvt Ltd"],
         "tags": ["earbuds", "noise-cancel", "wireless"]},
        {"sku": "ELEC-006", "name": "Smart LED Desk Lamp",
         "category": "Electronics", "price": 1299.00, "quantity": 30,
         "reorder_level": 8, "supplier_id": sup["GlobalElec Distributors"],
         "tags": ["lamp", "led", "smart"]},
        {"sku": "ELEC-007", "name": "Portable Power Bank 20000mAh",
         "category": "Electronics", "price": 1799.00, "quantity": 55,
         "reorder_level": 12, "supplier_id": sup["TechSupply India Pvt Ltd"],
         "tags": ["power-bank", "portable", "charging"]},
        {"sku": "ELEC-008", "name": "Webcam Full HD 1080p",
         "category": "Electronics", "price": 2199.00, "quantity": 18,
         "reorder_level": 5, "supplier_id": sup["GlobalElec Distributors"],
         "tags": ["webcam", "hd", "video-call"]},

        # ── Clothing (6 products) ─────────────────────────────────────────
        {"sku": "CLTH-001", "name": "Men's Cotton Casual Shirt",
         "category": "Clothing", "price": 599.00, "quantity": 80,
         "reorder_level": 20, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["shirt", "cotton", "men"]},
        {"sku": "CLTH-002", "name": "Women's Linen Kurti",
         "category": "Clothing", "price": 749.00, "quantity": 60,
         "reorder_level": 15, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["kurti", "linen", "women"]},
        {"sku": "CLTH-003", "name": "Unisex Hooded Sweatshirt",
         "category": "Clothing", "price": 1099.00, "quantity": 5,
         "reorder_level": 10, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["hoodie", "sweatshirt", "unisex"]},
        {"sku": "CLTH-004", "name": "Sports Track Pants",
         "category": "Clothing", "price": 799.00, "quantity": 40,
         "reorder_level": 10, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["track", "sports", "pants"]},
        {"sku": "CLTH-005", "name": "Premium Denim Jeans",
         "category": "Clothing", "price": 1499.00, "quantity": 25,
         "reorder_level": 8, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["jeans", "denim", "premium"]},
        {"sku": "CLTH-006", "name": "Kids' Summer Dress",
         "category": "Clothing", "price": 499.00, "quantity": 50,
         "reorder_level": 12, "supplier_id": sup["FashionHub Wholesale"],
         "tags": ["kids", "dress", "summer"]},

        # ── Home & Kitchen (5 products) ───────────────────────────────────
        {"sku": "HOME-001", "name": "Stainless Steel Pressure Cooker 5L",
         "category": "Home & Kitchen", "price": 1899.00, "quantity": 22,
         "reorder_level": 5, "supplier_id": sup["HomeNest Suppliers"],
         "tags": ["kitchen", "cooker", "stainless-steel"]},
        {"sku": "HOME-002", "name": "Non-Stick Frying Pan Set (3pcs)",
         "category": "Home & Kitchen", "price": 1499.00, "quantity": 0,
         "reorder_level": 5, "supplier_id": sup["HomeNest Suppliers"],
         "tags": ["pan", "non-stick", "cookware"]},
        {"sku": "HOME-003", "name": "Memory Foam Pillow Pair",
         "category": "Home & Kitchen", "price": 999.00, "quantity": 35,
         "reorder_level": 8, "supplier_id": sup["HomeNest Suppliers"],
         "tags": ["pillow", "memory-foam", "bedding"]},
        {"sku": "HOME-004", "name": "Bamboo Cutting Board Large",
         "category": "Home & Kitchen", "price": 349.00, "quantity": 70,
         "reorder_level": 15, "supplier_id": sup["HomeNest Suppliers"],
         "tags": ["cutting-board", "bamboo", "kitchen"]},
        {"sku": "HOME-005", "name": "Insulated Water Bottle 1L",
         "category": "Home & Kitchen", "price": 599.00, "quantity": 9,
         "reorder_level": 10, "supplier_id": sup["HomeNest Suppliers"],
         "tags": ["bottle", "insulated", "eco"]},

        # ── Food & Grocery (5 products) ───────────────────────────────────
        {"sku": "FOOD-001", "name": "Organic Cold-Pressed Coconut Oil 500ml",
         "category": "Food & Grocery", "price": 299.00, "quantity": 100,
         "reorder_level": 25, "supplier_id": sup["FreshFarm Organics"],
         "tags": ["organic", "coconut-oil", "cooking"]},
        {"sku": "FOOD-002", "name": "Whole Grain Quinoa 500g",
         "category": "Food & Grocery", "price": 249.00, "quantity": 4,
         "reorder_level": 20, "supplier_id": sup["FreshFarm Organics"],
         "tags": ["quinoa", "grain", "healthy"]},
        {"sku": "FOOD-003", "name": "Himalayan Pink Salt 1kg",
         "category": "Food & Grocery", "price": 179.00, "quantity": 85,
         "reorder_level": 30, "supplier_id": sup["NutriPack Foods Ltd"],
         "tags": ["salt", "himalayan", "mineral"]},
        {"sku": "FOOD-004", "name": "Mixed Nuts Premium Pack 250g",
         "category": "Food & Grocery", "price": 399.00, "quantity": 45,
         "reorder_level": 15, "supplier_id": sup["NutriPack Foods Ltd"],
         "tags": ["nuts", "snack", "healthy"]},
        {"sku": "FOOD-005", "name": "Herbal Green Tea (100 bags)",
         "category": "Food & Grocery", "price": 199.00, "quantity": 60,
         "reorder_level": 20, "supplier_id": sup["FreshFarm Organics"],
         "tags": ["tea", "herbal", "green-tea"]},

        # ── Sports & Fitness (5 products) ─────────────────────────────────
        {"sku": "SPRT-001", "name": "Yoga Mat Anti-Slip 6mm",
         "category": "Sports & Fitness", "price": 799.00, "quantity": 30,
         "reorder_level": 8, "supplier_id": sup["SportZone Trading Co"],
         "tags": ["yoga", "mat", "fitness"]},
        {"sku": "SPRT-002", "name": "Resistance Bands Set (5 bands)",
         "category": "Sports & Fitness", "price": 599.00, "quantity": 6,
         "reorder_level": 10, "supplier_id": sup["SportZone Trading Co"],
         "tags": ["resistance-band", "workout", "gym"]},
        {"sku": "SPRT-003", "name": "Adjustable Dumbbell Pair 10kg",
         "category": "Sports & Fitness", "price": 2999.00, "quantity": 12,
         "reorder_level": 5, "supplier_id": sup["SportZone Trading Co"],
         "tags": ["dumbbell", "weights", "gym"]},
        {"sku": "SPRT-004", "name": "Running Shoes Men Size 10",
         "category": "Sports & Fitness", "price": 3499.00, "quantity": 20,
         "reorder_level": 5, "supplier_id": sup["SportZone Trading Co"],
         "tags": ["shoes", "running", "sport"]},
        {"sku": "SPRT-005", "name": "Jump Rope Speed Cable",
         "category": "Sports & Fitness", "price": 299.00, "quantity": 50,
         "reorder_level": 10, "supplier_id": sup["SportZone Trading Co"],
         "tags": ["jump-rope", "cardio", "fitness"]},

        # ── Office Supplies (4 products) ──────────────────────────────────
        {"sku": "OFFC-001", "name": "A4 Printer Paper (500 sheets)",
         "category": "Office Supplies", "price": 299.00, "quantity": 200,
         "reorder_level": 50, "supplier_id": sup["OfficeWorld Supplies"],
         "tags": ["paper", "printer", "a4"]},
        {"sku": "OFFC-002", "name": "Blue Ball-Point Pens (Box of 50)",
         "category": "Office Supplies", "price": 199.00, "quantity": 3,
         "reorder_level": 10, "supplier_id": sup["OfficeWorld Supplies"],
         "tags": ["pen", "stationery", "blue"]},
        {"sku": "OFFC-003", "name": "Whiteboard Markers Set (12 colours)",
         "category": "Office Supplies", "price": 349.00, "quantity": 25,
         "reorder_level": 5, "supplier_id": sup["OfficeWorld Supplies"],
         "tags": ["marker", "whiteboard", "colour"]},
        {"sku": "OFFC-004", "name": "Ergonomic Lumbar Back Support Cushion",
         "category": "Office Supplies", "price": 999.00, "quantity": 18,
         "reorder_level": 5, "supplier_id": sup["OfficeWorld Supplies"],
         "tags": ["ergonomic", "cushion", "back-support"]},

        # ── Books (4 products) ────────────────────────────────────────────
        {"sku": "BOOK-001", "name": "Python Programming for Beginners",
         "category": "Books", "price": 449.00, "quantity": 35,
         "reorder_level": 10, "supplier_id": sup["BookBridge Publishers"],
         "tags": ["python", "programming", "beginners"]},
        {"sku": "BOOK-002", "name": "MongoDB: The Definitive Guide",
         "category": "Books", "price": 699.00, "quantity": 7,
         "reorder_level": 5, "supplier_id": sup["BookBridge Publishers"],
         "tags": ["mongodb", "database", "nosql"]},
        {"sku": "BOOK-003", "name": "Data Structures & Algorithms in Python",
         "category": "Books", "price": 549.00, "quantity": 40,
         "reorder_level": 10, "supplier_id": sup["BookBridge Publishers"],
         "tags": ["dsa", "algorithms", "python"]},
        {"sku": "BOOK-004", "name": "The Lean Startup (Paperback)",
         "category": "Books", "price": 399.00, "quantity": 20,
         "reorder_level": 5, "supplier_id": sup["BookBridge Publishers"],
         "tags": ["startup", "business", "entrepreneurship"]},

        # ── Crafts & Gifts (3 products) ───────────────────────────────────
        {"sku": "CRFT-001", "name": "Handmade Terracotta Vase Set",
         "category": "Crafts & Gifts", "price": 699.00, "quantity": 15,
         "reorder_level": 5, "supplier_id": sup["CraftCircle Artisans"],
         "tags": ["terracotta", "handmade", "decor"]},
        {"sku": "CRFT-002", "name": "Scented Soy Wax Candle (3-pack)",
         "category": "Crafts & Gifts", "price": 499.00, "quantity": 2,
         "reorder_level": 10, "supplier_id": sup["CraftCircle Artisans"],
         "tags": ["candle", "soy-wax", "scented"]},
        {"sku": "CRFT-003", "name": "Block-Print Fabric Gift Bag (5-pack)",
         "category": "Crafts & Gifts", "price": 249.00, "quantity": 60,
         "reorder_level": 15, "supplier_id": sup["CraftCircle Artisans"],
         "tags": ["gift-bag", "fabric", "block-print"]},
    ]

    # Add timestamps to each product
    for p in products:
        p["created_at"] = now
        p["updated_at"] = now

    # Bulk upsert: for each product, update if SKU exists, else insert.
    # Using UpdateOne operations in a bulk_write for efficiency.
    operations = [
        UpdateOne(
            {"sku": p["sku"]},           # filter by unique SKU
            {"$setOnInsert": p},          # only set on new insert, not update
            upsert=True
        )
        for p in products
    ]

    result = products_col.bulk_write(operations, ordered=False)
    inserted = result.upserted_count
    existing = len(products) - inserted
    print(f"  ✔ {inserted} products inserted, {existing} already existed (skipped).")


def main() -> None:
    """Run the seed script: connect, create indexes, insert demo data."""
    print("\n🌱  Seeding inventory_db with demo data...\n")

    try:
        get_client()
    except SystemExit:
        print("ERROR: MongoDB is not running. Start MongoDB and try again.")
        sys.exit(1)

    db = get_db()
    create_indexes()

    print("\n📦  Seeding Suppliers...")
    suppliers = seed_suppliers(db)

    print("\n📦  Seeding Products...")
    seed_products(db, suppliers)

    print(f"\n{'─' * 50}")
    print("✅  Seed complete! Run 'python main.py' to start the app.")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
