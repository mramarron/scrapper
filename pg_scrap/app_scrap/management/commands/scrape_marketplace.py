from django.core.management.base import BaseCommand
from app_scrap.services import MarketplaceScraperService
from app_scrap.services import MthandiziScraperService
import asyncio


class Command(BaseCommand):
  help = "Scrapes active commercial listings from classified platforms like Tisitano Malawi."

  def add_arguments(self, parser):
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pagination pages to crawl",
    )

  def handle(self, *args, **options):
    max_pages = options["pages"]
    self.stdout.write(
        self.style.NOTICE(
            f"Initializing Tisitano Malawi scraper for {max_pages} pages..."
        )
    )

    scraper = MarketplaceScraperService()
    processed_count, created_count = asyncio.run(
        scraper.scrape_listings(max_pages=max_pages)
    )

    self.stdout.write(
        self.style.SUCCESS(
            f"Processed {processed_count} marketplace listings; "
            f"added {created_count} new listings and refreshed "
            f"{processed_count - created_count} existing listings."
        )
    )