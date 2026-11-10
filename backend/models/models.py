from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, Numeric
from sqlalchemy import String, Text, text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ScrapedLead(Base):
    __tablename__ = "app_scrap_scrapedlead"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_platform: Mapped[str] = mapped_column(
        String(100), default="Tisitano Malawi", nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(50))
    listing_title: Mapped[str] = mapped_column(String(255), nullable=False)
    item_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    location_district: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    listing_url: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matched_tin: Mapped[str | None] = mapped_column(String(50))
    match_confidence_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class MthandiziBusinessLead(Base):
    __tablename__ = "app_scrap_mthandizibusinesslead"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(254), default="", nullable=False)
    profile_url: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matched_tin: Mapped[str | None] = mapped_column(String(50))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class MthandiziScrapeRun(Base):
    __tablename__ = "app_scrap_mthandiziscraperun"
    __table_args__ = (
        Index(
            "one_active_mthandizi_scrape",
            "is_active",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(20), default="queued", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    progress: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    error_code: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    output: Mapped[str] = mapped_column(Text, default="", nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
