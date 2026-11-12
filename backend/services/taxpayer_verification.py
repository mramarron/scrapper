import logging
import re
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.services.mthandizi_repository import (
    MthandiziLeadRepository,
    TaxpayerMatchAlreadyReviewedError,
)


ProgressCallback = Callable[[dict[str, Any]], None]
logger = logging.getLogger(__name__)


class TaxpayerDatabaseNotConfiguredError(RuntimeError):
    pass


class TaxpayerDatabaseQueryError(RuntimeError):
    pass


class MthandiziBusinessNotFoundError(LookupError):
    pass


class TaxpayerCandidateNotFoundError(LookupError):
    pass


class TaxpayerCandidateNoLongerMatchesError(ValueError):
    pass


class MthandiziBusinessVerificationService:
    CANDIDATE_QUERY = text(
        """
        SELECT [ID], [BUSINESSNAME]
        FROM [dbo].[EIS_Taxpayers_1]
        WHERE LOWER(LTRIM(RTRIM([EMAILADDRESS]))) = LOWER(:email)
          AND LOWER([BUSINESSNAME]) LIKE :name_pattern ESCAPE '\\'
        ORDER BY [BUSINESSNAME], [ID]
        """
    )
    APPROVAL_QUERY = text(
        """
        SELECT [TIN]
        FROM [dbo].[EIS_Taxpayers_1]
        WHERE [ID] = :taxpayer_record_id
          AND LOWER(LTRIM(RTRIM([EMAILADDRESS]))) = LOWER(:email)
          AND LOWER([BUSINESSNAME]) LIKE :name_pattern ESCAPE '\\'
        """
    )

    def __init__(
        self,
        app_session_factory: sessionmaker[Session],
        taxpayer_session_factory: sessionmaker[Session] | None,
    ) -> None:
        self.repository = MthandiziLeadRepository(app_session_factory)
        self.taxpayer_session_factory = taxpayer_session_factory

    def verify_business(self, business_id: int) -> int:
        target = self.repository.get_verification_target(business_id)
        if target is None:
            raise MthandiziBusinessNotFoundError(
                f"Business {business_id} was not found."
            )
        business_name, email = target
        candidates = self._find_candidates(business_name, email)
        self.repository.save_taxpayer_candidates(business_id, candidates)
        return len(candidates)

    def verify_all(
        self, progress_callback: ProgressCallback | None = None
    ) -> tuple[int, int]:
        targets = self.repository.list_verification_targets()
        matches_found = 0
        for index, (business_id, business_name, email) in enumerate(
            targets, start=1
        ):
            candidates = self._find_candidates(business_name, email)
            self.repository.save_taxpayer_candidates(business_id, candidates)
            matches_found += len(candidates)
            if progress_callback:
                progress_callback(
                    {
                        "stage": "verifying_businesses",
                        "message": f"Checked {business_name}",
                        "current": index,
                        "total": len(targets),
                        "businesses_processed": index,
                        "taxpayer_matches_found": matches_found,
                    }
                )
        return len(targets), matches_found

    def approve_candidate(self, business_id: int, match_id: int) -> None:
        candidate = self.repository.get_candidate_for_approval(
            business_id, match_id
        )
        if candidate is None:
            raise TaxpayerCandidateNotFoundError(
                f"Taxpayer candidate {match_id} was not found."
            )
        business_name, email, taxpayer_record_id = candidate
        tin = self._find_approved_tin(
            taxpayer_record_id, business_name, email
        )
        if not tin:
            raise TaxpayerCandidateNoLongerMatchesError(
                "The taxpayer record no longer matches this business."
            )
        if not self.repository.approve_candidate(business_id, match_id, tin):
            raise TaxpayerCandidateNotFoundError(
                f"Taxpayer candidate {match_id} was not found."
            )

    def reject_candidate(self, business_id: int, match_id: int) -> None:
        if not self.repository.reject_candidate(business_id, match_id):
            raise TaxpayerCandidateNotFoundError(
                f"Taxpayer candidate {match_id} was not found."
            )

    def _find_candidates(
        self, business_name: str, email: str
    ) -> list[tuple[str, str]]:
        session_factory = self._require_taxpayer_session()
        if not business_name.strip() or not email.strip():
            return []

        statement_parameters = {
            "email": email.strip(),
            "name_pattern": _name_contains_pattern(business_name),
        }
        rows = self._execute(
            session_factory, self.CANDIDATE_QUERY, statement_parameters
        )
        return [
            (str(row["ID"]), str(row["BUSINESSNAME"]).strip())
            for row in rows
            if row["ID"] is not None and row["BUSINESSNAME"]
        ]

    def _find_approved_tin(
        self, taxpayer_record_id: str, business_name: str, email: str
    ) -> str | None:
        session_factory = self._require_taxpayer_session()
        rows = self._execute(
            session_factory,
            self.APPROVAL_QUERY,
            {
                "taxpayer_record_id": taxpayer_record_id,
                "email": email.strip(),
                "name_pattern": _name_contains_pattern(business_name),
            },
        )
        if not rows or rows[0]["TIN"] is None:
            return None
        return str(rows[0]["TIN"]).strip() or None

    def _require_taxpayer_session(self) -> sessionmaker[Session]:
        if self.taxpayer_session_factory is None:
            raise TaxpayerDatabaseNotConfiguredError(
                "The taxpayer SQL Server connection is not configured."
            )
        return self.taxpayer_session_factory

    @staticmethod
    def _execute(
        session_factory: sessionmaker[Session],
        statement: Any,
        parameters: dict[str, str],
    ) -> list[Any]:
        try:
            with session_factory() as session:
                return session.execute(statement, parameters).mappings().all()
        except SQLAlchemyError as error:
            logger.error(
                "Taxpayer SQL Server query failed (%s).",
                type(error).__name__,
            )
            raise TaxpayerDatabaseQueryError(
                "The taxpayer SQL Server query failed."
            ) from None


def _name_contains_pattern(business_name: str) -> str:
    normalized_name = " ".join(business_name.split()).casefold()
    escaped_name = (
        normalized_name.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
    )
    return f"%{escaped_name}%"
