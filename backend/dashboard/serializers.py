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


ALLOWED_WIDGETS = {"clock", "weather", "stocks", "calendar", "news", "photos", "glucose"}
ALLOWED_PANELS = {"left", "right"}


class UserDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDashboard
        fields = ["widget_layout"]

    def validate_widget_layout(self, value: object) -> list:
        if not isinstance(value, list):
            raise serializers.ValidationError("widget_layout must be a list.")
        for i, widget in enumerate(value):
            if not isinstance(widget, dict):
                raise serializers.ValidationError(f"Item {i} must be an object.")
            widget_type = widget.get("widget")
            if widget_type not in ALLOWED_WIDGETS:
                raise serializers.ValidationError(
                    f"Item {i}: unknown widget type '{widget_type}'."
                )
            if not isinstance(widget.get("enabled", True), bool):
                raise serializers.ValidationError(
                    f"Item {i}: 'enabled' must be a boolean."
                )
            if not isinstance(widget.get("settings", {}), dict):
                raise serializers.ValidationError(
                    f"Item {i}: 'settings' must be an object."
                )
            panel = widget.get("panel")
            if panel is not None and panel not in ALLOWED_PANELS:
                raise serializers.ValidationError(
                    f"Item {i}: 'panel' must be 'left' or 'right'."
                )
        return value


class WeatherLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    location_name = serializers.CharField(
        max_length=500, required=False, default="",
    )
