"""Standalone, read-only SQL Server check using Windows authentication."""

import sys
from pathlib import Path

import pyodbc
from dotenv import dotenv_values


def _odbc_value(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def main() -> int:
    settings = dotenv_values(Path(__file__).resolve().with_name(".env"))

    database = (settings.get("MSSQL_DB_NAME") or "").strip()
    if not database:
        print("MSSQL_DB_NAME is missing.", file=sys.stderr)
        return 2

    host = (settings.get("MSSQL_DB_HOST") or "").strip() or "."
    port = (settings.get("MSSQL_DB_PORT") or "").strip()
    if port:
        try:
            port_number = int(port)
        except ValueError:
            print("MSSQL_DB_PORT must be an integer.", file=sys.stderr)
            return 2
        server = f"{host},{port_number}"
    else:
        server = host

    driver = (
        settings.get("MSSQL_DB_DRIVER") or "ODBC Driver 17 for SQL Server"
    ).strip()

    connection_parts = [
        f"DRIVER={_odbc_value(driver)}",
        f"SERVER={_odbc_value(server)}",
        f"DATABASE={_odbc_value(database)}",
        "Trusted_Connection=Yes",
    ]

    try:
        connection = pyodbc.connect(
            ";".join(connection_parts),
            timeout=5,
        )
    except pyodbc.Error as error:
        print(f"SQL Server connection failed: {error}", file=sys.stderr)
        return 1

    try:
        cursor = connection.cursor()
        try:
            taxpayer_count = cursor.execute(
                "SELECT COUNT(*) AS [total] FROM [dbo].[Taxpayers]"
            ).fetchone()[0]
        except pyodbc.Error as error:
            print(
                f"Connected, but counting dbo.Taxpayers failed: {error}",
                file=sys.stderr,
            )
            return 1
        finally:
            cursor.close()
    finally:
        connection.close()

    print(
        f"Connection succeeded. dbo.Taxpayers contains {taxpayer_count:,} "
        f"rows in database {database!r}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
