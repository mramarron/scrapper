import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import MthandiziBusinessLead, ScrapedLead
from .services import MarketplaceScraperService, MthandiziScraperService


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
  def test_scrapes_and_updates_directory_businesses(self, mock_get):
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
    profile_response = type(
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
    mock_get.side_effect = [
        directory_response,
        profile_response,
        directory_response,
        profile_response,
    ]

    service = MthandiziScraperService()
    first_result = service.scrape_directory()
    second_result = service.scrape_directory()

    business = MthandiziBusinessLead.objects.get(
        profile_url=(
            "https://mthandizi.com/partners/example-business?ref=marketplace"
        )
    )
    self.assertEqual(first_result, (1, 1))
    self.assertEqual(second_result, (1, 0))
    self.assertEqual(business.business_name, "Example Business")
    self.assertEqual(business.location, "Lilongwe")
    self.assertEqual(business.phone_number, "+265991234567")
    self.assertEqual(business.email, "info@example.mw")
