from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from app_scrap.views import (
    MthandiziBusinessLeadViewSet,
    ScrapedLeadViewSet,
    mthandizi_scrape,
    mthandizi_scrape_run,
    marketplace_list,
)

router = DefaultRouter()
router.register(
    "marketplace-listings",
    ScrapedLeadViewSet,
    basename="marketplace-listing",
)
router.register(
    "businesses",
    MthandiziBusinessLeadViewSet,
    basename="business",
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/scrape-mthandizi/", mthandizi_scrape, name="mthandizi-scrape"),
    path(
        "api/scrape-mthandizi/<uuid:run_id>/",
        mthandizi_scrape_run,
        name="mthandizi-scrape-run",
    ),
    path("api/", include(router.urls)),
    path('', marketplace_list, name='marketplace_list'),
]
