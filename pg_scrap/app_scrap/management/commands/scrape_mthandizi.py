from django.core.management.base import BaseCommand
from app_scrap.services import MthandiziScraperService


class Command(BaseCommand):
  help = "Scrapes business listings from Mthandizi's Lilongwe directory."

  def handle(self, *args, **options):
    self.stdout.write(
        self.style.NOTICE("Scraping Mthandizi's Lilongwe business directory...")
    )
    processed_count, created_count = (
        MthandiziScraperService().scrape_directory()
    )
    self.stdout.write(
        self.style.SUCCESS(
            f"Processed {processed_count} businesses; added "
            f"{created_count} new businesses and refreshed "
            f"{processed_count - created_count} existing businesses."
        )
    )
