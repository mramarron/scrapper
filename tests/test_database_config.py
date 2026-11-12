import os
import unittest
from unittest.mock import patch

from backend.config.database import _mssql_database_url
from sqlalchemy.dialects.mssql.pyodbc import MSDialect_pyodbc


class MssqlDatabaseConfigTests(unittest.TestCase):
    def test_builds_trusted_connection_url_without_credentials(self) -> None:
        settings = {
            "MSSQL_DB_HOST": "sql.example",
            "MSSQL_DB_NAME": "taxpayers",
            "MSSQL_DB_TRUSTED_CONNECTION": "true",
        }
        with patch.dict(os.environ, settings, clear=True):
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
        with patch.dict(os.environ, settings, clear=True):
            with self.assertRaisesRegex(ValueError, "Do not set"):
                _mssql_database_url()


if __name__ == "__main__":
    unittest.main()
