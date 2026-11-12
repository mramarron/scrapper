import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FeaturedProduct:
    listing_url: str
    listing_title: str
    item_price: Decimal | None
    category: str | None


def parse_next_flight_products(
    profile_soup: BeautifulSoup, profile_url: str
) -> list[FeaturedProduct]:
    rows = _parse_rows(profile_soup)
    if not rows:
        return []

    products = []
    seen_urls: set[str] = set()
    for row_value in rows.values():
        for _, props in _iter_elements(row_value, rows):
            product = _parse_product(props, rows, profile_url)
            if product is None or product.listing_url in seen_urls:
                continue
            products.append(product)
            seen_urls.add(product.listing_url)
    return products


def _parse_product(
    props: dict[str, Any], rows: dict[str, Any], profile_url: str
) -> FeaturedProduct | None:
    href = props.get("href")
    if not isinstance(href, str) or not re.match(r"^/shop/[^/?]+/[^/?]+", href):
        return None

    elements = list(_iter_elements(props.get("children"), rows))
    title = _find_element_text(elements, rows, {"h3", "h4"})
    if not title:
        return None

    price = _find_element_text(
        elements,
        rows,
        {"span"},
        contains_text="MWK",
        excluded_class="line-through",
    )
    category = _find_element_text(
        elements, rows, {"span"}, required_class="bg-muted"
    )
    return FeaturedProduct(
        listing_url=urljoin(profile_url, href),
        listing_title=title,
        item_price=_parse_price(price),
        category=category or None,
    )


def _find_element_text(
    elements: list[tuple[str, dict[str, Any]]],
    rows: dict[str, Any],
    tags: set[str],
    contains_text: str | None = None,
    required_class: str | None = None,
    excluded_class: str | None = None,
) -> str:
    for tag, props in elements:
        value = _react_text(props.get("children"), rows).strip()
        if tag not in tags or not value:
            continue
        if contains_text and contains_text.casefold() not in value.casefold():
            continue
        if required_class and not _has_class(props, required_class):
            continue
        if excluded_class and _has_class(props, excluded_class):
            continue
        return value
    return ""


def _parse_rows(profile_soup: BeautifulSoup) -> dict[str, Any]:
    flight_data = "".join(
        json.loads(match.group(1))
        for script in profile_soup.select("script")
        for match in re.finditer(
            r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)',
            script.string or script.get_text(),
        )
    )
    rows = {}
    for line in flight_data.splitlines():
        row = re.match(r"([a-z0-9]+):(.*)", line)
        if row:
            try:
                rows[row.group(1)] = json.loads(row.group(2))
            except json.JSONDecodeError:
                continue
    return rows


def _iter_elements(
    value: Any,
    rows: dict[str, Any],
    seen_rows: frozenset[str] = frozenset(),
) -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, str):
        row_reference = re.fullmatch(r"\$L([a-z0-9]+)", value)
        if (
            row_reference
            and row_reference.group(1) in rows
            and row_reference.group(1) not in seen_rows
        ):
            yield from _iter_elements(
                rows[row_reference.group(1)],
                rows,
                seen_rows | {row_reference.group(1)},
            )
    elif isinstance(value, list):
        if (
            len(value) > 3
            and value[0] == "$"
            and isinstance(value[1], str)
            and isinstance(value[3], dict)
        ):
            yield value[1], value[3]
        for child in value:
            yield from _iter_elements(child, rows, seen_rows)
    elif isinstance(value, dict):
        for child in value.values():
            yield from _iter_elements(child, rows, seen_rows)


def _react_text(
    value: Any,
    rows: dict[str, Any],
    seen_rows: frozenset[str] = frozenset(),
) -> str:
    if isinstance(value, str):
        row_reference = re.fullmatch(r"\$L([a-z0-9]+)", value)
        if (
            row_reference
            and row_reference.group(1) in rows
            and row_reference.group(1) not in seen_rows
        ):
            return _react_text(
                rows[row_reference.group(1)],
                rows,
                seen_rows | {row_reference.group(1)},
            )
        return "" if value.startswith("$") else value
    if isinstance(value, list):
        if (
            len(value) > 3
            and value[0] == "$"
            and isinstance(value[3], dict)
        ):
            return _react_text(value[3].get("children"), rows, seen_rows)
        return " ".join(
            filter(None, (_react_text(child, rows, seen_rows) for child in value))
        )
    if isinstance(value, dict):
        return _react_text(value.get("children"), rows, seen_rows)
    return ""


def _has_class(props: dict[str, Any], class_name: str) -> bool:
    classes = props.get("className")
    return isinstance(classes, str) and class_name in classes.split()


def _parse_price(value: str) -> Decimal | None:
    match = re.search(r"MWK\s*([\d,]+(?:\.\d{1,2})?)", value, re.I)
    return Decimal(match.group(1).replace(",", "")) if match else None
