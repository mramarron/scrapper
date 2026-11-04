from django.core.management.base import BaseCommand
from app_scrap.services import MthandiziScraperService
from app_scrap.models import MthandiziScrapeRun


class Command(BaseCommand):
  help = (
      "Scrapes business profiles and featured products from Mthandizi's "
      "Lilongwe directory."
  )

  def add_arguments(self, parser):
    parser.add_argument("--run-id", help="Persist progress for this scrape run.")

  def handle(self, *args, **options):
    run_id = options.get("run_id")
    progress_callback = None
    if run_id:
      progress_callback = lambda progress: MthandiziScrapeRun.objects.filter(
          pk=run_id
      ).update(progress=progress)

    self.stdout.write(
        self.style.NOTICE("Scraping Mthandizi's Lilongwe business directory...")
    )
    (
        processed_count,
        created_count,
        processed_product_count,
        created_product_count,
    ) = (
        MthandiziScraperService().scrape_directory(
            progress_callback=progress_callback
        )
    )
    self.stdout.write(
        self.style.SUCCESS(
            f"Processed {processed_count} businesses; added "
            f"{created_count} new businesses and refreshed "
            f"{processed_count - created_count} existing businesses. "
            f"Processed {processed_product_count} featured products; added "
            f"{created_product_count} new products and refreshed "
            f"{processed_product_count - created_product_count} existing "
            "products."
        )
    )
