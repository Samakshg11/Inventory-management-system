"""
tests/test_reports.py
----------------------
Unit tests for services/report_service.py

Tests cover:
  - Low stock report returns correct products
  - Products above reorder level are NOT in low stock report
  - Category stock value report computes correct totals
  - Supplier summary uses $lookup correctly
  - Monthly movement report groups by month and type
  - Top sold products report returns correct ranking
"""

import pytest
from config import TEST_DB_NAME
from db.connection import get_db
from services import product_service, supplier_service, stock_service, report_service

DB = TEST_DB_NAME


def _add_product(sku, name, category, price, quantity, reorder_level=10,
                 supplier_id=None):
    """Shorthand helper to add a product in the test DB."""
    return product_service.add_product(
        sku=sku, name=name, category=category, price=price,
        quantity=quantity, reorder_level=reorder_level,
        supplier_id=supplier_id, db_name=DB,
    )


class TestLowStockReport:
    """Tests for report_service.low_stock_report()"""

    def test_low_stock_returns_correct_products(
        self, clean_products, clean_suppliers
    ):
        """Products at or below reorder_level should appear in the report."""
        # quantity 5 <= reorder_level 10 → should appear
        _add_product("LOW-001", "Low Item", "Test", 100.0, quantity=5, reorder_level=10)
        # quantity 0 <= reorder_level 5 → should appear
        _add_product("LOW-002", "Empty Item", "Test", 50.0, quantity=0, reorder_level=5)
        # quantity 20 > reorder_level 10 → should NOT appear
        _add_product("OK-001", "Stocked Item", "Test", 200.0, quantity=20, reorder_level=10)

        results = report_service.low_stock_report(db_name=DB)
        result_skus = {r["sku"] for r in results}

        assert "LOW-001" in result_skus
        assert "LOW-002" in result_skus
        assert "OK-001" not in result_skus

    def test_low_stock_empty_when_all_stocked(self, clean_products):
        """Report should return empty list when all products are adequately stocked."""
        _add_product("FULL-001", "Full Stock A", "Test", 10.0, quantity=100, reorder_level=10)
        _add_product("FULL-002", "Full Stock B", "Test", 20.0, quantity=50, reorder_level=5)

        results = report_service.low_stock_report(db_name=DB)
        assert results == []

    def test_low_stock_exactly_at_reorder_level(self, clean_products):
        """A product exactly AT reorder_level (quantity == reorder_level) should appear."""
        # quantity == reorder_level means we need to reorder right now
        _add_product("EQ-001", "Exact Reorder", "Test", 15.0, quantity=10, reorder_level=10)

        results = report_service.low_stock_report(db_name=DB)
        result_skus = {r["sku"] for r in results}
        assert "EQ-001" in result_skus


class TestCategoryStockValueReport:
    """Tests for report_service.category_stock_value_report()"""

    def test_category_totals_are_correct(self, clean_products):
        """
        Category aggregation should correctly compute:
          - total_products (COUNT)
          - total_quantity (SUM of quantity)
          - total_value (SUM of price * quantity)
        """
        # Electronics: 2 products
        #   ELEC-T1: price=100, qty=10 → value=1000
        #   ELEC-T2: price=200, qty=5  → value=1000
        # Total Electronics value = 2000
        _add_product("ELEC-T1", "Elec Product 1", "Electronics", 100.0, 10)
        _add_product("ELEC-T2", "Elec Product 2", "Electronics", 200.0, 5)

        # Books: 1 product
        #   BOOK-T1: price=50, qty=20 → value=1000
        _add_product("BOOK-T1", "Book 1", "Books", 50.0, 20)

        results = report_service.category_stock_value_report(db_name=DB)

        # Build a lookup by category
        by_cat = {r["category"]: r for r in results}

        assert "Electronics" in by_cat
        assert by_cat["Electronics"]["total_products"] == 2
        assert by_cat["Electronics"]["total_quantity"] == 15    # 10+5
        assert by_cat["Electronics"]["total_value"] == 2000.0  # 1000+1000

        assert "Books" in by_cat
        assert by_cat["Books"]["total_value"] == 1000.0        # 50*20

    def test_category_sorted_by_value_desc(self, clean_products):
        """Results should be sorted by total_value descending."""
        _add_product("HIGH-001", "Expensive Item", "Luxury", 10000.0, 10)
        _add_product("LOW-001", "Cheap Item", "Budget", 1.0, 5)

        results = report_service.category_stock_value_report(db_name=DB)

        # Luxury (10000*10=100000) should come before Budget (1*5=5)
        categories = [r["category"] for r in results]
        assert categories.index("Luxury") < categories.index("Budget")


class TestSupplierSummaryReport:
    """Tests for report_service.supplier_summary_report()"""

    def test_supplier_lookup_joins_name(self, clean_products, clean_suppliers):
        """Supplier summary should include supplier name via $lookup."""
        # Add a real supplier
        sup_result = supplier_service.add_supplier(
            "Report Supplier", "report@sup.com", db_name=DB
        )
        sup = get_db(DB)["suppliers"].find_one({"_id": sup_result["inserted_id"]})

        _add_product("SUP-001", "Linked Product", "Test", 100.0, 10,
                     supplier_id=sup["_id"])
        _add_product("SUP-002", "Another Linked", "Test", 200.0, 20,
                     supplier_id=sup["_id"])

        results = report_service.supplier_summary_report(db_name=DB)

        # Find our supplier's row
        our_row = next(
            (r for r in results if r.get("supplier_name") == "Report Supplier"), None
        )
        assert our_row is not None
        assert our_row["product_count"] == 2
        assert our_row["total_quantity"] == 30   # 10 + 20


class TestMonthlyMovementReport:
    """Tests for report_service.monthly_movement_report()"""

    def test_monthly_report_groups_by_type(
        self, clean_products, clean_transactions, sample_supplier
    ):
        """
        Monthly report should produce separate rows for IN and OUT
        for the same month.
        """
        _add_product("MOVE-001", "Movable Product", "Test", 50.0, 100)

        stock_service.stock_in("MOVE-001", 30, db_name=DB)
        stock_service.stock_out("MOVE-001", 10, db_name=DB)
        stock_service.stock_in("MOVE-001", 20, db_name=DB)

        results = report_service.monthly_movement_report(db_name=DB)

        types_found = {r["type"] for r in results}
        assert "IN" in types_found
        assert "OUT" in types_found

        # Total IN should be 30 + 20 = 50
        in_rows = [r for r in results if r["type"] == "IN"]
        total_in = sum(r["total_quantity"] for r in in_rows)
        assert total_in == 50

        # Total OUT should be 10
        out_rows = [r for r in results if r["type"] == "OUT"]
        total_out = sum(r["total_quantity"] for r in out_rows)
        assert total_out == 10


class TestTopSoldReport:
    """Tests for report_service.top_sold_products_report()"""

    def test_top_sold_returns_max_5(self, clean_products, clean_transactions):
        """Report should return at most 5 products even if more were sold."""
        # Create 7 products and sell different quantities from each
        for i in range(7):
            _add_product(f"SOLD-{i:03d}", f"Sold Product {i}", "Test",
                         10.0, quantity=1000)
            stock_service.stock_out(f"SOLD-{i:03d}", (i + 1) * 10, db_name=DB)

        results = report_service.top_sold_products_report(db_name=DB)
        assert len(results) <= 5

    def test_top_sold_sorted_by_quantity_desc(self, clean_products, clean_transactions):
        """The product with highest total OUT should appear first."""
        _add_product("BEST-001", "Best Seller", "Test", 10.0, quantity=500)
        _add_product("SLOW-001", "Slow Seller", "Test", 10.0, quantity=500)

        stock_service.stock_out("BEST-001", 100, db_name=DB)
        stock_service.stock_out("SLOW-001", 10, db_name=DB)

        results = report_service.top_sold_products_report(db_name=DB)

        assert len(results) >= 2
        # First result must be the best seller
        assert results[0]["sku"] == "BEST-001"
        assert results[0]["total_sold"] == 100

    def test_top_sold_empty_without_out_transactions(
        self, clean_products, clean_transactions
    ):
        """If no Stock OUT has been recorded, report should be empty."""
        _add_product("NOSELL-001", "Unsold Product", "Test", 10.0, quantity=50)
        # Only do a Stock IN, no OUT
        stock_service.stock_in("NOSELL-001", 10, db_name=DB)

        results = report_service.top_sold_products_report(db_name=DB)
        assert results == []
