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
