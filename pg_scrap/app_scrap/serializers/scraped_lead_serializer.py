from rest_framework import serializers

from app_scrap.models import ScrapedLead


class ScrapedLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedLead
        fields = (
            "id",
            "source_platform",
            "vendor_name",
            "phone_number",
            "listing_title",
            "item_price",
            "location_district",
            "category",
            "listing_url",
            "scraped_at",
        )
