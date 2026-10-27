# scrapers/models.py
from django.db import models


class ScrapedLead(models.Model):
  source_platform = models.CharField(
      max_length=100, default="Tisitano Malawi"
  )
  vendor_name = models.CharField(max_length=255)
  phone_number = models.CharField(max_length=50, blank=True, null=True)
  listing_title = models.CharField(max_length=255)
  item_price = models.DecimalField(
      max_digits=15, decimal_places=2, blank=True, null=True
  )
  location_district = models.CharField(
      max_length=100, blank=True, null=True
  )  # e.g., Lilongwe, Blantyre
  category = models.CharField(max_length=100, blank=True, null=True)
  listing_url = models.URLField(unique=True)

  # Pipeline Matching Fields
  is_matched = models.BooleanField(default=False)
  matched_tin = models.CharField(max_length=50, blank=True, null=True)
  match_confidence_score = models.FloatField(default=0.0)

  scraped_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.vendor_name} - {self.listing_title} ({self.location_district})"


class MthandiziBusinessLead(models.Model):
  business_name = models.CharField(max_length=255)
  category = models.CharField(max_length=100, blank=True, null=True)
  location = models.CharField(max_length=100, blank=True, null=True)
  phone_number = models.CharField(
      max_length=50, blank=True
  )  # Direct phone number exposed here
  email = models.EmailField(blank=True)
  profile_url = models.URLField(unique=True)

  # Tracking pipeline status
  is_checked = models.BooleanField(default=False)
  matched_tin = models.CharField(max_length=50, blank=True, null=True)

  scraped_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.business_name} - {self.phone_number}"