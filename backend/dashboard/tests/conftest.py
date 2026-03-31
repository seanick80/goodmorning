"""App-level fixtures and factories for dashboard tests."""

from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from dashboard.models import (
    CalendarEvent,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class UserDashboardFactory(DjangoModelFactory):
    class Meta:
        model = UserDashboard

    user = factory.SubFactory(UserFactory)
    widget_layout = factory.LazyFunction(
        lambda: [
            {
                "widget": "weather",
                "enabled": True,
                "position": 0,
                "settings": {"latitude": 40.71, "longitude": -74.01},
            },
            {
                "widget": "clock",
                "enabled": True,
                "position": 1,
                "settings": {"timezone": "America/New_York"},
            },
        ]
    )


class WeatherCacheFactory(DjangoModelFactory):
    class Meta:
        model = WeatherCache

    location_key = factory.Sequence(lambda n: f"40.{n:02d},-74.01")
    latitude = 40.71
    longitude = -74.01
    temperature = 72.5
    temperature_unit = "fahrenheit"
    feels_like = 70.0
    humidity = 55
    wind_speed = 8.5
    wind_direction = 180
    weather_code = 0
    precipitation_probability = 10
    sunrise = factory.LazyFunction(lambda: time(6, 30))
    sunset = factory.LazyFunction(lambda: time(19, 45))
    daily_high = 78.0
    daily_low = 62.0
    hourly_forecast = factory.LazyFunction(
        lambda: [
            {"time": "2026-03-17T08:00", "temp": 65.0, "weather_code": 0, "precip_prob": 5},
            {"time": "2026-03-17T09:00", "temp": 68.0, "weather_code": 1, "precip_prob": 10},
        ]
    )


class StockQuoteFactory(DjangoModelFactory):
    class Meta:
        model = StockQuote

    symbol = factory.Sequence(lambda n: f"TST{n}")
    company_name = factory.LazyAttribute(lambda obj: f"Test Corp {obj.symbol}")
    current_price = Decimal("150.2500")
    change = Decimal("2.5000")
    change_percent = Decimal("1.6900")
    day_high = Decimal("152.0000")
    day_low = Decimal("148.0000")
    open_price = Decimal("149.0000")
    previous_close = Decimal("147.7500")
    timestamp = factory.LazyFunction(lambda: datetime(2026, 3, 17, 16, 0, tzinfo=timezone.utc))


class CalendarEventFactory(DjangoModelFactory):
    class Meta:
        model = CalendarEvent

    source_url = "google:1"
    uid = factory.Sequence(lambda n: f"event-{n}@example.com")
    title = factory.Sequence(lambda n: f"Meeting {n}")
    description = ""
    location = "Conference Room A"
    start = factory.LazyFunction(lambda: datetime(2026, 3, 17, 10, 0, tzinfo=timezone.utc))
    end = factory.LazyFunction(lambda: datetime(2026, 3, 17, 11, 0, tzinfo=timezone.utc))
    all_day = False


class NewsHeadlineFactory(DjangoModelFactory):
    class Meta:
        model = NewsHeadline

    source_url = "https://feeds.example.com/rss"
    source_name = "Example News"
    guid = factory.Sequence(lambda n: f"headline-{n}")
    title = factory.Sequence(lambda n: f"Breaking News Story {n}")
    link = factory.LazyAttribute(lambda obj: f"https://example.com/news/{obj.guid}")
    summary = "A brief summary of the news story."
    published_at = factory.LazyFunction(
        lambda: datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc)
    )


