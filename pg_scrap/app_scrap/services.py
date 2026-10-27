import asyncio
import json
import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
import requests

from .models import MthandiziBusinessLead, ScrapedLead


class MarketplaceScraperService:

  def __init__(self, base_url="https://tisitano.com/?country=Malawi"):
    self.base_url = base_url

  async def scrape_listings(self, max_pages=3):
    async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      try:
        page = await browser.new_page()
        processed_count = 0
        created_count = 0

        for current_page in range(1, max_pages + 1):
          target_url = f"{self.base_url}&page={current_page}"
          response = await page.goto(
              target_url,
              timeout=60000,
              wait_until="domcontentloaded",
          )
          if response is None or response.status >= 400:
            status = response.status if response else "no response"
            raise RuntimeError(
                f"Marketplace returned {status} for page {current_page}"
            )

          html_content = await page.content()
          processed, created = await sync_to_async(
              self._parse_and_save_html,
              thread_sensitive=True,
          )(html_content)
          processed_count += processed
          created_count += created

        return processed_count, created_count
      finally:
        await browser.close()

  def _parse_and_save_html(self, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    next_data = soup.select_one("script#__NEXT_DATA__")
    if next_data is None:
      raise ValueError("Marketplace response did not contain page data")

    page_data = json.loads(next_data.get_text())
    home_object = page_data.get("props", {}).get("pageProps", {}).get(
        "homeObject", {}
    )
    ads = home_object.get("ads")
    if not isinstance(ads, list):
      raise ValueError("Marketplace page data did not contain an ads list")

    processed_count = 0
    created_count = 0

    for ad in ads:
      title = ad.get("title")
      listing_id = ad.get("id")
      if not title or not listing_id:
        continue

      location = ad.get("location") or {}
      location_properties = location.get("properties") or {}
      category = ad.get("category") or {}
      cost = ad.get("cost")
      defaults = {
          "vendor_name": "Tisitano seller",
          "listing_title": title,
          "item_price": Decimal(str(cost)) if cost is not None else None,
          "location_district": (
              location_properties.get("city")
              or location_properties.get("district")
              or location_properties.get("country")
              or "Malawi"
          ),
          "category": category.get("title"),
      }
      _, created = ScrapedLead.objects.update_or_create(
          listing_url=f"https://tisitano.com/addetail/{listing_id}",
          defaults=defaults,
      )
      processed_count += 1
      if created:
        created_count += 1

    return processed_count, created_count




class MthandiziScraperService:

  def __init__(self, base_url="https://mthandizi.com/businesses-in-lilongwe"):
    self.base_url = base_url

  def scrape_directory(self):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    response = requests.get(self.base_url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    listings = soup.select('a[href*="/partners/"]')
    if not listings:
      raise ValueError("Mthandizi directory contained no business profiles")

    processed_count = 0
    created_count = 0
    for card in listings:
      name_elem = card.select_one("h2, h3")
      if name_elem is None:
        continue

      location_icon = card.select_one("svg.lucide-map-pin")
      location_elem = (
          location_icon.find_parent("div").select_one("span")
          if location_icon and location_icon.find_parent("div")
          else None
      )
      profile_url = urljoin(self.base_url, card["href"])
      profile_response = requests.get(
          profile_url,
          headers=headers,
          timeout=30,
      )
      profile_response.raise_for_status()
      profile_soup = BeautifulSoup(profile_response.text, "html.parser")
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

      _, created = MthandiziBusinessLead.objects.update_or_create(
          profile_url=profile_url,
          defaults={
              "business_name": name_elem.get_text(strip=True),
              "phone_number": phone_number,
              "email": email,
              "location": (
                  location_elem.get_text(strip=True)
                  if location_elem
                  else "Lilongwe"
              ),
          },
      )
      processed_count += 1
      if created:
        created_count += 1

    return processed_count, created_count