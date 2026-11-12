import unittest
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config.database import Base
from backend.models.models import MthandiziBusinessLead, ScrapedLead
from backend.services.mthandizi_parser import (
    BusinessProfile,
    DirectoryBusiness,
    FeaturedProduct,
)
from backend.services.mthandizi_repository import MthandiziLeadRepository


class MthandiziLeadRepositoryTests(unittest.TestCase):
    def test_saves_and_refreshes_business_and_featured_product(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        repository = MthandiziLeadRepository(session_factory)
        business = DirectoryBusiness(
            business_name="Example Business",
            profile_url="https://mthandizi.com/partners/example-business",
            location="Area 10",
        )
        product = FeaturedProduct(
            listing_url="https://mthandizi.com/shop/example-business/example-product",
            listing_title="Example Product",
            item_price=Decimal("12345.50"),
            category="Agriculture",
        )
        profile = BusinessProfile(
            phone_number="265991234567",
            email="hello@example.com",
            featured_products=[product],
        )

        self.assertEqual(
            repository.save_business_profile(business, profile), (True, 1, 1)
        )
        updated_profile = BusinessProfile(
            phone_number="265991234568",
            email="updated@example.com",
            featured_products=[product],
        )
        self.assertEqual(
            repository.save_business_profile(business, updated_profile),
            (False, 1, 0),
        )

        with session_factory() as session:
            saved_business = session.scalar(select(MthandiziBusinessLead))
            saved_product = session.scalar(select(ScrapedLead))

        self.assertEqual(saved_business.phone_number, "265991234568")
        self.assertEqual(saved_product.vendor_name, "Example Business")
        self.assertEqual(saved_product.phone_number, "265991234568")
        self.assertEqual(saved_product.item_price, Decimal("12345.50"))


if __name__ == "__main__":
    unittest.main()
