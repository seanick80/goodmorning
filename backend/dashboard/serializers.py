"""DRF serializers for dashboard models."""

from rest_framework import serializers

from .models import (
    CalendarEvent,
    GlucoseReading,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)


class WeatherCacheSerializer(serializers.ModelSerializer):
    weather_description = serializers.SerializerMethodField()

    class Meta:
        model = WeatherCache
        fields = [
            "location_key",
            "temperature",
            "temperature_unit",
            "feels_like",
            "humidity",
            "wind_speed",
            "weather_code",
            "weather_description",
            "precipitation_probability",
            "sunrise",
            "sunset",
            "daily_high",
            "daily_low",
            "hourly_forecast",
            "fetched_at",
        ]

    def get_weather_description(self, obj: WeatherCache) -> str:
        from .services.weather import WMO_CODES
        return WMO_CODES.get(obj.weather_code, "Unknown")


class StockQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockQuote
        fields = "__all__"


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = "__all__"


class NewsHeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsHeadline
        fields = "__all__"


class GlucoseReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlucoseReading
        fields = [
            "value",
            "mmol_l",
            "trend_direction",
            "trend_arrow",
            "recorded_at",
            "fetched_at",
        ]


class UserDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDashboard
        fields = ["widget_layout"]


