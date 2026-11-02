from rest_framework import serializers
from app_scrap.models import MthandiziBusinessLead


class MthandiziBusinessLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MthandiziBusinessLead
        fields = (
            "id",
            "business_name",
            "category",
            "location",
            "phone_number",
            "email",
            "profile_url",
            "scraped_at",
        )