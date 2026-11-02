from django.shortcuts import render
from .models import MthandiziBusinessLead, ScrapedLead
from rest_framework import viewsets
from .serializers import (
    MthandiziBusinessLeadSerializer,
    ScrapedLeadSerializer,
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