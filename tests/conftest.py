"""
tests/conftest.py
------------------
Shared pytest fixtures for all test modules.

Key design decisions:
  - All tests use 'inventory_test_db' (never the real 'inventory_db').
  - Each test gets CLEAN collections (all documents deleted before the test).
  - Indexes are created once for the test DB so services work correctly.
  - The 'db_name' parameter is passed explicitly to service functions.

pytest fixtures:
  @pytest.fixture creates a reusable setup/teardown function.
  'yield' separates setup (before yield) from teardown (after yield).
  scope="session" means the fixture runs ONCE for the entire test session.
"""

import pytest
from db.connection import get_db, get_client
from db.indexes import create_indexes
from config import TEST_DB_NAME


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Session-scoped fixture: connect to MongoDB and create indexes for test DB.

    autouse=True means this runs automatically for every test in the session
    without needing to explicitly include it in each test function.
    """
    # Ensure MongoDB is reachable before running any tests
    get_client()
    # Create indexes in the test database so unique constraints work
    create_indexes(db_name=TEST_DB_NAME)
    yield
    # Teardown: drop the entire test database after all tests complete
    get_db(TEST_DB_NAME).client.drop_database(TEST_DB_NAME)


@pytest.fixture()
def clean_products():
    """
    Function-scoped fixture: yield empty 'products' collection.

    Deletes ALL documents before each test that uses this fixture.
    This ensures tests are independent — one test's data doesn't affect another.
    """
    col = get_db(TEST_DB_NAME)["products"]
    col.delete_many({})   # wipe before test
    yield col
    col.delete_many({})   # wipe after test (belt and suspenders)


@pytest.fixture()
def clean_suppliers():
    """
    Function-scoped fixture: yield empty 'suppliers' collection.
    """
    col = get_db(TEST_DB_NAME)["suppliers"]
    col.delete_many({})
    yield col
    col.delete_many({})


@pytest.fixture()
def clean_transactions():
    """
    Function-scoped fixture: yield empty 'transactions' collection.
    """
    col = get_db(TEST_DB_NAME)["transactions"]
    col.delete_many({})
    yield col
    col.delete_many({})


@pytest.fixture()
def sample_supplier(clean_suppliers):
    """
    Insert one supplier into the test DB and return it.

    Depends on clean_suppliers — so the collection is already wiped.
    """
    from services.supplier_service import add_supplier
    result = add_supplier(
        name="Test Supplier",
        email="test@supplier.com",
        phone="9000000001",
        address="Test City",
        db_name=TEST_DB_NAME,
    )
    assert result["success"], "Fixture: supplier insert failed"
    supplier = get_db(TEST_DB_NAME)["suppliers"].find_one(
        {"_id": result["inserted_id"]}
    )
    return supplier


@pytest.fixture()
def sample_product(clean_products, sample_supplier):
    """
    Insert one product into the test DB and return it.

    Depends on sample_supplier so supplier_id is a valid ObjectId.
    """
    from services.product_service import add_product
    result = add_product(
        sku="TEST-001",
        name="Test Widget",
        category="Test Category",
        price=99.99,
        quantity=50,
        reorder_level=10,
        supplier_id=sample_supplier["_id"],
        tags=["test", "widget"],
        db_name=TEST_DB_NAME,
    )
    assert result["success"], "Fixture: product insert failed"
    product = get_db(TEST_DB_NAME)["products"].find_one({"sku": "TEST-001"})
    return product
