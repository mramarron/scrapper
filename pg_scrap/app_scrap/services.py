import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
import requests

from .models import MthandiziBusinessLead, ScrapedLead


class MthandiziDirectoryEmptyError(ValueError):
  pass


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
  REQUEST_TIMEOUT_SECONDS = 60
  PROFILE_FETCH_WORKERS = 5

  def __init__(self, base_url="https://mthandizi.com/businesses-in-lilongwe"):
    self.base_url = base_url

  def scrape_directory(self, progress_callback=None):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    if progress_callback:
      progress_callback({
          "stage": "loading_directory",
          "message": "Loading the Mthandizi business directory",
      })
    response = requests.get(
        self.base_url,
        headers=headers,
        timeout=self.REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    listings = soup.select('a[href*="/partners/"]')
    if not listings:
      raise MthandiziDirectoryEmptyError(
          "Mthandizi directory contained no business profiles"
      )

    business_cards = [
        (card, card.select_one("h2, h3"))
        for card in listings
        if card.select_one("h2, h3") is not None
    ]
    processed_count = 0
    created_count = 0
    processed_product_count = 0
    created_product_count = 0
    if progress_callback:
      progress_callback({
          "stage": "processing_businesses",
          "message": "Processing business profiles and featured products",
          "current": 0,
          "total": len(business_cards),
          "businesses_processed": 0,
          "businesses_added": 0,
          "products_processed": 0,
          "products_added": 0,
      })
    with ThreadPoolExecutor(
        max_workers=self.PROFILE_FETCH_WORKERS
    ) as executor:
      for batch_start in range(
          0, len(business_cards), self.PROFILE_FETCH_WORKERS
      ):
        batch = [
            (
                business_index,
                card,
                name_elem,
                urljoin(self.base_url, card["href"]),
            )
            for business_index, (card, name_elem) in enumerate(
                business_cards[
                    batch_start:batch_start + self.PROFILE_FETCH_WORKERS
                ],
                start=batch_start + 1,
            )
        ]
        for business_index, _, name_elem, _ in batch:
          if progress_callback:
            progress_callback({
                "stage": "processing_businesses",
                "message": f"Fetching {name_elem.get_text(strip=True)}",
                "current": business_index,
                "total": len(business_cards),
                "businesses_processed": processed_count,
                "businesses_added": created_count,
                "products_processed": processed_product_count,
                "products_added": created_product_count,
            })

        profile_html = executor.map(
            self._fetch_profile_html,
            [profile_url for _, _, _, profile_url in batch],
            [headers] * len(batch),
        )
        for (business_index, card, name_elem, profile_url), html in zip(
            batch, profile_html
        ):
          business_name = name_elem.get_text(strip=True)
          business_created, products_processed, products_created = (
              self._save_business_profile(
                  card,
                  business_name,
                  profile_url,
                  html,
              )
          )
          processed_count += 1
          created_count += int(business_created)
          processed_product_count += products_processed
          created_product_count += products_created
          if progress_callback:
            progress_callback({
                "stage": "processing_businesses",
                "message": f"Processed {business_name}",
                "current": business_index,
                "total": len(business_cards),
                "businesses_processed": processed_count,
                "businesses_added": created_count,
                "products_processed": processed_product_count,
                "products_added": created_product_count,
            })

    return (
        processed_count,
        created_count,
        processed_product_count,
        created_product_count,
    )

  def _fetch_profile_html(self, profile_url, headers):
    profile_response = requests.get(
        profile_url,
        headers=headers,
        timeout=self.REQUEST_TIMEOUT_SECONDS,
    )
    profile_response.raise_for_status()
    return profile_response.text

  def _save_business_profile(
      self,
      card,
      business_name,
      profile_url,
      profile_html,
  ):
    location_icon = card.select_one("svg.lucide-map-pin")
    location_elem = (
        location_icon.find_parent("div").select_one("span")
        if location_icon and location_icon.find_parent("div")
        else None
    )
    profile_soup = BeautifulSoup(profile_html, "html.parser")
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
    location = (
        location_elem.get_text(strip=True)
        if location_elem
        else "Lilongwe"
    )

    _, business_created = MthandiziBusinessLead.objects.update_or_create(
        profile_url=profile_url,
        defaults={
            "business_name": business_name,
            "phone_number": phone_number,
            "email": email,
            "location": location,
        },
    )
    products_processed = 0
    products_created = 0
    for product in self._parse_featured_products(profile_soup, profile_url):
      _, product_created = ScrapedLead.objects.update_or_create(
          listing_url=product["listing_url"],
          defaults={
              "source_platform": "Mthandizi",
              "vendor_name": business_name,
              "phone_number": phone_number,
              "listing_title": product["listing_title"],
              "item_price": product["item_price"],
              "location_district": location,
              "category": product["category"],
          },
      )
      products_processed += 1
      if product_created:
        products_created += 1
    return business_created, products_processed, products_created

  @staticmethod
  def _parse_featured_products(profile_soup, profile_url):
    heading = next(
        (
            element
            for element in profile_soup.select("h2")
            if (
                element.get_text(" ", strip=True).casefold()
                == "featured products"
            )
        ),
        None,
    )
    section = heading.find_parent("section") if heading else None
    if section is None:
      return []

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
      price_match = re.search(r"MWK\s*([\d,]+(?:\.\d{1,2})?)", price, re.I)
      item_price = (
          Decimal(price_match.group(1).replace(",", ""))
          if price_match
          else None
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
          {
              "listing_url": urljoin(profile_url, product_card["href"]),
              "listing_title": title.get_text(" ", strip=True),
              "item_price": item_price,
              "category": category,
          }
      )

    return products
