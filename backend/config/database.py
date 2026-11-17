import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
MSSQL_ENV_SETTINGS = dotenv_values(ENV_FILE)
load_dotenv(ENV_FILE)


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
    database_url = _mssql_setting("MSSQL_DATABASE_URL")
    if database_url:
        return database_url

    database_name = _mssql_setting("MSSQL_DB_NAME")
    trusted_connection = _mssql_trusted_connection_enabled()
    if not database_name:
        if trusted_connection or any(
            _mssql_setting(setting)
            for setting in (
                "MSSQL_DB_HOST",
                "MSSQL_DB_PORT",
                "MSSQL_DB_USER",
                "MSSQL_DB_PASSWORD",
                "MSSQL_DB_DRIVER",
            )
        ):
            raise ValueError(
                "MSSQL_DB_NAME is required when configuring the secondary "
                "SQL Server connection."
            )
        return None

    username = _mssql_setting("MSSQL_DB_USER") or None
    password = _mssql_setting("MSSQL_DB_PASSWORD") or None
    if trusted_connection and (username or password):
        raise ValueError(
            "Do not set MSSQL_DB_USER or MSSQL_DB_PASSWORD when using "
            "Windows authentication."
        )
    if trusted_connection and os.name != "nt":
        raise ValueError(
            "Windows authentication requires running the application on Windows."
        )

    database_port = _mssql_setting("MSSQL_DB_PORT")
    query = {
        "driver": _mssql_setting("MSSQL_DB_DRIVER")
        or "ODBC Driver 18 for SQL Server"
    }

    # The pyodbc dialect uses Trusted_Connection when credentials are omitted.
    return URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,
        host=_mssql_setting("MSSQL_DB_HOST") or None,
        port=int(database_port) if database_port else None,
        database=database_name,
        query=query,
    )


def _mssql_setting(name: str, default: str | None = None) -> str | None:
    if any(setting.startswith("MSSQL_") for setting in MSSQL_ENV_SETTINGS):
        return MSSQL_ENV_SETTINGS.get(name, default)
    return os.getenv(name, default)


def _mssql_trusted_connection_enabled() -> bool:
    value = (
        _mssql_setting("MSSQL_DB_TRUSTED_CONNECTION", "false") or "false"
    ).strip().lower()
    if value in {"1", "true", "yes"}:
        return True
    if value in {"0", "false", "no", ""}:
        return False
    raise ValueError(
        "MSSQL_DB_TRUSTED_CONNECTION must be true or false."
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
    create_engine(
        MSSQL_DATABASE_URL,
        connect_args={"timeout": 5},
        pool_pre_ping=True,
    )
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
