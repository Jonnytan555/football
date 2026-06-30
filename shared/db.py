import os
import sqlalchemy as sa

engine = sa.create_engine(
    "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
        os.getenv("DB_USER", "postgres"),
        os.getenv("DB_PASSWORD", ""),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_PORT", "5432"),
        os.getenv("DB_NAME", "footyhub"),
    ),
    pool_pre_ping=True,
)
