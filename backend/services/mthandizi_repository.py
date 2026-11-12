from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.models import models
from backend.services.mthandizi_parser import (
    BusinessProfile,
    DirectoryBusiness,
)


class MthandiziLeadRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def save_business_profile(
        self,
        business_entry: DirectoryBusiness,
        profile: BusinessProfile,
    ) -> tuple[bool, int, int]:
        with self.session_factory() as session:
            business_created = self._save_business(
                session, business_entry, profile
            )
            products_processed, products_created = self._save_products(
                session, business_entry, profile
            )
            session.commit()

        return business_created, products_processed, products_created

    def list_verification_targets(self) -> list[tuple[int, str, str]]:
        with self.session_factory() as session:
            rows = session.execute(
                select(
                    models.MthandiziBusinessLead.id,
                    models.MthandiziBusinessLead.business_name,
                    models.MthandiziBusinessLead.email,
                )
            ).all()
        return [(row.id, row.business_name, row.email) for row in rows]

    def get_verification_target(
        self, business_id: int
    ) -> tuple[str, str] | None:
        with self.session_factory() as session:
            business = session.get(models.MthandiziBusinessLead, business_id)
            if business is None:
                return None
            return business.business_name, business.email

    def save_taxpayer_candidates(
        self,
        business_id: int,
        candidates: list[tuple[str, str]],
    ) -> None:
        with self.session_factory() as session:
            business = session.get(models.MthandiziBusinessLead, business_id)
            if business is None:
                raise LookupError(f"Business {business_id} was not found.")

            business.is_checked = True
            existing_matches = session.scalars(
                select(models.MthandiziBusinessTaxpayerMatch).where(
                    models.MthandiziBusinessTaxpayerMatch.business_id
                    == business_id
                )
            ).all()
            existing_by_record_id = {
                match.taxpayer_record_id: match for match in existing_matches
            }
            current_record_ids = {record_id for record_id, _ in candidates}

            for match in existing_matches:
                if (
                    match.status == "pending"
                    and match.taxpayer_record_id not in current_record_ids
                ):
                    session.delete(match)

            for record_id, taxpayer_name in candidates:
                match = existing_by_record_id.get(record_id)
                if match is None:
                    session.add(
                        models.MthandiziBusinessTaxpayerMatch(
                            business_id=business_id,
                            taxpayer_record_id=record_id,
                            taxpayer_business_name=taxpayer_name,
                        )
                    )
                else:
                    match.taxpayer_business_name = taxpayer_name
            session.commit()

    def get_candidate_for_approval(
        self, business_id: int, match_id: int
    ) -> tuple[str, str, str] | None:
        with self.session_factory() as session:
            candidate = session.scalar(
                select(models.MthandiziBusinessTaxpayerMatch).where(
                    models.MthandiziBusinessTaxpayerMatch.id == match_id,
                    models.MthandiziBusinessTaxpayerMatch.business_id
                    == business_id,
                )
            )
            business = session.get(models.MthandiziBusinessLead, business_id)
            if candidate is None or business is None:
                return None
            if candidate.status != "pending":
                raise TaxpayerMatchAlreadyReviewedError(
                    "This taxpayer candidate has already been reviewed."
                )
            return (
                business.business_name,
                business.email,
                candidate.taxpayer_record_id,
            )

    def approve_candidate(
        self, business_id: int, match_id: int, taxpayer_tin: str
    ) -> bool:
        with self.session_factory() as session:
            business = session.get(models.MthandiziBusinessLead, business_id)
            candidate = session.scalar(
                select(models.MthandiziBusinessTaxpayerMatch).where(
                    models.MthandiziBusinessTaxpayerMatch.id == match_id,
                    models.MthandiziBusinessTaxpayerMatch.business_id
                    == business_id,
                )
            )
            if business is None or candidate is None:
                return False
            if candidate.status != "pending":
                raise TaxpayerMatchAlreadyReviewedError(
                    "This taxpayer candidate has already been reviewed."
                )

            candidate.status = "approved"
            business.is_checked = True
            business.matched_tin = taxpayer_tin
            for other_candidate in business.taxpayer_matches:
                if (
                    other_candidate.id != candidate.id
                    and other_candidate.status in ("pending", "approved")
                ):
                    other_candidate.status = "rejected"
            session.commit()
        return True

    def reject_candidate(self, business_id: int, match_id: int) -> bool:
        with self.session_factory() as session:
            candidate = session.scalar(
                select(models.MthandiziBusinessTaxpayerMatch).where(
                    models.MthandiziBusinessTaxpayerMatch.id == match_id,
                    models.MthandiziBusinessTaxpayerMatch.business_id
                    == business_id,
                )
            )
            if candidate is None:
                return False
            if candidate.status != "pending":
                raise TaxpayerMatchAlreadyReviewedError(
                    "This taxpayer candidate has already been reviewed."
                )
            candidate.status = "rejected"
            session.commit()
        return True

    @staticmethod
    def _save_business(
        session: Session,
        business_entry: DirectoryBusiness,
        profile: BusinessProfile,
    ) -> bool:
        business = session.scalar(
            select(models.MthandiziBusinessLead).where(
                models.MthandiziBusinessLead.profile_url
                == business_entry.profile_url
            )
        )
        business_created = business is None
        if business is None:
            business = models.MthandiziBusinessLead(
                profile_url=business_entry.profile_url
            )
            session.add(business)

        business.business_name = business_entry.business_name
        business.phone_number = profile.phone_number
        business.email = profile.email
        business.location = business_entry.location
        return business_created

    @staticmethod
    def _save_products(
        session: Session,
        business_entry: DirectoryBusiness,
        profile: BusinessProfile,
    ) -> tuple[int, int]:
        products_processed = 0
        products_created = 0
        for product in profile.featured_products:
            listing = session.scalar(
                select(models.ScrapedLead).where(
                    models.ScrapedLead.listing_url == product.listing_url
                )
            )
            if listing is None:
                listing = models.ScrapedLead(listing_url=product.listing_url)
                session.add(listing)
                products_created += 1
            listing.source_platform = "Mthandizi"
            listing.vendor_name = business_entry.business_name
            listing.phone_number = profile.phone_number
            listing.listing_title = product.listing_title
            listing.item_price = product.item_price
            listing.location_district = business_entry.location
            listing.category = product.category
            products_processed += 1
        return products_processed, products_created


class TaxpayerMatchAlreadyReviewedError(ValueError):
    pass
