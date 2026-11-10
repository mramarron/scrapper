import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
#PG_SCRAP_ROOT = PROJECT_ROOT / "pg_scrap"
load_dotenv(PROJECT_ROOT / ".env")


def _database_url() -> URL | str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    database_name = os.getenv("DB_NAME")
    if database_name:
        return URL.create(
            "postgresql+psycopg2",
            username=os.getenv("DB_USER") or None,
            password=os.getenv("DB_PASSWORD") or None,
            host=os.getenv("DB_HOST") or None,
            port=int(os.environ["DB_PORT"]) if os.getenv("DB_PORT") else None,
            database=database_name,
        )

    return f"connected to {database_name}"


DATABASE_URL = _database_url()
connect_args = (
    {"check_same_thread": False}
    if str(DATABASE_URL).startswith("sqlite")
    else {}
)
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
