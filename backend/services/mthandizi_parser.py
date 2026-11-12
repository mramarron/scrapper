import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from backend.services.next_flight import (
    FeaturedProduct,
    parse_next_flight_products,
)


@dataclass(frozen=True)
class DirectoryBusiness:
    business_name: str
    profile_url: str
    location: str


@dataclass(frozen=True)
class BusinessProfile:
    phone_number: str
    email: str
    featured_products: list[FeaturedProduct]


def parse_directory_businesses(
    directory_html: str, base_url: str
) -> list[DirectoryBusiness]:
    soup = BeautifulSoup(directory_html, "html.parser")
    businesses = []
    for card in soup.select('a[href*="/partners/"]'):
        name_element = card.select_one("h2, h3")
        if name_element is None:
            continue
        businesses.append(
            DirectoryBusiness(
                business_name=name_element.get_text(strip=True),
                profile_url=urljoin(base_url, card["href"]),
                location=_parse_location(card),
            )
        )
    return businesses


def parse_business_profile(
    profile_html: str, profile_url: str
) -> BusinessProfile:
    soup = BeautifulSoup(profile_html, "html.parser")
    whatsapp_link = soup.select_one('a[href*="wa.me/"]')
    if whatsapp_link is None:
        whatsapp_link = soup.select_one(
            'a[href*="api.whatsapp.com/send?phone="]'
        )
    phone_link = soup.select_one('a[href^="tel:"]')
    whatsapp_phone = (
        re.search(
            r"(?:wa\.me/|[?&]phone=)(\+?\d+)",
            whatsapp_link["href"],
        )
        if whatsapp_link
        else None
    )
    if whatsapp_phone:
        phone_number = whatsapp_phone.group(1)
    elif phone_link:
        phone_number = phone_link["href"].removeprefix("tel:")
    else:
        phone_number = ""
    email_link = soup.select_one('a[href^="mailto:"]')
    email = (
        email_link["href"].removeprefix("mailto:").split("?", 1)[0].strip()
        if email_link
        else ""
    )
    return BusinessProfile(
        phone_number=phone_number,
        email=email,
        featured_products=parse_featured_products(soup, profile_url),
    )


def parse_featured_products(
    profile_soup: BeautifulSoup, profile_url: str
) -> list[FeaturedProduct]:
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
    if section is not None:
        products = _parse_html_products(section, profile_url)
        if products:
            return products
    return parse_next_flight_products(profile_soup, profile_url)


def _parse_location(card: Tag) -> str:
    location_icon = card.select_one("svg.lucide-map-pin")
    location_container = location_icon.find_parent("div") if location_icon else None
    location_element = (
        location_container.select_one("span") if location_container else None
    )
    if location_element:
        return location_element.get_text(strip=True)
    return "Lilongwe"


def _parse_html_products(section: Tag, profile_url: str) -> list[FeaturedProduct]:
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
        category = next(
            (
                span.get_text(" ", strip=True)
                for span in product_card.select("span.bg-muted")
                if span.get_text(" ", strip=True)
            ),
            None,
        )
        products.append(
            FeaturedProduct(
                listing_url=urljoin(profile_url, product_card["href"]),
                listing_title=title.get_text(" ", strip=True),
                item_price=_parse_price(price),
                category=category,
            )
        )
    return products


def _parse_price(value: str) -> Decimal | None:
    match = re.search(r"MWK\s*([\d,]+(?:\.\d{1,2})?)", value, re.I)
    return Decimal(match.group(1).replace(",", "")) if match else None
