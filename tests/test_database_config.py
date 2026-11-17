import os
import unittest
from unittest.mock import patch

from backend.config.database import _mssql_database_url
from sqlalchemy.dialects.mssql.pyodbc import MSDialect_pyodbc


class MssqlDatabaseConfigTests(unittest.TestCase):
    def test_uses_configured_port_for_sql_login(self) -> None:
        settings = {
            "MSSQL_DB_HOST": "sql.example",
            "MSSQL_DB_PORT": "1433",
            "MSSQL_DB_NAME": "taxpayers",
            "MSSQL_DB_USER": "mndege",
            "MSSQL_DB_PASSWORD": "secret",
        }
        with (
            patch.dict(os.environ, settings, clear=True),
            patch("backend.config.database.MSSQL_ENV_SETTINGS", {}),
        ):
            url = _mssql_database_url()

        self.assertIsNotNone(url)
        self.assertEqual(url.port, 1433)
        self.assertEqual(url.username, "mndege")

    def test_builds_trusted_connection_url_without_credentials(self) -> None:
        settings = {
            "MSSQL_DB_HOST": "sql.example",
            "MSSQL_DB_NAME": "taxpayers",
            "MSSQL_DB_TRUSTED_CONNECTION": "true",
        }
        with (
            patch.dict(os.environ, settings, clear=True),
            patch("backend.config.database.MSSQL_ENV_SETTINGS", {}),
        ):
            if os.name != "nt":
                with self.assertRaisesRegex(ValueError, "requires running"):
                    _mssql_database_url()
                return

            url = _mssql_database_url()

        self.assertIsNotNone(url)
        self.assertIsNone(url.username)
        self.assertIsNone(url.password)
        connection_string = MSDialect_pyodbc().create_connect_args(url)[0][0]
        self.assertIn("Trusted_Connection=Yes", connection_string)
        self.assertEqual(connection_string.count("Trusted_Connection"), 1)

    def test_rejects_sql_credentials_with_trusted_connection(self) -> None:
        settings = {
            "MSSQL_DB_NAME": "taxpayers",
            "MSSQL_DB_TRUSTED_CONNECTION": "true",
            "MSSQL_DB_USER": "sql-user",
        }
        with (
            patch.dict(os.environ, settings, clear=True),
            patch("backend.config.database.MSSQL_ENV_SETTINGS", {}),
        ):
            with self.assertRaisesRegex(ValueError, "Do not set"):
                _mssql_database_url()

    def test_dotenv_windows_auth_settings_override_stale_environment(self) -> None:
        dotenv_settings = {
            "MSSQL_DB_HOST": ".",
            "MSSQL_DB_PORT": "",
            "MSSQL_DB_NAME": "DS_DEV",
            "MSSQL_DB_TRUSTED_CONNECTION": "true",
            "MSSQL_DB_DRIVER": "ODBC Driver 17 for SQL Server",
        }
        stale_environment = {
            "MSSQL_DB_HOST": "remote.example",
            "MSSQL_DB_PORT": "1433",
            "MSSQL_DB_USER": "stale-user",
            "MSSQL_DB_PASSWORD": "stale-password",
            "MSSQL_DATABASE_URL": (
                "mssql+pyodbc://stale-host/Other"
                "?driver=ODBC+Driver+17+for+SQL+Server"
            ),
        }
        with (
            patch.dict(os.environ, stale_environment, clear=True),
            patch(
                "backend.config.database.MSSQL_ENV_SETTINGS",
                dotenv_settings,
            ),
        ):
            url = _mssql_database_url()

        self.assertIsNotNone(url)
        self.assertEqual(url.host, ".")
        self.assertEqual(url.database, "DS_DEV")
        self.assertIsNone(url.port)
        self.assertIsNone(url.username)
        self.assertIsNone(url.password)
        connection_string = MSDialect_pyodbc().create_connect_args(url)[0][0]
        self.assertIn("Trusted_Connection=Yes", connection_string)


if __name__ == "__main__":
    unittest.main()
