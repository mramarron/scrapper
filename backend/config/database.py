import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _database_url() -> URL | str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    database_name = os.getenv("DB_NAME")
    if database_name:
        database_engine = os.getenv("DB_ENGINE", "postgresql").lower()
        if database_engine == "postgresql":
            drivername = "postgresql+psycopg2"
            query = None
        elif database_engine == "mssql":
            drivername = "mssql+pyodbc"
            query = {
                "driver": os.getenv("DB_DRIVER") or "ODBC Driver 18 for SQL Server"
            }
        else:
            raise ValueError(
                f"Unsupported DB_ENGINE {database_engine!r}; "
                "expected 'postgresql' or 'mssql'."
            )

        database_port = os.getenv("DB_PORT")
        return URL.create(
            drivername,
            username=os.getenv("DB_USER") or None,
            password=os.getenv("DB_PASSWORD") or None,
            host=os.getenv("DB_HOST") or None,
            port=int(database_port) if database_port else None,
            database=database_name,
            query=query or {},
        )

    return f"sqlite:///{PROJECT_ROOT / 'pg_scrap' / 'db.sqlite3'}"


def _mssql_database_url() -> URL | str | None:
    database_url = os.getenv("MSSQL_DATABASE_URL")
    if database_url:
        return database_url

    database_name = os.getenv("MSSQL_DB_NAME")
    mssql_settings = (
        "MSSQL_DB_HOST",
        "MSSQL_DB_PORT",
        "MSSQL_DB_USER",
        "MSSQL_DB_PASSWORD",
        "MSSQL_DB_DRIVER",
    )
    if not database_name:
        if any(os.getenv(setting) for setting in mssql_settings):
            raise ValueError(
                "MSSQL_DB_NAME is required when configuring the secondary "
                "SQL Server connection."
            )
        return None

    database_port = os.getenv("MSSQL_DB_PORT")
    return URL.create(
        "mssql+pyodbc",
        username=os.getenv("MSSQL_DB_USER") or None,
        password=os.getenv("MSSQL_DB_PASSWORD") or None,
        host=os.getenv("MSSQL_DB_HOST") or None,
        port=int(database_port) if database_port else None,
        database=database_name,
        query={
            "driver": os.getenv("MSSQL_DB_DRIVER")
            or "ODBC Driver 18 for SQL Server"
        },
    )


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

MSSQL_DATABASE_URL = _mssql_database_url()
mssql_engine = (
    create_engine(MSSQL_DATABASE_URL, pool_pre_ping=True)
    if MSSQL_DATABASE_URL is not None
    else None
)
MSSQLSessionLocal = (
    sessionmaker(
        bind=mssql_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    if mssql_engine is not None
    else None
)


class Base(DeclarativeBase):
    pass
