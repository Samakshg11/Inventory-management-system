"""
tests/test_stock.py
--------------------
Unit tests for services/stock_service.py

Tests cover:
  - Stock IN increases quantity correctly
  - Stock IN logs a transaction
  - Stock OUT decreases quantity correctly
  - Stock OUT logs a transaction
  - Stock OUT FAILS when requested quantity > available stock (CRITICAL TEST)
  - Stock does not go negative (the atomic guard works)
  - Stock IN/OUT on non-existent SKU returns error
"""

import pytest
from config import TEST_DB_NAME
from db.connection import get_db
from services import stock_service, product_service

DB = TEST_DB_NAME


class TestStockIn:
    """Tests for stock_service.stock_in()"""

    def test_stock_in_increases_quantity(self, sample_product, clean_transactions):
        """Stock IN should increase the product quantity by the given amount."""
        initial_qty = sample_product["quantity"]   # 50 from fixture

        result = stock_service.stock_in("TEST-001", 20, note="Test IN", db_name=DB)

        assert result["success"] is True
        assert result["new_quantity"] == initial_qty + 20

        # Verify in DB
        updated = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert updated["quantity"] == initial_qty + 20

    def test_stock_in_logs_transaction(self, sample_product, clean_transactions):
        """Stock IN should create one transaction record of type 'IN'."""
        stock_service.stock_in("TEST-001", 10, note="PO-9999", db_name=DB)

        txn_col = get_db(DB)["transactions"]
        txns = list(txn_col.find({"type": "IN"}))

        assert len(txns) == 1
        assert txns[0]["quantity"] == 10
        assert txns[0]["note"] == "PO-9999"
        assert txns[0]["type"] == "IN"
        assert txns[0]["product_id"] == sample_product["_id"]

    def test_stock_in_nonexistent_sku(self, clean_products, clean_transactions):
        """Stock IN on a non-existent SKU should fail gracefully."""
        result = stock_service.stock_in("GHOST-999", 10, db_name=DB)
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestStockOut:
    """Tests for stock_service.stock_out()"""

    def test_stock_out_decreases_quantity(self, sample_product, clean_transactions):
        """Stock OUT should decrease the product quantity by the given amount."""
        initial_qty = sample_product["quantity"]   # 50 from fixture

        result = stock_service.stock_out("TEST-001", 15, note="Invoice-001", db_name=DB)

        assert result["success"] is True
        assert result["new_quantity"] == initial_qty - 15

        # Verify in DB
        updated = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert updated["quantity"] == initial_qty - 15

    def test_stock_out_logs_transaction(self, sample_product, clean_transactions):
        """Stock OUT should create one transaction record of type 'OUT'."""
        stock_service.stock_out("TEST-001", 5, note="Customer: Raj", db_name=DB)

        txn_col = get_db(DB)["transactions"]
        txns = list(txn_col.find({"type": "OUT"}))

        assert len(txns) == 1
        assert txns[0]["quantity"] == 5
        assert txns[0]["type"] == "OUT"
        assert txns[0]["product_id"] == sample_product["_id"]

    def test_stock_out_insufficient_stock(self, sample_product, clean_transactions):
        """
        Stock OUT with more units than available should FAIL.

        This is the CRITICAL TEST that verifies the atomic guard:
            update_one({"quantity": {"$gte": requested}}, ...)

        The product has 50 units. We request 100 → should be rejected.
        The quantity must remain 50 after the failed operation.
        """
        initial_qty = sample_product["quantity"]  # 50
        requested = initial_qty + 50              # 100 > 50

        result = stock_service.stock_out("TEST-001", requested, db_name=DB)

        # The operation must fail
        assert result["success"] is False
        assert "insufficient" in result["error"].lower()

        # Quantity must NOT have changed
        updated = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert updated["quantity"] == initial_qty  # still 50

        # No transaction should have been logged for this failed operation
        txn_col = get_db(DB)["transactions"]
        assert txn_col.count_documents({}) == 0

    def test_stock_out_exact_quantity(self, sample_product, clean_transactions):
        """Stock OUT of the EXACT available quantity should succeed (qty becomes 0)."""
        exact_qty = sample_product["quantity"]  # 50

        result = stock_service.stock_out("TEST-001", exact_qty, db_name=DB)

        assert result["success"] is True
        assert result["new_quantity"] == 0

        updated = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert updated["quantity"] == 0

    def test_stock_out_nonexistent_sku(self, clean_products, clean_transactions):
        """Stock OUT on a non-existent SKU should fail gracefully."""
        result = stock_service.stock_out("GHOST-999", 5, db_name=DB)
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_stock_does_not_go_negative(self, sample_product, clean_transactions):
        """
        After a failed Stock OUT, the quantity must remain non-negative.

        Even if multiple OUT attempts fail, quantity must never drop below 0.
        This verifies the atomic $gte filter is working correctly.
        """
        product_service.update_product("TEST-001", {"quantity": 5}, db_name=DB)

        # Try to take out 10 when only 5 available
        result = stock_service.stock_out("TEST-001", 10, db_name=DB)
        assert result["success"] is False

        final = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert final["quantity"] >= 0   # MUST be non-negative


class TestTransactionHistory:
    """Tests for stock_service.get_transaction_history()"""

    def test_transaction_history_order(self, sample_product, clean_transactions):
        """Transactions should be returned newest first."""
        stock_service.stock_in("TEST-001", 10, db_name=DB)
        stock_service.stock_out("TEST-001", 3, db_name=DB)
        stock_service.stock_in("TEST-001", 5, db_name=DB)

        history = stock_service.get_transaction_history("TEST-001", db_name=DB)

        assert len(history) == 3
        # Newest should be the last stock_in (qty=5)
        assert history[0]["quantity"] == 5
        assert history[0]["type"] == "IN"
