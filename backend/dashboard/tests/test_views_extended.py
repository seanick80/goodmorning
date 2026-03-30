"""Extended tests for dashboard API views (Geocode, WeatherLocation, Photos, CSRF)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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


class TestPhotoProxyView:
    def _make_photos_dashboard(self, superuser, cached_media: list | None = None):
        """Create a dashboard with a photos widget containing cached_media."""
        media = cached_media or []
        return UserDashboardFactory(
            user=superuser,
            widget_layout=[
                {
                    "widget": "photos",
                    "enabled": True,
                    "position": 0,
                    "settings": {
                        "cached_media": media,
                        "picker_session_id": "session-abc",
                    },
                },
            ],
        )

    def _create_google_account(self, user):
        """Create a SocialApp, SocialAccount, and SocialToken for Google."""
        from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
        from django.contrib.sites.models import Site

        app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="test-client-id",
            secret="test-client-secret",
        )
        site = Site.objects.get(id=1)
        app.sites.add(site)

        account = SocialAccount.objects.create(
            user=user, provider="google", uid="g-proxy-test", extra_data={},
        )
        SocialToken.objects.create(
            account=account,
            app=app,
            token="access-token-xyz",
            token_secret="refresh-token-xyz",
        )
        return account

    def test_returns_404_when_no_dashboard(self, api_client):
        response = api_client.get("/api/photos/0/")
        assert response.status_code == 404

    def test_returns_404_for_invalid_index(self, api_client, superuser):
        self._make_photos_dashboard(superuser, cached_media=[
            {"base_url": "https://lh3.google.com/a"},
            {"base_url": "https://lh3.google.com/b"},
        ])
        response = api_client.get("/api/photos/5/")
        assert response.status_code == 404

    @patch("requests.get")
    @patch("dashboard.services.google_api.get_google_credentials")
    def test_returns_image_via_proxy(
        self, mock_get_creds, mock_requests_get, api_client, superuser,
    ):
        self._make_photos_dashboard(superuser, cached_media=[
            {"base_url": "https://lh3.google.com/photo1"},
        ])
        self._create_google_account(superuser)

        mock_creds = MagicMock()
        mock_creds.token = "fake-token"
        mock_creds.expired = False
        mock_get_creds.return_value = mock_creds

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake-image-data"
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_resp

        response = api_client.get("/api/photos/0/")

        assert response.status_code == 200
        assert response.content == b"fake-image-data"

    @patch("dashboard.services.google_api.get_google_credentials")
    def test_returns_400_when_no_google_account(
        self, mock_get_creds, api_client, superuser,
    ):
        self._make_photos_dashboard(superuser, cached_media=[
            {"base_url": "https://lh3.google.com/photo1"},
        ])
        # No SocialAccount created -- view checks for google account before credentials
        response = api_client.get("/api/photos/0/")
        assert response.status_code == 400


class TestCSRFCookie:
    def test_auth_status_sets_csrf_cookie(self, api_client):
        response = api_client.get("/api/auth/status/")
        assert response.status_code == 200
        assert "csrftoken" in response.cookies
