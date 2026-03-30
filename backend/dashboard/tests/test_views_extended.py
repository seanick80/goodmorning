"""Extended tests for dashboard API views (Geocode, WeatherLocation, Photos, CSRF)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from .conftest import (
    UserDashboardFactory,
    UserFactory,
)


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture()
def superuser():
    return UserFactory(is_superuser=True, username="admin")


class TestGeocodeView:
    def test_returns_results_for_valid_query(self, api_client):
        mock_results = [
            {
                "name": "Hobart",
                "display_name": "Hobart, Tasmania, Australia",
                "latitude": -42.88,
                "longitude": 147.33,
                "country": "Australia",
                "admin1": "Tasmania",
            },
        ]
        with patch(
            "dashboard.services.geocode.search_locations",
            return_value=mock_results,
        ):
            response = api_client.get("/api/geocode/", {"q": "Hobart"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Hobart"
        assert data[0]["latitude"] == -42.88

    def test_returns_empty_for_short_query(self, api_client):
        response = api_client.get("/api/geocode/", {"q": "a"})
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_empty_for_missing_query(self, api_client):
        response = api_client.get("/api/geocode/")
        assert response.status_code == 200
        assert response.json() == []


class TestWeatherLocationView:
    def test_updates_location_and_fetches_weather(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        mock_weather = {
            "temperature": 65.0,
            "temperature_unit": "fahrenheit",
            "feels_like": 63.0,
            "humidity": 50,
            "wind_speed": 10.0,
            "wind_direction": 270,
            "weather_code": 1,
            "precipitation_probability": 20,
            "sunrise": "06:30",
            "sunset": "19:00",
            "daily_high": 70.0,
            "daily_low": 55.0,
            "hourly_forecast": [],
        }
        with patch(
            "dashboard.services.weather.fetch_weather_data",
            return_value=mock_weather,
        ):
            response = api_client.post(
                "/api/weather/location/",
                data={
                    "latitude": -42.88,
                    "longitude": 147.33,
                    "location_name": "Hobart",
                },
                format="json",
            )

        assert response.status_code == 200
        data = response.json()
        assert "location_key" in data
        assert data["location_key"] == "-42.88,147.33"

    def test_creates_weather_widget_when_none_exists(self, api_client, superuser):
        UserDashboardFactory(user=superuser, widget_layout=[])
        mock_weather = {
            "temperature": 65.0,
            "temperature_unit": "fahrenheit",
            "feels_like": 63.0,
            "humidity": 50,
            "wind_speed": 10.0,
            "wind_direction": 270,
            "weather_code": 1,
            "precipitation_probability": 20,
            "sunrise": "06:30",
            "sunset": "19:00",
            "daily_high": 70.0,
            "daily_low": 55.0,
            "hourly_forecast": [],
        }
        with patch(
            "dashboard.services.weather.fetch_weather_data",
            return_value=mock_weather,
        ):
            response = api_client.post(
                "/api/weather/location/",
                data={"latitude": 40.71, "longitude": -74.01, "location_name": "NYC"},
                format="json",
            )

        assert response.status_code == 200
        # Verify a weather widget was appended to the layout
        from dashboard.models import UserDashboard

        dashboard = UserDashboard.objects.get(user=superuser)
        weather_widgets = [
            w for w in dashboard.widget_layout if w["widget"] == "weather"
        ]
        assert len(weather_widgets) == 1
        assert weather_widgets[0]["settings"]["latitude"] == 40.71

    def test_returns_400_without_coordinates(self, api_client, superuser):
        response = api_client.post(
            "/api/weather/location/",
            data={"location_name": "Somewhere"},
            format="json",
        )
        assert response.status_code == 400
        assert "latitude" in response.json()["detail"]

    def test_returns_404_without_superuser(self, api_client):
        response = api_client.post(
            "/api/weather/location/",
            data={"latitude": 40.71, "longitude": -74.01},
            format="json",
        )
        assert response.status_code == 404

    def test_returns_202_when_fetch_fails(self, api_client, superuser):
        UserDashboardFactory(user=superuser)
        with patch(
            "dashboard.services.weather.fetch_weather_data",
            side_effect=Exception("API down"),
        ):
            response = api_client.post(
                "/api/weather/location/",
                data={"latitude": 40.71, "longitude": -74.01},
                format="json",
            )

        assert response.status_code == 202
        assert "failed" in response.json()["detail"].lower()


class TestPhotosPickerPollView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(
            "/api/auth/google/photos/picker/test-session-123/"
        )
        assert response.status_code == 401

    def test_no_google_account_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        with patch(
            "dashboard.services.google_api.poll_picker_session",
            return_value=None,
        ):
            response = api_client.get(
                "/api/auth/google/photos/picker/test-session-123/"
            )
        assert response.status_code == 400

    def test_returns_poll_result(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        with patch(
            "dashboard.services.google_api.poll_picker_session",
            return_value={"mediaItemsSet": True},
        ):
            response = api_client.get(
                "/api/auth/google/photos/picker/test-session-123/"
            )
        assert response.status_code == 200
        assert response.json()["media_items_set"] is True


class TestPhotosPickerMediaView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(
            "/api/auth/google/photos/picker/test-session-123/media/"
        )
        assert response.status_code == 401

    def test_returns_media_items(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        mock_items = [
            {"id": "1", "base_url": "https://lh3.google.com/1", "mime_type": "image/jpeg"},
            {"id": "2", "base_url": "https://lh3.google.com/2", "mime_type": "image/png"},
        ]
        with patch(
            "dashboard.services.google_api.fetch_picker_media_items",
            return_value=mock_items,
        ):
            response = api_client.get(
                "/api/auth/google/photos/picker/test-session-123/media/"
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "1"
        assert data[1]["mime_type"] == "image/png"


class TestCSRFCookie:
    def test_auth_status_sets_csrf_cookie(self, api_client):
        response = api_client.get("/api/auth/status/")
        assert response.status_code == 200
        assert "csrftoken" in response.cookies
