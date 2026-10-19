"""
config.py
---------
Loads environment variables from the .env file using python-dotenv and
exposes them as module-level constants. Every other module should import
from here — never read os.environ directly elsewhere.

This centralises all configuration in one place, making it trivial to
switch from a local MongoDB instance to MongoDB Atlas by editing only .env.
"""

import os
from dotenv import load_dotenv

# load_dotenv() reads the .env file in the project root and sets values
# as environment variables. It is safe to call multiple times.
load_dotenv()

# --- MongoDB ---
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME: str = os.getenv("DB_NAME", "inventory_db")
TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", "inventory_test_db")

# --- CLI Behaviour ---
# Number of rows shown per page when listing products
PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "10"))

# --- File Export ---
EXPORT_DIR: str = os.getenv("EXPORT_DIR", "exports")
