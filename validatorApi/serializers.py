from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class NationalIDSerializer(serializers.Serializer):

    national_id = serializers.CharField(
        max_length=14,
        min_length=14,
        required=True,
        help_text=_("14-digit Egyptian National ID number"),
    )

    def validate_national_id(self, value):
        value = str(value).strip()
        if not value.isdigit():
            raise serializers.ValidationError(_("National ID must contain only digits"))
        return value


class GovernorateSerializer(serializers.Serializer):

    code = serializers.CharField()
    name_english = serializers.CharField()
    name_arabic = serializers.CharField()


class GenerationSerializer(serializers.Serializer):

    name = serializers.CharField()
    year_range = serializers.CharField()


class NationalIDResponseSerializer(serializers.Serializer):

    national_id = serializers.CharField()
    is_valid = serializers.BooleanField()
    birth_date = serializers.DateField(required=False)
    birth_year = serializers.IntegerField(required=False)
    birth_month = serializers.IntegerField(required=False)
    birth_day = serializers.IntegerField(required=False)
    age = serializers.IntegerField(required=False)
    century = serializers.CharField(required=False)
    governorate = GovernorateSerializer(required=False)
    gender = serializers.CharField(required=False)
    generation = GenerationSerializer(required=False)
    serial_number = serializers.CharField(required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
