from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.services.mthandizi_parser import (
    parse_business_profile,
    parse_directory_businesses,
)
from backend.services.mthandizi_repository import MthandiziLeadRepository


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
        self.repository = MthandiziLeadRepository(session_factory)
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

        businesses = parse_directory_businesses(response.text, self.base_url)
        if not businesses:
            raise MthandiziDirectoryEmptyError(
                "Mthandizi directory contained no business profiles"
            )

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
                    "total": len(businesses),
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
                0, len(businesses), self.PROFILE_FETCH_WORKERS
            ):
                batch = [
                    (business_index, business)
                    for business_index, business in enumerate(
                        businesses[
                            batch_start : batch_start + self.PROFILE_FETCH_WORKERS
                        ],
                        start=batch_start + 1,
                    )
                ]
                if progress_callback:
                    for business_index, business in batch:
                        progress_callback(
                            {
                                "stage": "processing_businesses",
                                "message": f"Fetching {business.business_name}",
                                "current": business_index,
                                "total": len(businesses),
                                "businesses_processed": businesses_processed,
                                "businesses_added": businesses_added,
                                "products_processed": products_processed,
                                "products_added": products_added,
                            }
                        )

                profile_html = executor.map(
                    self._fetch_profile_html,
                    [business.profile_url for _, business in batch],
                    [headers] * len(batch),
                )
                for (business_index, business), html in zip(batch, profile_html):
                    profile = parse_business_profile(
                        html, business.profile_url
                    )
                    (
                        business_created,
                        products_processed_count,
                        products_added_count,
                    ) = (
                        self.repository.save_business_profile(business, profile)
                    )
                    businesses_processed += 1
                    businesses_added += int(business_created)
                    products_processed += products_processed_count
                    products_added += products_added_count
                    if progress_callback:
                        progress_callback(
                            {
                                "stage": "processing_businesses",
                                "message": f"Processed {business.business_name}",
                                "current": business_index,
                                "total": len(businesses),
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
