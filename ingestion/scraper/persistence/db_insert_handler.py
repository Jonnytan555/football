import logging
import uuid

import pandas as pd
import sqlalchemy as sa

from ingestion.scraper.persistence.persistence_handler import PersistenceHandler


class DbInsertHandler(PersistenceHandler):
    """PostgreSQL-compatible insert handler. Skips rows that already exist based on key_cols."""

    def __init__(self, engine: sa.Engine, table_name: str, schema: str = "public", key_cols: list[str] | None = None) -> None:
        self.engine = engine
        self.table_name = table_name
        self.schema = schema
        self.key_cols = key_cols or []

    def handle(self, df: pd.DataFrame, dropNa: bool = False, dtypes=None, created_date: str = "CreatedDate") -> list[dict]:
        if df is None or df.empty:
            return []

        temp = f"{self.table_name}_tmp_{uuid.uuid4().hex[:12]}"
        columns = df.columns.tolist()
        col_list = ", ".join(f'"{c}"' for c in columns)
        src_cols = ", ".join(f'"{c}"' for c in columns)

        try:
            inspector = sa.inspect(self.engine)
            if not inspector.has_table(self.table_name, schema=self.schema):
                df.head(0).to_sql(self.table_name, con=self.engine, schema=self.schema, if_exists="fail", index=False)
                if self.key_cols:
                    constraint = f"uq_{self.table_name}_{'_'.join(self.key_cols)}"
                    key_col_list = ", ".join(f'"{c}"' for c in self.key_cols)
                    with self.engine.begin() as conn:
                        conn.execute(sa.text(
                            f'ALTER TABLE "{self.schema}"."{self.table_name}" '
                            f'ADD CONSTRAINT "{constraint}" UNIQUE ({key_col_list})'
                        ))
                logging.info("[DbInsertHandler] Created table %s.%s", self.schema, self.table_name)

            df.to_sql(temp, con=self.engine, schema=self.schema, if_exists="replace", index=False)

            if self.key_cols:
                conflict_cols = ", ".join(f'"{c}"' for c in self.key_cols)
                insert_sql = f"""
                    INSERT INTO "{self.schema}"."{self.table_name}" ({col_list})
                    SELECT {src_cols} FROM "{self.schema}"."{temp}"
                    ON CONFLICT ({conflict_cols}) DO NOTHING
                    RETURNING *
                """
            else:
                insert_sql = f"""
                    INSERT INTO "{self.schema}"."{self.table_name}" ({col_list})
                    SELECT {src_cols} FROM "{self.schema}"."{temp}"
                    RETURNING *
                """

            with self.engine.begin() as conn:
                result = conn.execute(sa.text(insert_sql))
                rows = result.fetchall()
                keys = list(result.keys())

            inserted = [dict(zip(keys, row)) for row in rows]
            logging.info("[DbInsertHandler] Inserted %d rows into %s.%s", len(inserted), self.schema, self.table_name)
            return inserted

        except Exception:
            logging.exception("[DbInsertHandler] Failed to insert into %s.%s", self.schema, self.table_name)
            raise

        finally:
            self._drop_temp(temp)

    def _drop_temp(self, temp: str) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(sa.text(f'DROP TABLE IF EXISTS "{self.schema}"."{temp}"'))
        except Exception:
            logging.warning("[DbInsertHandler] Failed to drop temp %s", temp)
