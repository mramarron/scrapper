from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel

from backend.models.models import MthandiziBusinessLead, MthandiziScrapeRun, ScrapedLead


class ScrapedListingResponse(BaseModel):
    id: int
    source_platform: str
    vendor_name: str
    phone_number: str | None
    listing_title: str
    item_price: str | None
    location_district: str | None
    category: str | None
    listing_url: str
    scraped_at: str


class BusinessResponse(BaseModel):
    id: int
    business_name: str
    category: str | None
    location: str | None
    phone_number: str
    email: str
    profile_url: str
    scraped_at: str


class ScrapeRunResponse(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: dict[str, Any]
    error_code: str
    output: str
    error: str
    created_at: str
    started_at: str | None
    completed_at: str | None


def _timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def serialize_listing(listing: ScrapedLead) -> ScrapedListingResponse:
    price: Decimal | None = listing.item_price
    return ScrapedListingResponse(
        id=listing.id,
        source_platform=listing.source_platform,
        vendor_name=listing.vendor_name,
        phone_number=listing.phone_number,
        listing_title=listing.listing_title,
        item_price=format(price, ".2f") if price is not None else None,
        location_district=listing.location_district,
        category=listing.category,
        listing_url=listing.listing_url,
        scraped_at=_timestamp(listing.scraped_at),
    )


def serialize_business(business: MthandiziBusinessLead) -> BusinessResponse:
    return BusinessResponse(
        id=business.id,
        business_name=business.business_name,
        category=business.category,
        location=business.location,
        phone_number=business.phone_number,
        email=business.email,
        profile_url=business.profile_url,
        scraped_at=_timestamp(business.scraped_at),
    )


def serialize_scrape_run(run: MthandiziScrapeRun) -> ScrapeRunResponse:
    return ScrapeRunResponse(
        id=str(UUID(hex=run.id)),
        status=run.status,
        progress=run.progress,
        error_code=run.error_code,
        output=run.output,
        error=run.error,
        created_at=_timestamp(run.created_at),
        started_at=_timestamp(run.started_at),
        completed_at=_timestamp(run.completed_at),
    )
