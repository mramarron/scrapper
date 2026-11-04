import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

import requests
from django.core.management import call_command
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    transaction,
)
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MthandiziBusinessLead, MthandiziScrapeRun, ScrapedLead
from .services import MthandiziDirectoryEmptyError
from .serializers import (
    MthandiziBusinessLeadSerializer,
    ScrapedLeadSerializer,
)

logger = logging.getLogger(__name__)
scrape_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="mthandizi-scraper",
)


def marketplace_list(request):
  listings = ScrapedLead.objects.order_by("-scraped_at")[:50]
  businesses = MthandiziBusinessLead.objects.order_by("-scraped_at")[:50]
  return render(
      request,
      "app_scrap/marketplace_list.html",
      {"listings": listings, "businesses": businesses},
  )


class MthandiziBusinessLeadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MthandiziBusinessLead.objects.order_by("-scraped_at")[:50]
    serializer_class = MthandiziBusinessLeadSerializer


class ScrapedLeadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScrapedLead.objects.order_by("-scraped_at")[:50]
    serializer_class = ScrapedLeadSerializer


def _serialize_scrape_run(run):
  return {
      "id": str(run.id),
      "status": run.status,
      "progress": run.progress,
      "error_code": run.error_code,
      "output": run.output,
      "error": run.error,
      "created_at": run.created_at,
      "started_at": run.started_at,
      "completed_at": run.completed_at,
  }


def _execute_mthandizi_scrape(run_id):
  close_old_connections()
  run = MthandiziScrapeRun.objects.get(pk=run_id)
  output = StringIO()
  try:
    run.status = MthandiziScrapeRun.Status.RUNNING
    run.started_at = timezone.now()
    run.progress = {
        "stage": "starting",
        "message": "Starting scraper services",
    }
    run.save(update_fields=("status", "started_at", "progress"))

    call_command(
        "scrape_mthandizi",
        stdout=output,
        stderr=output,
        run_id=str(run.id),
    )
    run.refresh_from_db(fields=("progress",))
    run.progress = {
        **run.progress,
        "stage": "completed",
        "message": "Scrape completed",
    }
    run.status = MthandiziScrapeRun.Status.COMPLETED
    run.error = ""
    run.error_code = ""
  except Exception as error:
    logger.exception("Mthandizi scraper run %s failed.", run_id)
    run.refresh_from_db(fields=("progress",))
    run.status = MthandiziScrapeRun.Status.FAILED
    run.error_code, run.error = _describe_scrape_error(error)
  finally:
    run.output = output.getvalue()[-4000:]
    run.completed_at = timezone.now()
    run.is_active = False
    run.save(
        update_fields=(
            "status",
            "error",
            "error_code",
            "progress",
            "output",
            "completed_at",
            "is_active",
        )
    )
    close_old_connections()


def _describe_scrape_error(error):
  if isinstance(error, requests.Timeout):
    return (
        MthandiziScrapeRun.ErrorCode.UPSTREAM_TIMEOUT,
        "Mthandizi took too long to respond. Please try again shortly.",
    )
  if isinstance(error, requests.ConnectionError):
    return (
        MthandiziScrapeRun.ErrorCode.UPSTREAM_UNREACHABLE,
        "Could not connect to Mthandizi. Check the connection and try again.",
    )
  if isinstance(error, requests.HTTPError):
    response = error.response
    status_code = response.status_code if response is not None else None
    if status_code == 408:
      return (
          MthandiziScrapeRun.ErrorCode.UPSTREAM_TIMEOUT,
          "Mthandizi took too long to respond. Please try again shortly.",
      )
    if status_code == 429:
      return (
          MthandiziScrapeRun.ErrorCode.UPSTREAM_RATE_LIMITED,
          "Mthandizi is receiving too many requests. Please try again later.",
      )
    if status_code in (401, 403):
      return (
          MthandiziScrapeRun.ErrorCode.UPSTREAM_ACCESS_DENIED,
          "Mthandizi temporarily refused access. Please try again later.",
      )
    if status_code is not None and status_code >= 500:
      return (
          MthandiziScrapeRun.ErrorCode.UPSTREAM_SERVER_ERROR,
          "Mthandizi is experiencing a problem. Please try again later.",
      )
    return (
        MthandiziScrapeRun.ErrorCode.UPSTREAM_REQUEST_FAILED,
        "Mthandizi could not provide the requested page. Please try again.",
    )
  if isinstance(error, MthandiziDirectoryEmptyError):
    return (
        MthandiziScrapeRun.ErrorCode.DIRECTORY_EMPTY,
        "No business profiles were found in the Mthandizi directory.",
    )
  if isinstance(error, DatabaseError):
    return (
        MthandiziScrapeRun.ErrorCode.STORAGE_ERROR,
        "The scraper could not save its results. Please try again.",
    )
  return (
      MthandiziScrapeRun.ErrorCode.UNEXPECTED_ERROR,
      "An unexpected error interrupted the scrape. Please try again later.",
  )


@api_view(["GET", "POST"])
def mthandizi_scrape(request):
  if request.method == "GET":
    run = MthandiziScrapeRun.objects.first()
    return Response({"run": _serialize_scrape_run(run) if run else None})

  try:
    with transaction.atomic():
      run = MthandiziScrapeRun.objects.create(id=uuid.uuid4())
  except IntegrityError:
    run = MthandiziScrapeRun.objects.filter(is_active=True).first()
    if run is None:
      raise
    return Response(_serialize_scrape_run(run), status=status.HTTP_202_ACCEPTED)

  try:
    scrape_executor.submit(_execute_mthandizi_scrape, run.id)
  except RuntimeError:
    logger.exception("Could not start Mthandizi scraper run %s.", run.id)
    run.status = MthandiziScrapeRun.Status.FAILED
    run.error_code = MthandiziScrapeRun.ErrorCode.WORKER_UNAVAILABLE
    run.error = "The scraper could not be started. Try again."
    run.completed_at = timezone.now()
    run.is_active = False
    run.save(
        update_fields=(
            "status",
            "error",
            "error_code",
            "completed_at",
            "is_active",
        )
    )
    return Response(
        _serialize_scrape_run(run),
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )

  return Response(_serialize_scrape_run(run), status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
def mthandizi_scrape_run(request, run_id):
  run = get_object_or_404(MthandiziScrapeRun, pk=run_id)
  return Response(_serialize_scrape_run(run))