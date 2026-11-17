import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config.database import Base
from backend.models.models import (
    MthandiziBusinessLead,
    MthandiziBusinessTaxpayerMatch,
)
from backend.services.taxpayer_verification import (
    MthandiziBusinessVerificationService,
    TaxpayerDatabaseConnectionError,
    TaxpayerDatabaseQueryError,
    _name_contains_pattern,
)
from backend.routes.directory import _raise_verification_http_error


class FakeResult:
    def __init__(self, rows=None) -> None:
        self.rows = rows or [{"ID": 42, "BUSINESSNAME": "Example Trading"}]

    def mappings(self):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(
        self,
        connection_error: Exception | None = None,
        query_error: Exception | None = None,
    ) -> None:
        self.statement = None
        self.parameters = None
        self.connection_error = connection_error
        self.query_error = query_error
        self.connection_calls = 0
        self.execute_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def connection(self):
        self.connection_calls += 1
        if self.connection_error:
            raise self.connection_error

    def execute(self, statement, parameters):
        self.execute_calls += 1
        if self.query_error:
            raise self.query_error
        self.statement = statement
        self.parameters = parameters
        return FakeResult()


class FakeTaxpayerDatabase:
    def __init__(self) -> None:
        self.statements = []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def connection(self):
        return None

    def execute(self, statement, _parameters):
        self.statements.append(str(statement))
        rows = (
            [{"TIN": "TIN-12345"}]
            if "[TIN]" in str(statement)
            else [{"ID": 42, "BUSINESSNAME": "Example Business Limited"}]
        )
        return FakeResult(rows)


class TaxpayerVerificationTests(unittest.TestCase):
    def test_connection_failure_is_distinct_from_query_failure(self):
        database = FakeSession(
            connection_error=OperationalError(
                "connect", {}, RuntimeError("connection refused")
            )
        )
        verification = MthandiziBusinessVerificationService(
            sessionmaker(), lambda: database
        )

        with self.assertRaises(TaxpayerDatabaseConnectionError):
            verification._find_candidates(
                "Example Trading", "owner@example.com"
            )

        self.assertEqual(database.connection_calls, 1)
        self.assertEqual(database.execute_calls, 0)

    def test_query_failure_is_reported_after_connection_succeeds(self):
        database = FakeSession(
            query_error=ProgrammingError(
                "query", {}, RuntimeError("invalid query")
            )
        )
        verification = MthandiziBusinessVerificationService(
            sessionmaker(), lambda: database
        )

        with self.assertRaises(TaxpayerDatabaseQueryError):
            verification._find_candidates(
                "Example Trading", "owner@example.com"
            )

        self.assertEqual(database.connection_calls, 1)
        self.assertEqual(database.execute_calls, 1)

    def test_connection_and_query_failures_have_distinct_http_codes(self):
        with self.assertRaises(HTTPException) as connection_error:
            _raise_verification_http_error(
                TaxpayerDatabaseConnectionError("offline")
            )

        self.assertEqual(connection_error.exception.status_code, 503)
        self.assertEqual(
            connection_error.exception.detail["code"],
            "taxpayer_connection_error",
        )

        with patch("backend.routes.directory.logger.exception"):
            with self.assertRaises(HTTPException) as query_error:
                _raise_verification_http_error(
                    TaxpayerDatabaseQueryError("invalid query")
                )

        self.assertEqual(query_error.exception.status_code, 500)
        self.assertEqual(
            query_error.exception.detail["code"],
            "taxpayer_query_error",
        )

    def test_candidate_lookup_requires_exact_email_and_does_not_read_tin(self):
        taxpayer_session = FakeSession()
        verification = MthandiziBusinessVerificationService(
            sessionmaker(), lambda: taxpayer_session
        )

        candidates = verification._find_candidates(
            "Example Trading", "owner@example.com"
        )

        self.assertEqual(candidates, [("42", "Example Trading")])
        self.assertIn("FROM [dbo].[Taxpayers]", str(taxpayer_session.statement))
        self.assertIn("[Id] AS [ID]", str(taxpayer_session.statement))
        self.assertIn(
            "[BusinessName] AS [BUSINESSNAME]",
            str(taxpayer_session.statement),
        )
        self.assertIn("[EmailAddress]", str(taxpayer_session.statement))
        self.assertIn("[BUSINESSNAME]", str(taxpayer_session.statement))
        self.assertNotIn("[TIN]", str(taxpayer_session.statement))
        self.assertEqual(
            taxpayer_session.parameters,
            {
                "email": "owner@example.com",
                "name_pattern": "%example trading%",
            },
        )

    def test_tin_is_loaded_and_saved_only_after_candidate_approval(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        app_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        with app_session_factory() as session:
            business = MthandiziBusinessLead(
                business_name="Example Business",
                email="owner@example.com",
                profile_url="https://mthandizi.com/partners/example-business",
            )
            session.add(business)
            session.commit()
            business_id = business.id

        taxpayer_database = FakeTaxpayerDatabase()
        verification = MthandiziBusinessVerificationService(
            app_session_factory, taxpayer_database
        )
        self.assertEqual(verification.verify_business(business_id), 1)

        with app_session_factory() as session:
            business = session.get(MthandiziBusinessLead, business_id)
            candidate = session.scalar(
                select(MthandiziBusinessTaxpayerMatch)
            )
            self.assertTrue(business.is_checked)
            self.assertIsNone(business.matched_tin)
            self.assertEqual(
                candidate.taxpayer_business_name, "Example Business Limited"
            )
            candidate_id = candidate.id

        self.assertNotIn("[TIN]", taxpayer_database.statements[0])
        self.assertIn("FROM [dbo].[Taxpayers]", taxpayer_database.statements[0])
        verification.approve_candidate(business_id, candidate_id)

        with app_session_factory() as session:
            business = session.get(MthandiziBusinessLead, business_id)
            candidate = session.get(MthandiziBusinessTaxpayerMatch, candidate_id)
            self.assertEqual(business.matched_tin, "TIN-12345")
            self.assertEqual(candidate.status, "approved")

        self.assertIn("[TIN]", taxpayer_database.statements[1])
        self.assertIn("FROM [dbo].[Taxpayers]", taxpayer_database.statements[1])

    def test_name_search_escapes_sql_like_wildcards(self):
        self.assertEqual(
            _name_contains_pattern(" A_%[B]\\ "),
            r"%a\_\%\[b]\\%",
        )


if __name__ == "__main__":
    unittest.main()
