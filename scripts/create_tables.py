"""
Create all tables in the configured PostgreSQL database.
Run from the football/ root directory:

    python scripts/create_tables.py

Reads each file in scripts/sql/ in alphabetical order.
football_teams is excluded — auto-created by the ingestion handler on first run.
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlalchemy as sa
from shared.db import engine

SQL_DIR = Path(__file__).parent / "sql"

try:
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    with engine.begin() as conn:
        for f in sql_files:
            conn.execute(sa.text(f.read_text()))
            print(f"  OK  {f.name}")

    print("\nTables in database:")
    inspector = sa.inspect(engine)
    for t in sorted(inspector.get_table_names(schema="public")):
        print(f"  {t}")

    print("\nNext steps:")
    print("  python -m ingestion.main backfill 2024")
    print("  python -m ingestion.main standings 2024")
    print("  python -m ingestion.main teams")

except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
