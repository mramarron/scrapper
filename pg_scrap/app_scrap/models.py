# scrapers/models.py
from django.db import models
from django.db.models import Q


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


class MthandiziScrapeRun(models.Model):
  class Status(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"

  class ErrorCode(models.TextChoices):
    UPSTREAM_TIMEOUT = "upstream_timeout", "Upstream timeout"
    UPSTREAM_UNREACHABLE = "upstream_unreachable", "Upstream unreachable"
    UPSTREAM_RATE_LIMITED = "upstream_rate_limited", "Upstream rate limited"
    UPSTREAM_ACCESS_DENIED = "upstream_access_denied", "Upstream access denied"
    UPSTREAM_SERVER_ERROR = "upstream_server_error", "Upstream server error"
    UPSTREAM_REQUEST_FAILED = "upstream_request_failed", "Upstream request failed"
    DIRECTORY_EMPTY = "directory_empty", "Directory empty"
    STORAGE_ERROR = "storage_error", "Storage error"
    WORKER_UNAVAILABLE = "worker_unavailable", "Worker unavailable"
    UNEXPECTED_ERROR = "unexpected_error", "Unexpected error"

  id = models.UUIDField(primary_key=True, editable=False)
  status = models.CharField(
      max_length=20,
      choices=Status.choices,
      default=Status.QUEUED,
  )
  is_active = models.BooleanField(default=True)
  progress = models.JSONField(default=dict, blank=True)
  error_code = models.CharField(max_length=40, blank=True)
  output = models.TextField(blank=True)
  error = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  started_at = models.DateTimeField(blank=True, null=True)
  completed_at = models.DateTimeField(blank=True, null=True)

  class Meta:
    ordering = ("-created_at",)
    constraints = [
        models.UniqueConstraint(
            fields=("is_active",),
            condition=Q(is_active=True),
            name="one_active_mthandizi_scrape",
        ),
    ]