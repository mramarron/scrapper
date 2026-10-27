from django.shortcuts import render
from .models import MthandiziBusinessLead, ScrapedLead


def marketplace_list(request):
  listings = ScrapedLead.objects.order_by("-scraped_at")[:50]
  businesses = MthandiziBusinessLead.objects.order_by("-scraped_at")[:50]
  return render(
      request,
      "app_scrap/marketplace_list.html",
      {"listings": listings, "businesses": businesses},
  )
