import json
import threading
import uuid
from decimal import Decimal
from types import SimpleNamespace

import requests
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import MthandiziBusinessLead, MthandiziScrapeRun, ScrapedLead
from .services import (
    MarketplaceScraperService,
    MthandiziDirectoryEmptyError,
    MthandiziScraperService,
)


class MarketplaceListViewTests(TestCase):
  def test_homepage_renders_saved_listings_and_mthandizi_businesses(self):
    listing = ScrapedLead.objects.create(
        vendor_name="Classified Vendor",
        listing_title="Used bicycle",
        item_price="125000.00",
        location_district="Lilongwe",
        listing_url="https://example.com/listings/bicycle",
    )

    business = MthandiziBusinessLead.objects.create(
        business_name="Lilongwe Hardware",
        location="Area 3, Lilongwe",
        phone_number="+265 999 123 456",
        email="contact@lilongwehardware.mw",
        profile_url="https://mthandizi.com/partners/lilongwe-hardware",
    )

    response = self.client.get(reverse("marketplace_list"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, listing.listing_title)
    self.assertContains(response, "125000.00")
    self.assertContains(response, listing.location_district)
    self.assertContains(response, business.business_name)
    self.assertContains(response, business.location)
    self.assertContains(response, business.phone_number)
    self.assertContains(response, business.email)
    self.assertContains(response, f"mailto:{business.email}")
    self.assertContains(response, business.profile_url)


class DirectoryApiTests(TestCase):
  def test_lists_marketplace_listings_and_businesses(self):
    listing = ScrapedLead.objects.create(
        vendor_name="Classified Vendor",
        listing_title="Used bicycle",
        item_price="125000.00",
        location_district="Lilongwe",
        listing_url="https://example.com/listings/bicycle",
    )
    business = MthandiziBusinessLead.objects.create(
        business_name="Lilongwe Hardware",
        location="Area 3, Lilongwe",
        phone_number="+265 999 123 456",
        email="contact@lilongwehardware.mw",
        profile_url="https://mthandizi.com/partners/lilongwe-hardware",
    )

    listings_response = self.client.get("/api/marketplace-listings/")
    businesses_response = self.client.get("/api/businesses/")

    self.assertEqual(listings_response.status_code, 200)
    self.assertEqual(businesses_response.status_code, 200)
    self.assertEqual(
        listings_response.json()[0]["listing_title"], listing.listing_title
    )
    self.assertEqual(
        listings_response.json()[0]["item_price"], "125000.00"
    )
    self.assertEqual(
        businesses_response.json()[0]["business_name"], business.business_name
    )
    self.assertEqual(
        businesses_response.json()[0]["email"], business.email
    )

  def test_directory_endpoints_are_read_only(self):
    listing_response = self.client.post("/api/marketplace-listings/", {})
    business_response = self.client.post("/api/businesses/", {})

    self.assertEqual(listing_response.status_code, 405)
    self.assertEqual(business_response.status_code, 405)


class MarketplaceScraperServiceTests(TestCase):
  def test_parses_minimal_listing_data_from_page_props(self):
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(
            {
                "props": {
                    "pageProps": {
                        "homeObject": {
                            "ads": [
                                {
                                    "id": "listing-123",
                                    "title": "Used bicycle",
                                    "cost": 125000,
                                    "location": {
                                        "properties": {
                                            "city": "Lilongwe",
                                            "country": "Malawi",
                                        }
                                    },
                                    "category": {"title": "Vehicles"},
                                }
                            ]
                        }
                    }
                }
            }
        )
        + "</script>"
    )

    service = MarketplaceScraperService()
    processed_count, created_count = service._parse_and_save_html(html)
    listing = ScrapedLead.objects.get(
        listing_url="https://tisitano.com/addetail/listing-123"
    )
    second_processed_count, second_created_count = (
        service._parse_and_save_html(html)
    )

    self.assertEqual(processed_count, 1)
    self.assertEqual(created_count, 1)
    self.assertEqual(second_processed_count, 1)
    self.assertEqual(second_created_count, 0)
    self.assertEqual(ScrapedLead.objects.count(), 1)
    self.assertEqual(listing.listing_title, "Used bicycle")
    self.assertEqual(listing.item_price, Decimal("125000"))
    self.assertEqual(listing.location_district, "Lilongwe")
    self.assertEqual(listing.category, "Vehicles")


class MthandiziScraperServiceTests(TestCase):
  @patch("app_scrap.services.requests.get")
  def test_fetches_business_profiles_with_bounded_concurrency(self, mock_get):
    directory_html = "".join(
        f'<a href="/partners/business-{index}"><h3>Business {index}</h3></a>'
        for index in range(4)
    )
    active_requests = 0
    max_active_requests = 0
    profile_request_count = 0
    lock = threading.Lock()
    first_pair_started = threading.Barrier(2)

    def fake_get(url, **kwargs):
      nonlocal active_requests, max_active_requests, profile_request_count
      if url.endswith("/businesses-in-lilongwe"):
        return SimpleNamespace(
            text=directory_html,
            raise_for_status=lambda: None,
        )

      with lock:
        profile_request_count += 1
        request_number = profile_request_count
        active_requests += 1
        max_active_requests = max(max_active_requests, active_requests)
      try:
        if request_number <= 2:
          first_pair_started.wait(timeout=3)
        return SimpleNamespace(
            text="<main></main>",
            raise_for_status=lambda: None,
        )
      finally:
        with lock:
          active_requests -= 1

    mock_get.side_effect = fake_get
    service = MthandiziScraperService()
    service.PROFILE_FETCH_WORKERS = 2

    result = service.scrape_directory()

    self.assertEqual(result, (4, 4, 0, 0))
    self.assertEqual(max_active_requests, 2)

  @patch("app_scrap.services.requests.get")
  def test_discovers_new_products_for_existing_businesses(self, mock_get):
    directory_response = mock_get.return_value
    directory_response.status_code = 200
    directory_response.text = """
      <a href="/partners/example-business?ref=marketplace">
        <div>
          <h3>Example Business</h3>
          <div><svg class="lucide-map-pin"></svg><span>Lilongwe</span></div>
        </div>
      </a>
    """
    existing_profile_response = type(
        "Response",
        (),
        {
            "status_code": 200,
            "text": (
                '<a href="https://wa.me/message/QSZPRR7EZHFVH1">WhatsApp</a>'
                '<a href="tel:+265991234567">Call Business</a>'
                '<a href="mailto:info@example.mw">Email</a>'
            ),
            "raise_for_status": lambda self: None,
        },
    )()
    profile_response = type(
        "Response",
        (),
        {
            "status_code": 200,
            "text": (
                '<a href="https://wa.me/message/QSZPRR7EZHFVH1">WhatsApp</a>'
                '<a href="tel:+265991234567">Call Business</a>'
                '<a href="mailto:info@example.mw">Email</a>'
                '<section><h2>Featured products</h2>'
                '<a href="/shop/example-business/widget?ref=partner_profile">'
                '<h3>Widget</h3><span class="bg-muted">Retail</span>'
                '<span>MWK 12,500</span>'
                '<span class="line-through">MWK 15,000</span></a>'
                '<a href="/shop/example-business">'
                '<span>Visit shop</span></a></section>'
            ),
            "raise_for_status": lambda self: None,
        },
    )()
    mock_get.side_effect = [
        directory_response,
        existing_profile_response,
        directory_response,
        profile_response,
        directory_response,
        profile_response,
    ]

    service = MthandiziScraperService()
    progress_updates = []
    first_result = service.scrape_directory(progress_updates.append)
    self.assertEqual(mock_get.call_args_list[0].kwargs["timeout"], 60)
    self.assertEqual(mock_get.call_args_list[1].kwargs["timeout"], 60)
    second_result = service.scrape_directory(progress_updates.append)
    third_result = service.scrape_directory(progress_updates.append)

    business = MthandiziBusinessLead.objects.get(
        profile_url=(
            "https://mthandizi.com/partners/example-business?ref=marketplace"
        )
    )
    product = ScrapedLead.objects.get(
        listing_url=(
            "https://mthandizi.com/shop/example-business/widget"
            "?ref=partner_profile"
        )
    )
    self.assertEqual(first_result, (1, 1, 0, 0))
    self.assertEqual(second_result, (1, 0, 1, 1))
    self.assertEqual(third_result, (1, 0, 1, 0))
    self.assertEqual(mock_get.call_count, 6)
    self.assertEqual(business.business_name, "Example Business")
    self.assertEqual(business.location, "Lilongwe")
    self.assertEqual(business.phone_number, "+265991234567")
    self.assertEqual(business.email, "info@example.mw")
    self.assertEqual(ScrapedLead.objects.count(), 1)
    self.assertEqual(product.source_platform, "Mthandizi")
    self.assertEqual(product.vendor_name, "Example Business")
    self.assertEqual(product.phone_number, "+265991234567")
    self.assertEqual(product.listing_title, "Widget")
    self.assertEqual(product.item_price, Decimal("12500"))
    self.assertEqual(product.location_district, "Lilongwe")
    self.assertEqual(product.category, "Retail")
    self.assertEqual(progress_updates[0]["stage"], "loading_directory")
    self.assertEqual(progress_updates[1]["stage"], "processing_businesses")
    self.assertEqual(progress_updates[-1]["businesses_processed"], 1)
    self.assertEqual(progress_updates[-5]["products_processed"], 1)
    self.assertEqual(progress_updates[-5]["products_added"], 1)
    self.assertIn("Processed Example Business", progress_updates[-1]["message"])


class MthandiziScrapeEndpointTests(TestCase):
  def test_scrape_errors_map_to_stable_aliases(self):
    from .views import _describe_scrape_error

    rate_limited_response = requests.Response()
    rate_limited_response.status_code = 429
    rate_limited_error = requests.HTTPError(
        response=rate_limited_response
    )

    self.assertEqual(
        _describe_scrape_error(MthandiziDirectoryEmptyError())[0],
        MthandiziScrapeRun.ErrorCode.DIRECTORY_EMPTY,
    )
    self.assertEqual(
        _describe_scrape_error(rate_limited_error)[0],
        MthandiziScrapeRun.ErrorCode.UPSTREAM_RATE_LIMITED,
    )

  @patch("app_scrap.views.scrape_executor.submit")
  def test_post_starts_scrape_and_returns_run_status(self, submit):
    response = self.client.post(reverse("mthandizi-scrape"))

    self.assertEqual(response.status_code, 202)
    self.assertEqual(response.json()["status"], "queued")
    self.assertTrue(
        MthandiziScrapeRun.objects.get(pk=response.json()["id"]).is_active
    )
    submit.assert_called_once()

  @patch("app_scrap.views.scrape_executor.submit")
  def test_post_returns_existing_run_when_scrape_is_active(self, submit):
    active_run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())

    response = self.client.post(reverse("mthandizi-scrape"))

    self.assertEqual(response.status_code, 202)
    self.assertEqual(response.json()["id"], str(active_run.id))
    self.assertEqual(MthandiziScrapeRun.objects.count(), 1)
    submit.assert_not_called()

  def test_get_returns_scrape_run_status(self):
    run = MthandiziScrapeRun.objects.create(
        id=uuid.uuid4(),
        status=MthandiziScrapeRun.Status.RUNNING,
        progress={
            "stage": "processing_businesses",
            "message": "Processing Example Business",
            "current": 1,
            "total": 3,
        },
    )

    response = self.client.get(
        reverse("mthandizi-scrape-run", kwargs={"run_id": run.id})
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["id"], str(run.id))
    self.assertEqual(response.json()["status"], "running")
    self.assertEqual(response.json()["progress"], run.progress)
    self.assertEqual(response.json()["error_code"], "")

  @patch("app_scrap.views.call_command")
  def test_worker_records_successful_command_output(self, call_command_mock):
    call_command_mock.side_effect = (
        lambda name, stdout, stderr, run_id: stdout.write("Scraper finished.")
    )
    run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())

    from .views import _execute_mthandizi_scrape

    _execute_mthandizi_scrape(run.id)
    run.refresh_from_db()

    self.assertEqual(run.status, MthandiziScrapeRun.Status.COMPLETED)
    self.assertFalse(run.is_active)
    self.assertIsNotNone(run.started_at)
    self.assertIsNotNone(run.completed_at)
    self.assertEqual(run.output, "Scraper finished.")
    self.assertEqual(run.progress["stage"], "completed")
    self.assertEqual(run.error_code, "")
    self.assertIn("run_id", call_command_mock.call_args.kwargs)

  @patch(
      "app_scrap.management.commands.scrape_mthandizi."
      "MthandiziScraperService.scrape_directory"
  )
  def test_management_command_persists_service_progress(self, scrape_directory):
    def report_progress(progress_callback):
      progress_callback({
          "stage": "processing_businesses",
          "message": "Processing Example Business",
          "current": 1,
          "total": 1,
          "businesses_processed": 0,
          "products_processed": 0,
      })
      return 1, 1, 0, 0

    scrape_directory.side_effect = report_progress
    run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())

    call_command("scrape_mthandizi", run_id=str(run.id))
    run.refresh_from_db()

    self.assertEqual(
        run.progress["message"],
        "Processing Example Business",
    )

  @patch("app_scrap.views.call_command", side_effect=RuntimeError("raw secret"))
  def test_worker_records_failed_command(self, call_command_mock):
    run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())

    from .views import _execute_mthandizi_scrape

    with self.assertLogs("app_scrap.views", level="ERROR"):
      _execute_mthandizi_scrape(run.id)
    run.refresh_from_db()

    self.assertEqual(run.status, MthandiziScrapeRun.Status.FAILED)
    self.assertFalse(run.is_active)
    self.assertEqual(
        run.error_code,
        MthandiziScrapeRun.ErrorCode.UNEXPECTED_ERROR,
    )
    self.assertEqual(
        run.error,
        "An unexpected error interrupted the scrape. Please try again later.",
    )
    self.assertNotIn("raw secret", run.error)

  @patch(
      "app_scrap.views.call_command",
      side_effect=requests.Timeout("request timed out"),
  )
  def test_worker_maps_upstream_timeout_to_safe_error_alias(
      self, call_command_mock
  ):
    run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())

    from .views import _execute_mthandizi_scrape

    with self.assertLogs("app_scrap.views", level="ERROR"):
      _execute_mthandizi_scrape(run.id)
    run.refresh_from_db()

    self.assertEqual(
        run.error_code,
        MthandiziScrapeRun.ErrorCode.UPSTREAM_TIMEOUT,
    )
    self.assertEqual(
        run.error,
        "Mthandizi took too long to respond. Please try again shortly.",
    )

  def test_start_failure_includes_worker_error_alias(self):
    with self.assertLogs("app_scrap.views", level="ERROR"):
      with patch(
          "app_scrap.views.scrape_executor.submit",
          side_effect=RuntimeError("executor stopped"),
      ):
        response = self.client.post(reverse("mthandizi-scrape"))

    run = MthandiziScrapeRun.objects.get(pk=response.json()["id"])
    self.assertEqual(response.status_code, 503)
    self.assertEqual(
        response.json()["error_code"],
        MthandiziScrapeRun.ErrorCode.WORKER_UNAVAILABLE,
    )
    self.assertEqual(
        run.error_code,
        MthandiziScrapeRun.ErrorCode.WORKER_UNAVAILABLE,
    )
