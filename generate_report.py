"""
generate_report.py
------------------
Generates a professional PDF project report for the
Inventory Stock Management System.

Usage:
    python generate_report.py
    # Output: docs/Project_Report_Inventory_Management.pdf
"""

from fpdf import FPDF
import os
from datetime import datetime


class ProjectReport(FPDF):
    """Custom PDF class with header/footer styling."""

    NAVY = (15, 23, 42)
    DARK_BG = (30, 41, 59)
    ACCENT = (99, 102, 241)
    TEXT = (51, 65, 85)
    TEXT_LIGHT = (100, 116, 139)
    WHITE = (255, 255, 255)
    LIGHT_BG = (241, 245, 249)
    SUCCESS = (16, 185, 129)
    WARNING = (245, 158, 11)
    BORDER_COLOR = (203, 213, 225)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.TEXT_LIGHT)
        self.cell(0, 8, "Inventory Stock Management System - Project Report", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.BORDER_COLOR)
        self.line(10, 16, 200, 16)
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-20)
        self.set_draw_color(*self.BORDER_COLOR)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.TEXT_LIGHT)
        self.cell(0, 8, "Python + MongoDB | College Assignment", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R")

    # -- Helper methods --

    def cover_page(self):
        self.add_page()
        self.set_fill_color(*self.NAVY)
        self.rect(0, 0, 210, 297, "F")

        self.set_fill_color(*self.ACCENT)
        self.rect(0, 110, 210, 4, "F")

        self.set_y(60)
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(*self.WHITE)
        self.cell(0, 16, "Inventory Stock", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 16, "Management System", align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(6)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "A Full-Stack Python + MongoDB Application", align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(30)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(203, 213, 225)

        info_lines = [
            ("Subject", "Database Management Systems"),
            ("Technology", "Python, Flask, MongoDB, PyMongo, HTML/CSS/JS"),
            ("Database", "MongoDB (NoSQL Document Store)"),
            ("Date", datetime.now().strftime("%B %d, %Y")),
        ]
        for label, value in info_lines:
            self.set_x(45)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*self.ACCENT)
            self.cell(40, 10, f"{label}:")
            self.set_font("Helvetica", "", 11)
            self.set_text_color(203, 213, 225)
            self.cell(0, 10, value, new_x="LMARGIN", new_y="NEXT")

        self.set_y(260)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, "College Assignment - Project Report", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_title(self, number, title):
        self.ln(6)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*self.NAVY)
        self.cell(0, 12, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.8)
        self.line(10, self.get_y() + 1, 80, self.get_y() + 1)
        self.set_line_width(0.2)
        self.ln(8)

    def sub_title(self, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.DARK_BG)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*self.TEXT)
        self.multi_cell(0, 6.5, text)
        self.ln(2)

    def bullet_list(self, items):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*self.TEXT)
        for item in items:
            x = self.get_x()
            self.set_x(x + 6)
            self.set_font("Helvetica", "B", 10.5)
            self.set_text_color(*self.ACCENT)
            self.cell(5, 6.5, ">")
            self.set_font("Helvetica", "", 10.5)
            self.set_text_color(*self.TEXT)
            self.multi_cell(0, 6.5, f"  {item}")
            self.ln(1)
        self.ln(2)

    def styled_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*self.NAVY)
        self.set_text_color(*self.WHITE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 9, h, border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        fill = False
        for row in rows:
            if self.get_y() > 260:
                self.add_page()
            self.set_fill_color(*self.LIGHT_BG if fill else self.WHITE)
            self.set_text_color(*self.TEXT)
            for i, cell_val in enumerate(row):
                self.cell(col_widths[i], 7, str(cell_val), border=1, fill=True, align="C" if i > 0 else "L")
            self.ln()
            fill = not fill
        self.ln(4)

    def code_block(self, code, title=None):
        if title:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*self.DARK_BG)
            self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

        self.set_fill_color(30, 30, 46)
        self.set_text_color(220, 220, 240)
        self.set_font("Courier", "", 8.5)

        lines = code.strip().split('\n')
        block_height = len(lines) * 5.5 + 8

        if self.get_y() + block_height > 270:
            self.add_page()

        y_start = self.get_y()
        self.rect(12, y_start, 186, block_height, "F")

        self.set_xy(16, y_start + 4)
        for line in lines:
            self.cell(0, 5.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(16)
        self.ln(6)

    def info_box(self, text, box_type="info"):
        colors = {
            "info": self.ACCENT,
            "success": self.SUCCESS,
            "warning": self.WARNING,
        }
        color = colors.get(box_type, self.ACCENT)
        self.set_fill_color(color[0], color[1], color[2])
        y = self.get_y()
        self.rect(10, y, 3, 20, "F")
        self.set_xy(16, y + 2)
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(*self.TEXT)
        self.multi_cell(178, 5.5, text)
        self.ln(4)


def build_report():
    pdf = ProjectReport()

    # ================================================================
    # COVER PAGE
    # ================================================================
    pdf.cover_page()

    # ================================================================
    # TABLE OF CONTENTS
    # ================================================================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.NAVY)
    pdf.cell(0, 14, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    toc_items = [
        ("1", "Introduction & Problem Statement"),
        ("2", "Real-World Applications"),
        ("3", "Objectives & Scope"),
        ("4", "Technology Stack"),
        ("5", "System Architecture"),
        ("6", "Database Design (MongoDB)"),
        ("7", "Indexing Strategy"),
        ("8", "Core Features & Implementation"),
        ("9", "Aggregation Pipelines (Reports)"),
        ("10", "Atomic Operations (Stock Management)"),
        ("11", "REST API Design"),
        ("12", "Frontend Design"),
        ("13", "Project File Structure"),
        ("14", "How to Run the Project"),
        ("15", "Future Enhancements"),
        ("16", "Conclusion"),
        ("17", "References"),
    ]
    for num, title in toc_items:
        pdf.set_font("Helvetica", "B" if len(num) <= 2 else "", 11)
        pdf.set_text_color(*pdf.NAVY)
        pdf.cell(12, 8, num + ".")
        pdf.set_text_color(*pdf.TEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    # 1. INTRODUCTION
    # ================================================================
    pdf.add_page()
    pdf.section_title("1", "Introduction & Problem Statement")

    pdf.body_text(
        "Inventory management is a critical aspect of any retail business, warehouse, or institutional store. "
        "It involves tracking the quantity, location, and status of goods across the supply chain. "
        "In many small retail shops, college stores, and local businesses, inventory is still managed "
        "using paper registers or spreadsheets, leading to several operational challenges."
    )

    pdf.sub_title("Problems with Manual Inventory Management")
    pdf.bullet_list([
        "Stockouts: Running out of items without any warning system, leading to lost sales and customer dissatisfaction.",
        "Overstocking: Excessive inventory ties up working capital and increases storage costs.",
        "No Audit Trail: It is impossible to trace who added or removed stock, making accountability difficult.",
        "Human Errors: Manual data entry is prone to mistakes in quantity, pricing, and categorization.",
        "Slow Reporting: Generating reports like 'which items are low?' or 'what is the total inventory value?' requires hours.",
        "No Real-time Visibility: Managers cannot see current stock levels without physically counting items.",
    ])

    pdf.sub_title("Our Solution")
    pdf.body_text(
        "This project - the Inventory Stock Management System - addresses all of the above problems by providing "
        "a digital inventory management solution built with Python and MongoDB. It offers both a Command-Line Interface (CLI) "
        "for quick terminal-based operations and a modern Web Dashboard for visual, browser-based management. "
        "The system supports full CRUD operations on products and suppliers, atomic stock movements, "
        "real-time low-stock alerts, and powerful aggregation-based analytics reports."
    )

    # ================================================================
    # 2. REAL-WORLD APPLICATIONS
    # ================================================================
    pdf.add_page()
    pdf.section_title("2", "Real-World Applications")

    pdf.body_text(
        "This system is not just an academic exercise - it models real-world inventory management "
        "patterns used by businesses of all sizes. Below are practical scenarios where this system "
        "can be directly deployed or adapted:"
    )

    use_cases = [
        ("Retail Shops & Kirana Stores",
         "A local shop owner can track all products, set reorder levels for automatic low-stock alerts, "
         "record daily sales (stock OUT), and purchases from suppliers (stock IN). The CSV export feature "
         "helps with tax filing and bookkeeping."),
        ("College & University Stores",
         "Campus bookstores, lab supply rooms, and hostel canteens can manage stationery, chemicals, "
         "or food items. Multiple staff members can use the web interface simultaneously."),
        ("Warehouse Management",
         "Warehouses receiving goods from multiple suppliers can track each supplier's products, "
         "monitor total inventory value, and generate monthly movement reports for logistics planning."),
        ("Pharmacy & Medical Stores",
         "Medicines with critical stock levels can be monitored using the reorder_level feature. "
         "The audit trail (transactions collection) ensures regulatory compliance."),
        ("E-commerce Order Fulfillment",
         "The atomic stock-out operation prevents overselling - if two orders arrive simultaneously "
         "for the last item, MongoDB's atomic guard ensures only one succeeds, preventing negative stock."),
        ("Restaurant & Cafe Inventory",
         "Track ingredients, beverages, and supplies. Monthly movement reports show consumption patterns "
         "to optimize purchasing decisions."),
    ]

    for title, desc in use_cases:
        pdf.sub_title(title)
        pdf.body_text(desc)

    # ================================================================
    # 3. OBJECTIVES
    # ================================================================
    pdf.add_page()
    pdf.section_title("3", "Objectives & Scope")

    pdf.sub_title("Primary Objectives")
    pdf.bullet_list([
        "Demonstrate proficiency in MongoDB - CRUD operations, indexing, text search, and aggregation pipelines.",
        "Build a functional inventory system with Product Management, Supplier Management, Stock Operations, and Reporting.",
        "Implement atomic database operations to prevent race conditions in concurrent stock updates.",
        "Provide both a CLI and a Web-based interface for maximum flexibility.",
        "Generate 5 analytical reports using MongoDB's Aggregation Framework.",
        "Export data to CSV format for external use and backup.",
    ])

    pdf.sub_title("Scope")
    pdf.styled_table(
        ["Feature", "In Scope", "Out of Scope"],
        [
            ["Product CRUD", "Yes", ""],
            ["Supplier CRUD", "Yes", ""],
            ["Stock IN/OUT (Atomic)", "Yes", ""],
            ["5 Aggregation Reports", "Yes", ""],
            ["Text Search + Filters", "Yes", ""],
            ["CSV Export", "Yes", ""],
            ["Web Dashboard", "Yes", ""],
            ["User Authentication", "", "Future Enhancement"],
            ["Barcode/QR Scanning", "", "Future Enhancement"],
            ["Cloud Deployment", "", "Future Enhancement"],
        ],
        col_widths=[70, 50, 70],
    )

    # ================================================================
    # 4. TECHNOLOGY STACK
    # ================================================================
    pdf.add_page()
    pdf.section_title("4", "Technology Stack")

    pdf.styled_table(
        ["Layer", "Technology", "Purpose"],
        [
            ["Language", "Python 3.x", "Core application logic"],
            ["Database", "MongoDB 7.x", "NoSQL document store for all data"],
            ["DB Driver", "PyMongo 4.7", "Python driver for MongoDB operations"],
            ["Web Framework", "Flask 3.x", "Lightweight REST API server"],
            ["CORS", "Flask-CORS", "Cross-Origin Resource Sharing for API"],
            ["Frontend", "HTML5+CSS3+JS", "Modern single-page web dashboard"],
            ["Config", "python-dotenv", "Environment variable management"],
            ["Display", "tabulate", "CLI table formatting"],
            ["Seed Data", "Faker", "Realistic test data generation"],
            ["Testing", "Pytest", "Unit and integration testing"],
        ],
        col_widths=[35, 50, 105],
    )

    pdf.sub_title("Why MongoDB (NoSQL) over SQL?")
    pdf.styled_table(
        ["Aspect", "MongoDB (NoSQL)", "MySQL/PostgreSQL (SQL)"],
        [
            ["Data Model", "Flexible JSON documents", "Rigid table schemas"],
            ["Schema Changes", "No migrations needed", "ALTER TABLE required"],
            ["Nested Data", "Tags array, embedded docs", "Separate join tables"],
            ["Aggregation", "Pipeline stages (flexible)", "GROUP BY (rigid)"],
            ["Scaling", "Horizontal (sharding)", "Vertical (bigger server)"],
            ["Setup", "No schema definition", "CREATE TABLE + types"],
            ["Best For", "Evolving applications", "Fixed-schema, ACID-heavy"],
        ],
        col_widths=[35, 77, 78],
    )

    # ================================================================
    # 5. SYSTEM ARCHITECTURE
    # ================================================================
    pdf.add_page()
    pdf.section_title("5", "System Architecture")

    pdf.sub_title("Three-Tier Architecture")
    pdf.body_text(
        "The application follows a clean three-tier architecture pattern, separating concerns across "
        "distinct layers. Each layer communicates only with its adjacent layer, promoting modularity "
        "and testability."
    )

    pdf.styled_table(
        ["Tier", "Components", "Responsibility"],
        [
            ["Presentation", "frontend/ + cli/", "User interface (web + CLI)"],
            ["Application", "server.py + services/", "Business logic, API routing"],
            ["Data", "db/ + MongoDB", "Database connection, indexes, storage"],
        ],
        col_widths=[35, 55, 100],
    )

    pdf.sub_title("Request Flow (Adding a Product)")
    pdf.bullet_list([
        "1. Browser sends HTTP POST /api/products with JSON body.",
        "2. Flask (server.py) receives the request and parses JSON data.",
        "3. Flask calls the service function: add_product().",
        "4. Service uses PyMongo to execute insert_one() on MongoDB.",
        "5. MongoDB stores the document and returns the ObjectId.",
        "6. Service returns a success/failure dict to Flask.",
        "7. Flask serializes the response to JSON and returns to browser.",
        "8. Browser JS shows a success toast and refreshes the table.",
    ])

    pdf.sub_title("Singleton Connection Pattern")
    pdf.body_text(
        "The database connection uses the Singleton pattern (db/connection.py). PyMongo's MongoClient "
        "maintains an internal connection pool, so creating one per process is the recommended approach. "
        "The module-level variable _client is initialized on the first call to get_client() and reused "
        "for all subsequent calls."
    )

    pdf.code_block(
        '# Singleton pattern - one MongoClient per process\n'
        '_client = None\n\n'
        'def get_client():\n'
        '    global _client\n'
        '    if _client is None:\n'
        '        _client = MongoClient(MONGO_URI, timeout=3000)\n'
        '        _client.admin.command("ping")  # verify connection\n'
        '    return _client',
        "db/connection.py - Singleton MongoClient"
    )

    # ================================================================
    # 6. DATABASE DESIGN
    # ================================================================
    pdf.add_page()
    pdf.section_title("6", "Database Design (MongoDB)")

    pdf.body_text(
        "The database 'inventory_db' contains three collections. Unlike SQL databases, MongoDB does not "
        "require predefined schemas - documents can have varying fields. However, our application enforces "
        "consistent structure through builder functions in models/schemas.py."
    )

    pdf.sub_title("Collection 1: products")
    pdf.styled_table(
        ["Field", "Type", "Required", "Description"],
        [
            ["_id", "ObjectId", "Auto", "Unique document ID (auto-generated)"],
            ["sku", "String", "Yes", "Stock Keeping Unit - unique code"],
            ["name", "String", "Yes", "Product display name"],
            ["category", "String", "Yes", "Product category"],
            ["price", "Float", "Yes", "Unit price in INR"],
            ["quantity", "Integer", "Yes", "Current stock count"],
            ["reorder_level", "Integer", "No", "Low-stock alert threshold (def: 10)"],
            ["supplier_id", "ObjectId", "No", "Reference to supplier document"],
            ["tags", "Array", "No", "Searchable tags list"],
            ["created_at", "DateTime", "Auto", "Creation timestamp (UTC)"],
            ["updated_at", "DateTime", "Auto", "Last modification timestamp"],
        ],
        col_widths=[30, 22, 18, 120],
    )

    pdf.sub_title("Collection 2: suppliers")
    pdf.styled_table(
        ["Field", "Type", "Required", "Description"],
        [
            ["_id", "ObjectId", "Auto", "Unique document ID"],
            ["name", "String", "Yes", "Supplier company name"],
            ["email", "String", "Yes", "Contact email (unique)"],
            ["phone", "String", "No", "Contact phone number"],
            ["address", "String", "No", "Physical address"],
            ["created_at", "DateTime", "Auto", "Registration timestamp"],
        ],
        col_widths=[30, 22, 18, 120],
    )

    pdf.sub_title("Collection 3: transactions")
    pdf.body_text(
        "Every stock movement (IN or OUT) is recorded as a transaction document. This collection serves "
        "as an audit trail and is the data source for movement reports."
    )
    pdf.styled_table(
        ["Field", "Type", "Required", "Description"],
        [
            ["_id", "ObjectId", "Auto", "Unique document ID"],
            ["product_id", "ObjectId", "Yes", "Reference to product that moved"],
            ["type", "String", "Yes", "Movement type: 'IN' or 'OUT'"],
            ["quantity", "Integer", "Yes", "Number of units moved"],
            ["note", "String", "No", "Optional note (PO number, etc.)"],
            ["timestamp", "DateTime", "Auto", "When the movement occurred"],
        ],
        col_widths=[30, 22, 18, 120],
    )

    pdf.sub_title("Entity Relationships")
    pdf.bullet_list([
        "products.supplier_id references suppliers._id (manual join via $lookup).",
        "transactions.product_id references products._id (for stock history).",
        "Supplier deletion is blocked if products still reference that supplier.",
    ])

    # ================================================================
    # 7. INDEXING
    # ================================================================
    pdf.add_page()
    pdf.section_title("7", "Indexing Strategy")

    pdf.body_text(
        "Indexes in MongoDB work like indexes in a book - they allow the database engine to locate "
        "documents without scanning every document in the collection (called a collection scan). "
        "Without indexes, MongoDB must perform a full scan for every query, which becomes slow "
        "as data grows."
    )

    pdf.styled_table(
        ["Collection", "Field(s)", "Index Type", "Purpose"],
        [
            ["products", "sku", "Unique", "Prevents duplicate SKUs"],
            ["products", "category", "Regular", "Fast category filtering"],
            ["products", "name", "Text", "Full-text search"],
            ["suppliers", "email", "Unique", "Prevents duplicate emails"],
            ["transactions", "(product_id, timestamp)", "Compound", "Fast history queries"],
        ],
        col_widths=[32, 48, 28, 82],
    )

    pdf.code_block(
        '# Indexes are created at startup (idempotent)\n'
        'products.create_index("sku", unique=True)\n'
        'products.create_index("category")\n'
        'products.create_index([("name", "text")])\n'
        'suppliers.create_index("email", unique=True)\n'
        'transactions.create_index(\n'
        '    [("product_id", ASCENDING), ("timestamp", DESCENDING)]\n'
        ')',
        "db/indexes.py - Index Definitions"
    )

    pdf.info_box(
        "Unique indexes also serve as constraints - attempting to insert a document with a "
        "duplicate SKU or email raises a DuplicateKeyError, which we catch and return a friendly "
        "error message to the user.",
        "info"
    )

    # ================================================================
    # 8. CORE FEATURES
    # ================================================================
    pdf.add_page()
    pdf.section_title("8", "Core Features & Implementation")

    pdf.sub_title("8.1 Product Management (CRUD)")
    pdf.body_text("The product service (services/product_service.py) implements all four CRUD operations:")

    pdf.styled_table(
        ["Operation", "PyMongo Method", "SQL Equivalent"],
        [
            ["Create", "insert_one(doc)", "INSERT INTO products VALUES(...)"],
            ["Read All", "find({}).sort().skip().limit()", "SELECT * ... ORDER BY ... LIMIT"],
            ["Read One", "find_one({'sku': sku})", "SELECT * WHERE sku='X' LIMIT 1"],
            ["Update", "update_one(filter, {'$set': ...})", "UPDATE products SET ... WHERE"],
            ["Delete", "delete_one({'sku': sku})", "DELETE FROM products WHERE"],
            ["Count", "count_documents({})", "SELECT COUNT(*)"],
            ["Distinct", "distinct('category')", "SELECT DISTINCT category"],
        ],
        col_widths=[25, 65, 100],
    )

    pdf.sub_title("8.2 Text Search")
    pdf.body_text(
        "MongoDB's $text operator uses the text index on the 'name' field for full-text search. "
        "It supports stemming (e.g., 'laptop' matches 'laptops') and relevance scoring. "
        "If text search returns no results, a regex fallback performs partial matching."
    )

    pdf.code_block(
        '# Primary: Full-text search (fast, uses text index)\n'
        'col.find(\n'
        '    {"$text": {"$search": "wireless keyboard"}},\n'
        '    {"score": {"$meta": "textScore"}}\n'
        ').sort([("score", {"$meta": "textScore"})])\n\n'
        '# Fallback: Regex search (slower, partial matches)\n'
        'col.find({"name": {"$regex": "key", "$options": "i"}})',
        "product_service.py - Search Implementation"
    )

    pdf.sub_title("8.3 Supplier Management")
    pdf.body_text(
        "Suppliers support full CRUD operations. A critical feature is referential integrity enforcement: "
        "a supplier cannot be deleted if any products reference their supplier_id. This check is performed "
        "manually in the service layer since MongoDB does not enforce foreign keys."
    )

    pdf.code_block(
        '# Before deleting a supplier, check for linked products\n'
        'linked = products_col.count_documents({"supplier_id": oid})\n'
        'if linked > 0:\n'
        '    return {"error": f"{linked} products still linked"}',
        "supplier_service.py - Referential Integrity Check"
    )

    pdf.sub_title("8.4 Pagination")
    pdf.body_text(
        "Product listing uses server-side pagination with MongoDB's skip() and limit() methods."
    )

    pdf.code_block(
        'skip_count = (page - 1) * PAGE_SIZE\n'
        'products = list(\n'
        '    col.find({}).sort("sku", 1).skip(skip_count).limit(PAGE_SIZE)\n'
        ')\n'
        'total = col.count_documents({})\n'
        'total_pages = -(-total // PAGE_SIZE)  # ceiling division',
        "product_service.py - Pagination with skip/limit"
    )

    # ================================================================
    # 9. AGGREGATION PIPELINES
    # ================================================================
    pdf.add_page()
    pdf.section_title("9", "Aggregation Pipelines (Reports)")

    pdf.body_text(
        "MongoDB's Aggregation Framework is one of its most powerful features. A pipeline is an ordered "
        "array of stages - each stage transforms its input documents and passes the result to the next, "
        "similar to Unix pipes. The system implements 5 report pipelines:"
    )

    pdf.sub_title("Pipeline Stages Used")
    pdf.styled_table(
        ["Stage", "SQL Equivalent", "Description"],
        [
            ["$match", "WHERE", "Filters documents"],
            ["$group", "GROUP BY", "Groups and aggregates (SUM, COUNT)"],
            ["$sort", "ORDER BY", "Sorts results"],
            ["$limit", "LIMIT", "Restricts result count"],
            ["$lookup", "LEFT JOIN", "Joins with another collection"],
            ["$unwind", "Flatten", "Deconstructs array into docs"],
            ["$project", "SELECT / AS", "Reshapes output documents"],
            ["$expr", "Compare cols", "Compares two fields in same doc"],
        ],
        col_widths=[25, 30, 135],
    )

    reports = [
        ("Report 1: Low Stock Alert",
         "Finds products where quantity <= reorder_level using $expr to compare two fields.",
         'col.find(\n'
         '    {"$expr": {"$lte": ["$quantity", "$reorder_level"]}}\n'
         ').sort("quantity", 1)'),

        ("Report 2: Category Stock Value",
         "Groups by category, counts products, sums quantities, calculates total value (price x qty).",
         '{"$group": {\n'
         '    "_id": "$category",\n'
         '    "total_products": {"$sum": 1},\n'
         '    "total_value": {"$sum": {"$multiply": ["$price", "$quantity"]}}\n'
         '}}\n'
         '{"$sort": {"total_value": -1}}'),

        ("Report 3: Supplier Summary",
         "Groups products by supplier_id, then uses $lookup to JOIN with suppliers collection.",
         '{"$group": {"_id": "$supplier_id", ...}}\n'
         '{"$lookup": {\n'
         '    "from": "suppliers",\n'
         '    "localField": "_id",\n'
         '    "foreignField": "_id",\n'
         '    "as": "supplier_info"\n'
         '}}\n'
         '{"$unwind": "$supplier_info"}'),

        ("Report 4: Monthly Movement",
         "Groups transactions by year, month, and type using date extraction operators.",
         '{"$group": {\n'
         '    "_id": {\n'
         '        "year": {"$year": "$timestamp"},\n'
         '        "month": {"$month": "$timestamp"},\n'
         '        "type": "$type"\n'
         '    },\n'
         '    "total_quantity": {"$sum": "$quantity"}\n'
         '}}'),

        ("Report 5: Top 5 Sold Products",
         "A 7-stage pipeline: $match -> $group -> $sort -> $limit -> $lookup -> $unwind -> $project.",
         '{"$match": {"type": "OUT"}}\n'
         '{"$group": {"_id": "$product_id",\n'
         '            "total_sold": {"$sum": "$quantity"}}}\n'
         '{"$sort": {"total_sold": -1}}\n'
         '{"$limit": 5}\n'
         '{"$lookup": {"from": "products", ...}}'),
    ]

    for title, desc, code in reports:
        pdf.sub_title(title)
        pdf.body_text(desc)
        pdf.code_block(code)

    # ================================================================
    # 10. ATOMIC OPERATIONS
    # ================================================================
    pdf.add_page()
    pdf.section_title("10", "Atomic Operations (Stock Management)")

    pdf.body_text(
        "Stock management is the most technically challenging part of the system. The key problem is "
        "ensuring data consistency when multiple users update stock simultaneously."
    )

    pdf.sub_title("The Race Condition Problem")
    pdf.body_text(
        "Consider the naive approach to Stock OUT: "
        "1) Read the product (quantity = 5). "
        "2) Check if quantity >= requested (5 >= 3? Yes). "
        "3) Update: set quantity = 5 - 3 = 2. "
        "If two users execute this simultaneously, both read quantity = 5 at step 1, both pass the check, "
        "and both subtract 3 - resulting in quantity = -1, which is impossible!"
    )

    pdf.sub_title("The Atomic Guard Solution")
    pdf.body_text(
        "MongoDB solves this by combining the check and update into a SINGLE atomic operation. "
        "The guard condition is embedded inside the query filter:"
    )

    pdf.code_block(
        '# ATOMIC stock-out: check + update in ONE operation\n'
        'result = col.update_one(\n'
        '    {\n'
        '        "_id": product_id,\n'
        '        "quantity": {"$gte": requested_qty}   # GUARD\n'
        '    },\n'
        '    {\n'
        '        "$inc": {"quantity": -requested_qty},  # decrement\n'
        '        "$set": {"updated_at": now}\n'
        '    }\n'
        ')\n\n'
        '# If matched_count == 0, guard failed (insufficient stock)\n'
        'if result.matched_count == 0:\n'
        '    return {"error": "Insufficient stock"}',
        "stock_service.py - Atomic Guard Pattern"
    )

    pdf.info_box(
        "Why this works: MongoDB guarantees that update_one() is atomic at the document level. "
        "No other operation can modify the document between the filter evaluation and the update. "
        "If quantity was already reduced by another concurrent request, the filter won't match, "
        "and matched_count will be 0 - preventing negative stock.",
        "success"
    )

    pdf.sub_title("Stock IN - Using $inc Operator")
    pdf.code_block(
        '# $inc atomically adds to the current value\n'
        'col.update_one(\n'
        '    {"_id": product_id},\n'
        '    {\n'
        '        "$inc": {"quantity": 20},      # quantity += 20\n'
        '        "$set": {"updated_at": now}    # update timestamp\n'
        '    }\n'
        ')',
        "stock_service.py - Atomic Stock IN"
    )

    # ================================================================
    # 11. REST API
    # ================================================================
    pdf.add_page()
    pdf.section_title("11", "REST API Design")

    pdf.body_text(
        "The Flask server (server.py) exposes a RESTful API following standard HTTP conventions. "
        "All endpoints accept/return JSON. The API layer only handles HTTP routing - all business "
        "logic is delegated to the service layer."
    )

    pdf.sub_title("Product Endpoints")
    pdf.styled_table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/api/products?page=1", "List products (paginated)"],
            ["POST", "/api/products", "Add a new product"],
            ["GET", "/api/products/<sku>", "Get product by SKU"],
            ["PUT", "/api/products/<sku>", "Update product fields"],
            ["DELETE", "/api/products/<sku>", "Delete a product"],
            ["GET", "/api/categories", "Get distinct categories"],
        ],
        col_widths=[20, 65, 105],
    )

    pdf.sub_title("Supplier Endpoints")
    pdf.styled_table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/api/suppliers", "List all suppliers"],
            ["POST", "/api/suppliers", "Add a new supplier"],
            ["GET", "/api/suppliers/<id>", "Get supplier by ID"],
            ["PUT", "/api/suppliers/<id>", "Update supplier fields"],
            ["DELETE", "/api/suppliers/<id>", "Delete a supplier"],
        ],
        col_widths=[20, 65, 105],
    )

    pdf.sub_title("Stock & Report Endpoints")
    pdf.styled_table(
        ["Method", "Endpoint", "Description"],
        [
            ["POST", "/api/stock/in", "Record Stock IN operation"],
            ["POST", "/api/stock/out", "Record Stock OUT operation"],
            ["GET", "/api/stock/history/<sku>", "Transaction history"],
            ["GET", "/api/dashboard", "Summary stats"],
            ["GET", "/api/reports/low-stock", "Low stock report"],
            ["GET", "/api/reports/category-value", "Category value report"],
            ["GET", "/api/reports/supplier-summary", "Supplier summary"],
            ["GET", "/api/reports/monthly-movement", "Monthly movements"],
            ["GET", "/api/reports/top-sold", "Top 5 sold products"],
            ["POST", "/api/export/csv", "Export products to CSV"],
        ],
        col_widths=[20, 65, 105],
    )

    # ================================================================
    # 12. FRONTEND
    # ================================================================
    pdf.add_page()
    pdf.section_title("12", "Frontend Design")

    pdf.body_text(
        "The web frontend is a Single-Page Application (SPA) built with vanilla HTML, CSS, and JavaScript "
        "- no frameworks like React or Angular are used. It communicates with the Flask API via fetch() requests."
    )

    pdf.sub_title("Design Features")
    pdf.bullet_list([
        "Dark theme with glassmorphism effects for a premium look.",
        "Sidebar navigation with smooth page transitions.",
        "Real-time search with debouncing (400ms delay).",
        "Modal dialogs for add/edit/delete operations.",
        "Toast notifications for success/error feedback.",
        "Responsive layout - works on desktop and tablet.",
        "Color-coded stock badges (In Stock, Low Stock, Out of Stock).",
        "Paginated product tables with category filtering.",
    ])

    pdf.sub_title("Frontend Pages")
    pdf.styled_table(
        ["Page", "Features"],
        [
            ["Dashboard", "6 stat cards, low stock alerts, top sellers"],
            ["Products", "CRUD table, search, filter, pagination"],
            ["Suppliers", "CRUD table with integrity protection"],
            ["Stock Ops", "Side-by-side IN/OUT forms, history"],
            ["Reports", "5 analytics reports in card layout"],
        ],
        col_widths=[35, 155],
    )

    # ================================================================
    # 13. FILE STRUCTURE
    # ================================================================
    pdf.add_page()
    pdf.section_title("13", "Project File Structure")

    pdf.code_block(
        'inventory-management/\n'
        '|\n'
        '|-- server.py               # Flask REST API server\n'
        '|-- main.py                 # CLI entry point\n'
        '|-- config.py               # Loads .env configuration\n'
        '|-- .env                    # Environment variables\n'
        '|-- requirements.txt        # Python dependencies\n'
        '|\n'
        '|-- frontend/               # Web UI (SPA)\n'
        '|   |-- index.html          # HTML structure\n'
        '|   |-- style.css           # Dark theme stylesheet\n'
        '|   |-- app.js              # Client-side JavaScript\n'
        '|\n'
        '|-- db/                     # Database layer\n'
        '|   |-- connection.py       # Singleton MongoClient\n'
        '|   |-- indexes.py          # Index definitions\n'
        '|\n'
        '|-- models/\n'
        '|   |-- schemas.py          # Dataclass schemas + builders\n'
        '|\n'
        '|-- services/               # Business logic layer\n'
        '|   |-- product_service.py  # Product CRUD + search\n'
        '|   |-- supplier_service.py # Supplier CRUD\n'
        '|   |-- stock_service.py    # Atomic stock operations\n'
        '|   |-- report_service.py   # 5 aggregation reports\n'
        '|\n'
        '|-- utils/\n'
        '|   |-- exporter.py         # CSV export utility\n'
        '|   |-- validators.py       # Input validation\n'
        '|\n'
        '|-- cli/                    # CLI interface layer\n'
        '|-- tests/                  # Pytest test suite\n'
        '|-- scripts/                # Seed data script\n'
        '|-- docs/                   # Documentation'
    )

    # ================================================================
    # 14. HOW TO RUN
    # ================================================================
    pdf.section_title("14", "How to Run the Project")

    pdf.sub_title("Prerequisites")
    pdf.bullet_list([
        "Python 3.10+ installed",
        "MongoDB 6.0+ installed and running",
        "pip (Python package manager)",
    ])

    pdf.sub_title("Installation Steps")
    pdf.code_block(
        '# 1. Clone the repository\n'
        'git clone <repository-url>\n'
        'cd inventory-management\n\n'
        '# 2. Create and activate virtual environment\n'
        'python -m venv venv\n'
        'source venv/bin/activate      # macOS/Linux\n\n'
        '# 3. Install dependencies\n'
        'pip install -r requirements.txt\n'
        'pip install flask flask-cors\n\n'
        '# 4. Configure environment\n'
        'cp .env.example .env\n\n'
        '# 5. Start MongoDB\n'
        'brew services start mongodb-community   # macOS\n\n'
        '# 6. Run the web application\n'
        'python server.py\n'
        '# Open http://localhost:5000\n\n'
        '# OR run the CLI version\n'
        'python main.py',
        "Setup & Run Commands"
    )

    # ================================================================
    # 15. FUTURE ENHANCEMENTS
    # ================================================================
    pdf.add_page()
    pdf.section_title("15", "Future Enhancements")

    pdf.bullet_list([
        "User Authentication: JWT-based login with role-based access (admin, staff).",
        "Barcode/QR Scanning: Integrate scanner for faster stock operations.",
        "Purchase Order Management: Generate and track POs with suppliers.",
        "Multi-location Support: Track inventory across warehouses.",
        "Email Notifications: Auto alerts when stock falls below reorder level.",
        "Dashboard Charts: Interactive charts using Chart.js for visuals.",
        "Cloud Deployment: Deploy on MongoDB Atlas + Railway for remote access.",
        "Mobile App: Companion app using React Native.",
        "Batch Import: Upload CSV/Excel to bulk-add products.",
        "Audit Logging: Track all user actions (who changed what, when).",
    ])

    # ================================================================
    # 16. CONCLUSION
    # ================================================================
    pdf.section_title("16", "Conclusion")

    pdf.body_text(
        "The Inventory Stock Management System successfully demonstrates the practical application of "
        "MongoDB and PyMongo in building a real-world database-driven application. The project covers "
        "all essential database concepts including:"
    )

    pdf.bullet_list([
        "CRUD operations using insert_one, find, update_one, and delete_one.",
        "Indexing with unique, text, compound, and regular indexes.",
        "Aggregation Pipelines with 7 different stages across 5 reports.",
        "Atomic Operations to prevent race conditions in stock updates.",
        "Schema Design with document references (simulating foreign keys).",
        "Full-Text Search with text indexes and relevance scoring.",
        "Pagination with skip/limit for efficient data retrieval.",
    ])

    pdf.body_text(
        "By providing both a CLI and a modern web interface, the system demonstrates how a "
        "service-oriented architecture allows multiple frontends to share the same business logic "
        "and database layer. The project is ready for production use in small retail environments."
    )

    # ================================================================
    # 17. REFERENCES
    # ================================================================
    pdf.section_title("17", "References")

    refs = [
        "[1] MongoDB Official Documentation - https://www.mongodb.com/docs/manual/",
        "[2] PyMongo Documentation - https://pymongo.readthedocs.io/en/stable/",
        "[3] Flask Documentation - https://flask.palletsprojects.com/",
        "[4] MongoDB Aggregation Pipeline - mongodb.com/docs/manual/core/aggregation-pipeline/",
        "[5] MongoDB Indexes - https://www.mongodb.com/docs/manual/indexes/",
        "[6] MongoDB Atomic Operations - mongodb.com/docs/manual/core/write-operations-atomicity/",
        "[7] Python Official Documentation - https://docs.python.org/3/",
        "[8] MDN Web Docs (HTML/CSS/JS) - https://developer.mozilla.org/",
    ]
    for ref in refs:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*pdf.TEXT)
        pdf.cell(0, 7, ref, new_x="LMARGIN", new_y="NEXT")

    # -- Save --
    os.makedirs("docs", exist_ok=True)
    output_path = "docs/Project_Report_Inventory_Management.pdf"
    pdf.output(output_path)
    print(f"\n[SUCCESS] Report generated: {output_path}")
    print(f"          Total pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    build_report()
