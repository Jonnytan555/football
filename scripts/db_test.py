"""Test the database connection and print available tables."""
import sys
import os

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.db import engine
import sqlalchemy as sa

try:
    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT version()"))
        version = result.scalar()
        print(f"Connected to PostgreSQL: {version}")

        inspector = sa.inspect(engine)
        tables = inspector.get_table_names(schema="public")
        if tables:
            print(f"Tables in public schema: {', '.join(tables)}")
        else:
            print("No tables yet — they will be created on first ingestion run.")

    print("DB connection OK")
    sys.exit(0)

except Exception as e:
    print(f"DB connection FAILED: {e}")
    sys.exit(1)
