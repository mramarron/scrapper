from django.core.management.base import BaseCommand
from app_scrap.services import PublicWebScraperService
import asyncio


class Command(BaseCommand):
  help = "Executes the public web scraping and lead staging pipeline."

  def add_arguments(self, parser):
    parser.add_argument(
        "--url", type=str, help="Target URL to scrape", required=True
    )

  def handle(self, *args, **options):
    target_url = options["url"]
    self.stdout.write(
        self.style.NOTICE(f"Starting scraper target: {target_url}")
    )

    scraper = PublicWebScraperService(target_url)

    # Run async playwright loop inside sync Django management command
    loop = asyncio.get_event_loop()
    html_content = loop.run_until_complete(scraper.fetch_page_content())

    staged_records = scraper.parse_and_stage_data(html_content)

    self.stdout.write(
        self.style.SUCCESS(
            f"Successfully scraped and staged {staged_records} leads."
        )
    )