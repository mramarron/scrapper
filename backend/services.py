import re
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Any, Callable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import MthandiziBusinessLead, ScrapedLead


ProgressCallback = Callable[[dict[str, Any]], None]


class MthandiziDirectoryEmptyError(ValueError):
    pass


class MthandiziScraperService:
    REQUEST_TIMEOUT_SECONDS = 60
    PROFILE_FETCH_WORKERS = 5

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        base_url: str = "https://mthandizi.com/businesses-in-lilongwe",
    ) -> None:
        self.session_factory = session_factory
        self.base_url = base_url

    def scrape_directory(
        self, progress_callback: ProgressCallback | None = None
    ) -> tuple[int, int, int, int]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }
        if progress_callback:
            progress_callback(
                {
                    "stage": "loading_directory",
                    "message": "Loading the Mthandizi business directory",
                }
            )
        response = requests.get(
            self.base_url,
            headers=headers,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select('a[href*="/partners/"]')
        if not listings:
            raise MthandiziDirectoryEmptyError(
                "Mthandizi directory contained no business profiles"
            )

        business_cards = [
            (card, card.select_one("h2, h3"))
            for card in listings
            if card.select_one("h2, h3") is not None
        ]
        businesses_processed = 0
        businesses_added = 0
        products_processed = 0
        products_added = 0

        if progress_callback:
            progress_callback(
                {
                    "stage": "processing_businesses",
                    "message": "Processing business profiles and featured products",
                    "current": 0,
                    "total": len(business_cards),
                    "businesses_processed": 0,
                    "businesses_added": 0,
                    "products_processed": 0,
                    "products_added": 0,
                }
            )

        with ThreadPoolExecutor(
            max_workers=self.PROFILE_FETCH_WORKERS
        ) as executor:
            for batch_start in range(
                0, len(business_cards), self.PROFILE_FETCH_WORKERS
            ):
                batch = [
                    (
                        business_index,
                        card,
                        name_element,
                        urljoin(self.base_url, card["href"]),
                    )
                    for business_index, (card, name_element) in enumerate(
                        business_cards[
                            batch_start : batch_start + self.PROFILE_FETCH_WORKERS
                        ],
                        start=batch_start + 1,
                    )
                ]
                if progress_callback:
                    for business_index, _, name_element, _ in batch:
                        progress_callback(
                            {
                                "stage": "processing_businesses",
                                "message": (
                                    f"Fetching {name_element.get_text(strip=True)}"
                                ),
                                "current": business_index,
                                "total": len(business_cards),
                                "businesses_processed": businesses_processed,
                                "businesses_added": businesses_added,
                                "products_processed": products_processed,
                                "products_added": products_added,
                            }
                        )

                profile_html = executor.map(
                    self._fetch_profile_html,
                    [profile_url for _, _, _, profile_url in batch],
                    [headers] * len(batch),
                )
                for (business_index, card, name_element, profile_url), html in zip(
                    batch, profile_html
                ):
                    business_name = name_element.get_text(strip=True)
                    was_created, count, new_count = self._save_business_profile(
                        card, business_name, profile_url, html
                    )
                    businesses_processed += 1
                    businesses_added += int(was_created)
                    products_processed += count
                    products_added += new_count
                    if progress_callback:
                        progress_callback(
                            {
                                "stage": "processing_businesses",
                                "message": f"Processed {business_name}",
                                "current": business_index,
                                "total": len(business_cards),
                                "businesses_processed": businesses_processed,
                                "businesses_added": businesses_added,
                                "products_processed": products_processed,
                                "products_added": products_added,
                            }
                        )

        return (
            businesses_processed,
            businesses_added,
            products_processed,
            products_added,
        )

    def _fetch_profile_html(self, profile_url: str, headers: dict[str, str]) -> str:
        response = requests.get(
            profile_url,
            headers=headers,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text

    def _save_business_profile(
        self,
        card: Any,
        business_name: str,
        profile_url: str,
        profile_html: str,
    ) -> tuple[bool, int, int]:
        location_icon = card.select_one("svg.lucide-map-pin")
        location_container = (
            location_icon.find_parent("div") if location_icon else None
        )
        location_element = (
            location_container.select_one("span") if location_container else None
        )
        profile_soup = BeautifulSoup(profile_html, "html.parser")
        whatsapp_link = profile_soup.select_one('a[href*="wa.me/"]')
        if whatsapp_link is None:
            whatsapp_link = profile_soup.select_one(
                'a[href*="api.whatsapp.com/send?phone="]'
            )
        phone_link = profile_soup.select_one('a[href^="tel:"]')
        whatsapp_phone = (
            re.search(
                r"(?:wa\.me/|[?&]phone=)(\+?\d+)",
                whatsapp_link["href"],
            )
            if whatsapp_link
            else None
        )
        phone_number = (
            whatsapp_phone.group(1)
            if whatsapp_phone
            else phone_link["href"].removeprefix("tel:")
            if phone_link
            else ""
        )
        email_link = profile_soup.select_one('a[href^="mailto:"]')
        email = (
            email_link["href"].removeprefix("mailto:").split("?", 1)[0].strip()
            if email_link
            else ""
        )
        location = (
            location_element.get_text(strip=True)
            if location_element
            else "Lilongwe"
        )

        with self.session_factory() as session:
            business = session.scalar(
                select(MthandiziBusinessLead).where(
                    MthandiziBusinessLead.profile_url == profile_url
                )
            )
            business_created = business is None
            if business is None:
                business = MthandiziBusinessLead(profile_url=profile_url)
                session.add(business)
            business.business_name = business_name
            business.phone_number = phone_number
            business.email = email
            business.location = location

            products_processed = 0
            products_created = 0
            for product in self._parse_featured_products(
                profile_soup, profile_url
            ):
                listing = session.scalar(
                    select(ScrapedLead).where(
                        ScrapedLead.listing_url == product["listing_url"]
                    )
                )
                if listing is None:
                    listing = ScrapedLead(listing_url=product["listing_url"])
                    session.add(listing)
                    products_created += 1
                listing.source_platform = "Mthandizi"
                listing.vendor_name = business_name
                listing.phone_number = phone_number
                listing.listing_title = product["listing_title"]
                listing.item_price = product["item_price"]
                listing.location_district = location
                listing.category = product["category"]
                products_processed += 1
            session.commit()

        return business_created, products_processed, products_created

    @staticmethod
    def _parse_featured_products(
        profile_soup: BeautifulSoup, profile_url: str
    ) -> list[dict[str, Any]]:
        heading = next(
            (
                element
                for element in profile_soup.select("h2")
                if element.get_text(" ", strip=True).casefold()
                == "featured products"
            ),
            None,
        )
        section = heading.find_parent("section") if heading else None
        if section is None:
            return []

        products = []
        for product_card in section.select('a[href*="/shop/"]'):
            title = product_card.select_one("h3, h4")
            if title is None:
                continue

            price = next(
                (
                    span.get_text(" ", strip=True)
                    for span in product_card.select("span")
                    if "MWK" in span.get_text(" ", strip=True).upper()
                    and "line-through" not in span.get("class", [])
                ),
                "",
            )
            price_match = re.search(
                r"MWK\s*([\d,]+(?:\.\d{1,2})?)", price, re.I
            )
            item_price = (
                Decimal(price_match.group(1).replace(",", ""))
                if price_match
                else None
            )
            category = next(
                (
                    span.get_text(" ", strip=True)
                    for span in product_card.select("span.bg-muted")
                    if span.get_text(" ", strip=True)
                ),
                None,
            )
            products.append(
                {
                    "listing_url": urljoin(profile_url, product_card["href"]),
                    "listing_title": title.get_text(" ", strip=True),
                    "item_price": item_price,
                    "category": category,
                }
            )
        return products


def describe_scrape_error(error: Exception) -> tuple[str, str]:
    if isinstance(error, requests.Timeout):
        return (
            "upstream_timeout",
            "Mthandizi took too long to respond. Please try again shortly.",
        )
    if isinstance(error, requests.ConnectionError):
        return (
            "upstream_unreachable",
            "Could not connect to Mthandizi. Check the connection and try again.",
        )
    if isinstance(error, requests.HTTPError):
        response = error.response
        status_code = response.status_code if response is not None else None
        if status_code == 408:
            return (
                "upstream_timeout",
                "Mthandizi took too long to respond. Please try again shortly.",
            )
        if status_code == 429:
            return (
                "upstream_rate_limited",
                "Mthandizi is receiving too many requests. Please try again later.",
            )
        if status_code in (401, 403):
            return (
                "upstream_access_denied",
                "Mthandizi temporarily refused access. Please try again later.",
            )
        if status_code is not None and status_code >= 500:
            return (
                "upstream_server_error",
                "Mthandizi is experiencing a problem. Please try again later.",
            )
        return (
            "upstream_request_failed",
            "Mthandizi could not provide the requested page. Please try again.",
        )
    if isinstance(error, MthandiziDirectoryEmptyError):
        return (
            "directory_empty",
            "No business profiles were found in the Mthandizi directory.",
        )
    if isinstance(error, SQLAlchemyError):
        return (
            "storage_error",
            "The scraper could not save its results. Please try again.",
        )
    return (
        "unexpected_error",
        "An unexpected error interrupted the scrape. Please try again later.",
    )
