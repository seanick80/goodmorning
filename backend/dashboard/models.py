"""Dashboard models for weather, stocks, calendar, news, and user configuration."""

from django.conf import settings
from django.db import models


class UserDashboard(models.Model):
    """Per-user dashboard configuration. One-to-one with User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard",
    )
    widget_layout = models.JSONField(
        default=list,
        help_text="Ordered list of widget configs: [{widget, enabled, position, settings}, ...]",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Dashboard"
        verbose_name_plural = "User Dashboards"

    def __str__(self):
        return f"Dashboard for {self.user.username}"


class WeatherCache(models.Model):
    """Cached weather data from Open-Meteo. One row per location."""

    location_key = models.CharField(
        max_length=50,
        unique=True,
        help_text="'lat,lon' string, e.g. '40.71,-74.01'",
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature = models.FloatField(help_text="Current temperature")
    temperature_unit = models.CharField(max_length=10, default="fahrenheit")
    feels_like = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True, help_text="Relative humidity %")
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.IntegerField(null=True, blank=True, help_text="Degrees")
    weather_code = models.IntegerField(
        help_text="WMO weather interpretation code (0=clear, 1-3=cloudy, etc.)"
    )
    precipitation_probability = models.IntegerField(null=True, blank=True)
    sunrise = models.TimeField(null=True, blank=True)
    sunset = models.TimeField(null=True, blank=True)
    hourly_forecast = models.JSONField(
        default=list,
        help_text="List of hourly data: [{time, temp, weather_code, precip_prob}, ...]",
    )
    daily_high = models.FloatField(null=True, blank=True)
    daily_low = models.FloatField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Weather Cache"
        verbose_name_plural = "Weather Cache"

    def __str__(self):
        return f"Weather at {self.location_key} ({self.temperature})"


class StockQuote(models.Model):
    """Cached stock quote from Finnhub. One row per symbol."""

    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200, blank=True, default="")
    current_price = models.DecimalField(max_digits=12, decimal_places=4)
    change = models.DecimalField(max_digits=12, decimal_places=4, help_text="Price change")
    change_percent = models.DecimalField(
        max_digits=8, decimal_places=4, help_text="Change %"
    )
    day_high = models.DecimalField(max_digits=12, decimal_places=4)
    day_low = models.DecimalField(max_digits=12, decimal_places=4)
    open_price = models.DecimalField(max_digits=12, decimal_places=4)
    previous_close = models.DecimalField(max_digits=12, decimal_places=4)
    timestamp = models.DateTimeField(help_text="Quote timestamp from Finnhub")
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock Quote"
        verbose_name_plural = "Stock Quotes"
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol}: ${self.current_price}"


class CalendarEvent(models.Model):
    """Cached calendar event from Google Calendar API."""

    source_url = models.URLField(help_text="Event source identifier (e.g. 'google:1')")
    uid = models.CharField(max_length=255, help_text="Event UID for deduplication")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=500, blank=True, default="")
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Calendar Event"
        verbose_name_plural = "Calendar Events"
        ordering = ["start"]
        unique_together = [("source_url", "uid")]

    def __str__(self):
        return f"{self.title} ({self.start})"


class NewsHeadline(models.Model):
    """Cached news headline from RSS feed."""

    source_url = models.URLField(help_text="RSS feed URL this headline came from")
    source_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Display name for the source (e.g., 'BBC News')",
    )
    guid = models.CharField(
        max_length=500,
        help_text="RSS item guid/id for deduplication",
    )
    title = models.CharField(max_length=1000)
    link = models.URLField(max_length=2000, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication timestamp from the RSS feed",
    )
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "News Headline"
        verbose_name_plural = "News Headlines"
        ordering = ["-published_at"]
        unique_together = [("source_url", "guid")]

    def __str__(self):
        return f"{self.source_name}: {self.title[:80]}"


class GlucoseReading(models.Model):
    """Cached glucose reading from Dexcom CGM."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="glucose_readings",
    )
    value = models.IntegerField(help_text="Blood glucose in mg/dL")
    mmol_l = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Blood glucose in mmol/L",
    )
    trend_direction = models.CharField(
        max_length=30,
        help_text="e.g. Flat, FortyFiveUp, SingleUp",
    )
    trend_arrow = models.CharField(
        max_length=5,
        help_text="Unicode trend arrow",
    )
    recorded_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Glucose Reading"
        verbose_name_plural = "Glucose Readings"
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["user", "-recorded_at"])]

    def __str__(self) -> str:
        return f"{self.value} mg/dL {self.trend_arrow} ({self.recorded_at})"
