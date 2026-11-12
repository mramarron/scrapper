import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config.database import Base
from backend.models.models import (
    MthandiziBusinessLead,
    MthandiziBusinessTaxpayerMatch,
)
from backend.services.taxpayer_verification import (
    MthandiziBusinessVerificationService,
    _name_contains_pattern,
)


class FakeResult:
    def __init__(self, rows=None) -> None:
        self.rows = rows or [{"ID": 42, "BUSINESSNAME": "Example Trading"}]

    def mappings(self):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self) -> None:
        self.statement = None
        self.parameters = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement, parameters):
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

    def execute(self, statement, _parameters):
        self.statements.append(str(statement))
        rows = (
            [{"TIN": "TIN-12345"}]
            if "[TIN]" in str(statement)
            else [{"ID": 42, "BUSINESSNAME": "Example Business Limited"}]
        )
        return FakeResult(rows)


class TaxpayerVerificationTests(unittest.TestCase):
    def test_candidate_lookup_requires_exact_email_and_does_not_read_tin(self):
        taxpayer_session = FakeSession()
        verification = MthandiziBusinessVerificationService(
            sessionmaker(), lambda: taxpayer_session
        )

        candidates = verification._find_candidates(
            "Example Trading", "owner@example.com"
        )

        self.assertEqual(candidates, [("42", "Example Trading")])
        self.assertIn("[EMAILADDRESS]", str(taxpayer_session.statement))
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
        verification.approve_candidate(business_id, candidate_id)

        with app_session_factory() as session:
            business = session.get(MthandiziBusinessLead, business_id)
            candidate = session.get(MthandiziBusinessTaxpayerMatch, candidate_id)
            self.assertEqual(business.matched_tin, "TIN-12345")
            self.assertEqual(candidate.status, "approved")

        self.assertIn("[TIN]", taxpayer_database.statements[1])

    def test_name_search_escapes_sql_like_wildcards(self):
        self.assertEqual(
            _name_contains_pattern(" A_%[B]\\ "),
            r"%a\_\%\[b]\\%",
        )


if __name__ == "__main__":
    unittest.main()
