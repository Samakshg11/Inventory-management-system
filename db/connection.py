"""
db/connection.py
----------------
Manages the MongoDB connection using the Singleton pattern.

Why Singleton?
    PyMongo's MongoClient maintains an internal connection pool.
    Creating a new MongoClient on every function call is wasteful and slow.
    One client instance per Python process is the recommended approach.

Usage:
    from db.connection import get_db, get_collection

    db = get_db()                          # returns the inventory_db Database
    products = get_collection("products")  # returns the products Collection
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import MONGO_URI, DB_NAME

# Module-level cache — starts as None, populated on first call to get_client()
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """
    Return the shared MongoClient instance, creating it if it doesn't exist.

    The `serverSelectionTimeoutMS=3000` means PyMongo will give up trying to
    connect after 3 seconds, giving the user a fast error instead of hanging.

    Returns:
        MongoClient: The singleton MongoDB client.

    Raises:
        SystemExit: If MongoDB is not reachable (fail-fast on startup).
    """
    global _client

    if _client is None:
        # Create the client — this does NOT open a connection yet.
        # PyMongo is lazy: the actual TCP connection happens on first operation.
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

        # "ping" forces an immediate connection attempt so we know right away
        # if the MongoDB server is running.
        try:
            _client.admin.command("ping")
            print(f"[DB] Connected to MongoDB at {MONGO_URI}")
        except (ConnectionFailure, ServerSelectionTimeoutError):
            print(
                "\n[ERROR] Cannot connect to MongoDB.\n"
                f"  URI: {MONGO_URI}\n"
                "  Make sure MongoDB is running:  mongod --dbpath /data/db\n"
            )
            raise SystemExit(1)

    return _client


def get_db(db_name: str = DB_NAME) -> Database:
    """
    Return the MongoDB Database object for the given database name.

    Args:
        db_name: Name of the database (defaults to DB_NAME from config).

    Returns:
        Database: The pymongo Database object.
    """
    # Accessing a database by name on a MongoClient is lazy —
    # MongoDB creates the database automatically when the first document
    # is inserted. No explicit "CREATE DATABASE" needed.
    return get_client()[db_name]


def get_collection(collection_name: str, db_name: str = DB_NAME) -> Collection:
    """
    Convenience helper to get a specific collection from the database.

    Args:
        collection_name: Name of the MongoDB collection.
        db_name: Name of the database (defaults to DB_NAME from config).

    Returns:
        Collection: The pymongo Collection object.
    """
    return get_db(db_name)[collection_name]


def close_connection() -> None:
    """
    Close the MongoDB connection and reset the singleton.
    Call this on application exit or in test teardowns.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
        print("[DB] MongoDB connection closed.")
