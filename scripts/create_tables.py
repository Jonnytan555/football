"""
Create all tables in the configured PostgreSQL database.
Run from the football/ root directory:

    python scripts/create_tables.py

Uses the same connection as the rest of the app (reads from .env or environment variables).
football_teams is excluded — it is auto-created by the ingestion handler on first run.
"""
import os
import sys
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlalchemy as sa
from shared.db import engine

DDL = Path(__file__).parent / "create_tables.sql"

try:
    sql = DDL.read_text()
    with engine.begin() as conn:
        conn.execute(sa.text(sql))
    print("Tables created (or already exist):")
    inspector = sa.inspect(engine)
    for t in sorted(inspector.get_table_names(schema="public")):
        print(f"  {t}")
    print("\nDone. Run ingestion to populate:")
    print("  python -m ingestion.main backfill")
    print("  python -m ingestion.main standings")
    print("  python -m ingestion.main teams")
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
