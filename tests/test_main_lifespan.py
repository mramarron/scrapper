import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI

from backend.main import engine, lifespan


class AppLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_taxpayer_sql_server_is_not_required_at_startup(self) -> None:
        taxpayer_engine = Mock()
        with (
            patch("backend.main.Base.metadata.create_all") as create_all,
            patch("backend.main.mssql_engine", taxpayer_engine, create=True),
        ):
            async with lifespan(FastAPI()):
                pass

        create_all.assert_called_once_with(bind=engine)
        taxpayer_engine.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
