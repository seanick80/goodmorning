"""Tests for dashboard API views."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from dashboard.models import UserDashboard

from .conftest import (
    CalendarEventFactory,
    NewsHeadlineFactory,
    StockQuoteFactory,
    UserDashboardFactory,
    UserFactory,
    WeatherCacheFactory,
)


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture()
def superuser() -> User:
    return UserFactory(is_superuser=True, username="admin")


class TestWeatherView:
    def test_returns_200_with_weather_data(self, api_client):
        WeatherCacheFactory(location_key="40.71,-74.01")
        response = api_client.get("/api/weather/")
        assert response.status_code == 200
        data = response.json()
        assert data["location_key"] == "40.71,-74.01"
        assert "temperature" in data
        assert "weather_description" in data

    def test_returns_weather_for_configured_location(self, api_client):
        """When a superuser has a weather widget configured, the view returns
        the cache entry matching that location and includes location_name."""
        user = UserFactory(is_superuser=True, username="admin")
        UserDashboardFactory(
            user=user,
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {
                        "latitude": -42.88,
                        "longitude": 147.33,
                        "location_name": "Hobart",
                    },
                },
            ],
        )
        # Cache entry that matches the dashboard config
        WeatherCacheFactory(location_key="-42.88,147.33", latitude=-42.88, longitude=147.33)
        # A different location that should NOT be returned
        WeatherCacheFactory(location_key="40.71,-74.01")

        response = api_client.get("/api/weather/")
        assert response.status_code == 200
        data = response.json()
        assert data["location_key"] == "-42.88,147.33"
        assert data["location_name"] == "Hobart"

    def test_returns_404_when_no_cache_exists(self, api_client):
        response = api_client.get("/api/weather/")
        assert response.status_code == 404
        assert "No weather data" in response.json()["detail"]


class TestDashboardView:
    def test_get_returns_user_dashboard_config(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        response = api_client.get("/api/dashboard/")
        assert response.status_code == 200
        data = response.json()
        assert "widget_layout" in data
        assert isinstance(data["widget_layout"], list)

    def test_get_creates_default_dashboard_on_first_access(self, api_client, superuser):
        assert not UserDashboard.objects.filter(user=superuser).exists()
        response = api_client.get("/api/dashboard/")
        assert response.status_code == 200
        assert UserDashboard.objects.filter(user=superuser).exists()
        assert response.json()["widget_layout"] == []

    def test_patch_updates_widget_layout(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        new_layout = [
            {"widget": "clock", "enabled": True, "position": 0, "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": new_layout},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["widget_layout"] == new_layout

    def test_get_returns_404_when_no_superuser(self, api_client):
        response = api_client.get("/api/dashboard/")
        assert response.status_code == 404
        assert "No dashboard configured" in response.json()["detail"]

    def test_patch_returns_404_when_no_superuser(self, api_client):
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": []},
            format="json",
        )
        assert response.status_code == 404


class TestStocksView:
    def test_returns_stock_quotes_ordered_by_symbol(self, api_client):
        StockQuoteFactory(symbol="MSFT")
        StockQuoteFactory(symbol="AAPL")
        StockQuoteFactory(symbol="GOOG")

        response = api_client.get("/api/stocks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        symbols = [q["symbol"] for q in data]
        assert symbols == ["AAPL", "GOOG", "MSFT"]

    def test_filters_by_configured_symbols(self, api_client):
        """When a superuser has a stocks widget with specific symbols,
        the view only returns quotes for those symbols."""
        user = UserFactory(is_superuser=True, username="admin")
        UserDashboardFactory(
            user=user,
            widget_layout=[
                {
                    "widget": "stocks",
                    "enabled": True,
                    "position": 0,
                    "settings": {"symbols": ["AAPL", "GOOG"]},
                },
            ],
        )
        StockQuoteFactory(symbol="AAPL")
        StockQuoteFactory(symbol="GOOG")
        StockQuoteFactory(symbol="MSFT")  # not in config — should be excluded

        response = api_client.get("/api/stocks/")
        assert response.status_code == 200
        data = response.json()
        symbols = [q["symbol"] for q in data]
        assert symbols == ["AAPL", "GOOG"]
        assert "MSFT" not in symbols

    def test_returns_empty_list_when_no_data(self, api_client):
        response = api_client.get("/api/stocks/")
        assert response.status_code == 200
        assert response.json() == []


class TestCalendarView:
    def test_returns_todays_events(self, api_client):
        from datetime import datetime, timedelta, timezone

        today = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        CalendarEventFactory(
            title="Morning Standup",
            start=today.replace(hour=9),
            end=today.replace(hour=9, minute=30),
        )
        CalendarEventFactory(
            title="Afternoon Sync",
            start=today.replace(hour=14),
            end=today.replace(hour=15),
        )
        # Event from yesterday -- should not appear
        yesterday = today - timedelta(days=1)
        CalendarEventFactory(
            title="Old Event",
            start=yesterday.replace(hour=10),
            end=yesterday.replace(hour=11),
        )

        response = api_client.get("/api/calendar/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = [e["title"] for e in data]
        assert "Morning Standup" in titles
        assert "Old Event" not in titles

    def test_returns_empty_list_when_no_events(self, api_client):
        response = api_client.get("/api/calendar/")
        assert response.status_code == 200
        assert response.json() == []


class TestNewsView:
    def test_returns_headlines_ordered_by_published_at_desc(self, api_client):
        from datetime import datetime, timezone

        NewsHeadlineFactory(
            title="Older Story",
            published_at=datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc),
        )
        NewsHeadlineFactory(
            title="Newer Story",
            published_at=datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
        )

        response = api_client.get("/api/news/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Newer Story"
        assert data[1]["title"] == "Older Story"

    def test_limits_to_20_results(self, api_client):
        from datetime import datetime, timedelta, timezone

        base_time = datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc)
        for i in range(25):
            NewsHeadlineFactory(
                published_at=base_time + timedelta(hours=i),
            )

        response = api_client.get("/api/news/")
        assert response.status_code == 200
        assert len(response.json()) == 20
