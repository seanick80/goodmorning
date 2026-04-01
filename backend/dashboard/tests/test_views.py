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

    def test_patch_accepts_panel_field(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        layout = [
            {"widget": "clock", "enabled": True, "position": 0, "panel": "left", "settings": {}},
            {"widget": "weather", "enabled": True, "position": 1, "panel": "left", "settings": {}},
            {"widget": "stocks", "enabled": True, "position": 0, "panel": "right", "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": layout},
            format="json",
        )
        assert response.status_code == 200
        saved = response.json()["widget_layout"]
        assert saved[0]["panel"] == "left"
        assert saved[2]["panel"] == "right"

    def test_patch_rejects_invalid_panel(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        layout = [
            {"widget": "clock", "enabled": True, "position": 0, "panel": "center", "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": layout},
            format="json",
        )
        assert response.status_code == 400

    def test_patch_accepts_layout_without_panel(self, api_client, superuser):
        """Widgets without panel field should still be accepted (backwards compat)."""
        UserDashboardFactory(user=superuser)
        layout = [
            {"widget": "clock", "enabled": True, "position": 0, "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": layout},
            format="json",
        )
        assert response.status_code == 200

    def test_patch_rejects_unknown_widget_type(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        layout = [
            {"widget": "unknown", "enabled": True, "position": 0, "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": layout},
            format="json",
        )
        assert response.status_code == 400

    def test_patch_full_layout_with_disabled_widgets(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        layout = [
            {"widget": "clock", "enabled": True, "position": 0, "panel": "left", "settings": {}},
            {"widget": "weather", "enabled": False, "position": 1, "panel": "left", "settings": {}},
            {"widget": "stocks", "enabled": True, "position": 0, "panel": "right", "settings": {}},
            {"widget": "glucose", "enabled": False, "position": 1, "panel": "right", "settings": {}},
        ]
        response = api_client.patch(
            "/api/dashboard/",
            data={"widget_layout": layout},
            format="json",
        )
        assert response.status_code == 200
        saved = response.json()["widget_layout"]
        assert len(saved) == 4
        assert saved[1]["enabled"] is False
        assert saved[3]["enabled"] is False


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

        today = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        # Events in the future today so they count as "remaining"
        CalendarEventFactory(
            title="Morning Standup",
            start=today.replace(hour=23),
            end=today.replace(hour=23, minute=30),
        )
        CalendarEventFactory(
            title="Afternoon Sync",
            start=today.replace(hour=23, minute=30),
            end=today.replace(hour=23, minute=59),
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


@pytest.mark.django_db()
class TestCORSConfiguration:
    """Verify CORS allows Pi kiosk origin alongside dev server."""

    def test_cors_allows_pi_kiosk_origin(self, api_client):
        response = api_client.get(
            "/api/weather/",
            HTTP_ORIGIN="http://goodmorning.local",
        )
        assert response.get("Access-Control-Allow-Origin") == "http://goodmorning.local"

    def test_cors_allows_dev_origin(self, api_client):
        response = api_client.get(
            "/api/weather/",
            HTTP_ORIGIN="http://localhost:5173",
        )
        assert response.get("Access-Control-Allow-Origin") == "http://localhost:5173"

    def test_cors_rejects_unknown_origin(self, api_client):
        response = api_client.get(
            "/api/weather/",
            HTTP_ORIGIN="http://evil.example.com",
        )
        assert response.get("Access-Control-Allow-Origin") is None


@pytest.mark.django_db()
class TestAuthStatusView:
    """Tests for GET /api/auth/status/."""

    def test_unauthenticated_returns_false(self, api_client):
        response = api_client.get("/api/auth/status/")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}

    def test_authenticated_without_google(self, api_client):
        user = UserFactory(username="testuser", email="test@example.com")
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/auth/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["email"] == "test@example.com"
        assert data["google_connected"] is False

    def test_authenticated_with_google(self, api_client):
        from allauth.socialaccount.models import SocialAccount

        user = UserFactory(username="googleuser", email="g@gmail.com")
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="123456",
            extra_data={
                "email": "g@gmail.com",
            },
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/auth/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["google_connected"] is True
        assert data["google_email"] == "g@gmail.com"


@pytest.mark.django_db()
class TestGoogleCalendarListView:
    """Tests for GET /api/auth/google/calendars/."""

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/auth/google/calendars/")
        assert response.status_code == 401

    def test_no_google_account_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/auth/google/calendars/")
        assert response.status_code == 400


@pytest.mark.django_db()
class TestPhotosPickerCreateView:
    """Tests for POST /api/auth/google/photos/picker/."""

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post("/api/auth/google/photos/picker/")
        assert response.status_code == 401

    def test_no_google_account_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        response = api_client.post("/api/auth/google/photos/picker/")
        assert response.status_code == 400
