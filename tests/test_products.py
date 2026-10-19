"""
tests/test_products.py
-----------------------
Unit tests for services/product_service.py

Tests cover:
  - Adding a product successfully
  - Rejecting duplicate SKUs (unique index)
  - Fetching a product by SKU
  - Searching by name (text + regex)
  - Filtering by category
  - Updating a product
  - Deleting a product
  - Pagination
"""

import pytest
from config import TEST_DB_NAME
from services import product_service


DB = TEST_DB_NAME   # shorthand for the test DB name


class TestAddProduct:
    """Tests for product_service.add_product()"""

    def test_add_product_success(self, clean_products, sample_supplier):
        """Adding a valid product should succeed and return an inserted_id."""
        result = product_service.add_product(
            sku="P-001", name="Test Laptop", category="Electronics",
            price=45000.0, quantity=10, reorder_level=5,
            supplier_id=sample_supplier["_id"], db_name=DB,
        )
        assert result["success"] is True
        assert result["inserted_id"] is not None

    def test_add_product_sku_uppercased(self, clean_products, sample_supplier):
        """SKU should be stored in uppercase regardless of input case."""
        product_service.add_product(
            sku="lowercase-sku", name="Test Item", category="General",
            price=10.0, quantity=5, db_name=DB,
        )
        product = product_service.get_product_by_sku("lowercase-sku", db_name=DB)
        assert product is not None
        assert product["sku"] == "LOWERCASE-SKU"

    def test_add_product_duplicate_sku(self, clean_products, sample_supplier):
        """Inserting a product with a duplicate SKU should fail gracefully."""
        product_service.add_product(
            sku="DUPE-001", name="Product A", category="Electronics",
            price=100.0, quantity=10, db_name=DB,
        )
        # Second insert with same SKU
        result = product_service.add_product(
            sku="DUPE-001", name="Product B", category="Electronics",
            price=200.0, quantity=5, db_name=DB,
        )
        assert result["success"] is False
        assert "already exists" in result["error"].lower() or "dupe-001" in result["error"].upper()

    def test_add_product_price_stored_rounded(self, clean_products):
        """Price should be stored rounded to 2 decimal places."""
        product_service.add_product(
            sku="ROUND-001", name="Rounded Priced Item", category="Test",
            price=9.9999, quantity=1, db_name=DB,
        )
        product = product_service.get_product_by_sku("ROUND-001", db_name=DB)
        assert product["price"] == 10.0  # rounded from 9.9999


class TestGetProduct:
    """Tests for get_product_by_sku, get_all_products, distinct_categories."""

    def test_get_product_by_sku_found(self, sample_product):
        """Should find an existing product by SKU."""
        product = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert product is not None
        assert product["name"] == "Test Widget"

    def test_get_product_by_sku_not_found(self, clean_products):
        """Should return None for a non-existent SKU."""
        result = product_service.get_product_by_sku("NOPE-999", db_name=DB)
        assert result is None

    def test_get_all_products_pagination(self, clean_products, sample_supplier):
        """Pagination should return correct products and page counts."""
        # Insert 15 products
        for i in range(15):
            product_service.add_product(
                sku=f"PAGE-{i:03d}", name=f"Paginated Product {i}",
                category="Test", price=10.0, quantity=5, db_name=DB,
            )

        page1 = product_service.get_all_products(page=1, db_name=DB)
        assert page1["total"] == 15
        assert len(page1["products"]) == 10    # PAGE_SIZE = 10
        assert page1["total_pages"] == 2

        page2 = product_service.get_all_products(page=2, db_name=DB)
        assert len(page2["products"]) == 5

    def test_get_distinct_categories(self, clean_products):
        """distinct_categories should return unique sorted category list."""
        for cat in ["Electronics", "Books", "Electronics", "Clothing"]:
            product_service.add_product(
                sku=f"CAT-{cat[:4].upper()}-{id(cat)}", name=f"Item {cat}",
                category=cat, price=10.0, quantity=1, db_name=DB,
            )
        categories = product_service.get_distinct_categories(db_name=DB)
        assert "Electronics" in categories
        assert "Books" in categories
        assert "Clothing" in categories
        # Should not have duplicates
        assert len(categories) == len(set(categories))


class TestSearchProduct:
    """Tests for search_products and filter_by_category."""

    def test_search_by_name_regex(self, clean_products):
        """Regex search should find partial name matches."""
        product_service.add_product(
            sku="SRCH-001", name="Blue Mechanical Keyboard",
            category="Electronics", price=3000.0, quantity=10, db_name=DB,
        )
        results = product_service.search_products("Keyboard", db_name=DB)
        names = [p["name"] for p in results]
        assert any("Keyboard" in n for n in names)

    def test_filter_by_category(self, clean_products):
        """filter_by_category should return only matching category products."""
        product_service.add_product(
            sku="FLT-001", name="Running Shoes",
            category="Sports", price=2000.0, quantity=5, db_name=DB,
        )
        product_service.add_product(
            sku="FLT-002", name="Notebook",
            category="Books", price=100.0, quantity=20, db_name=DB,
        )
        results = product_service.filter_by_category("Sports", db_name=DB)
        assert len(results) == 1
        assert results[0]["sku"] == "FLT-001"


class TestUpdateProduct:
    """Tests for product_service.update_product()"""

    def test_update_product_price(self, sample_product):
        """Updating price should reflect in a subsequent fetch."""
        result = product_service.update_product(
            "TEST-001", {"price": 149.99}, db_name=DB
        )
        assert result["success"] is True

        updated = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert updated["price"] == 149.99

    def test_update_nonexistent_product(self, clean_products):
        """Updating a product that doesn't exist should fail gracefully."""
        result = product_service.update_product(
            "GHOST-999", {"price": 1.0}, db_name=DB
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestDeleteProduct:
    """Tests for product_service.delete_product()"""

    def test_delete_product_success(self, sample_product):
        """Deleting an existing product should succeed."""
        result = product_service.delete_product("TEST-001", db_name=DB)
        assert result["success"] is True

        # Verify it no longer exists
        product = product_service.get_product_by_sku("TEST-001", db_name=DB)
        assert product is None

    def test_delete_nonexistent_product(self, clean_products):
        """Deleting a product that doesn't exist should fail gracefully."""
        result = product_service.delete_product("GHOST-000", db_name=DB)
        assert result["success"] is False
        assert "not found" in result["error"].lower()
