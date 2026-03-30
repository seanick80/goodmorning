"""Extended tests for dashboard services (geocode, google_api)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import requests
import requests_mock as rm

from dashboard.services.geocode import GEOCODING_URL, search_locations


class TestSearchLocations:
    def test_returns_formatted_results(self, requests_mock):
        requests_mock.get(
            GEOCODING_URL,
            json={
                "results": [
                    {
                        "name": "Hobart",
                        "admin1": "Tasmania",
                        "country": "Australia",
                        "latitude": -42.88,
                        "longitude": 147.33,
                    },
                ],
            },
        )
        results = search_locations("Hobart")
        assert len(results) == 1
        assert results[0]["name"] == "Hobart"
        assert results[0]["latitude"] == -42.88
        assert results[0]["longitude"] == 147.33
        assert results[0]["country"] == "Australia"
        assert results[0]["admin1"] == "Tasmania"

    def test_returns_empty_for_short_query(self):
        results = search_locations("a")
        assert results == []

    def test_returns_empty_for_empty_query(self):
        results = search_locations("")
        assert results == []

    def test_handles_api_error(self, requests_mock):
        requests_mock.get(GEOCODING_URL, status_code=500)
        results = search_locations("Hobart")
        assert results == []

    def test_handles_timeout(self, requests_mock):
        requests_mock.get(GEOCODING_URL, exc=requests.exceptions.ConnectTimeout)
        results = search_locations("Hobart")
        assert results == []

    def test_formats_display_name(self, requests_mock):
        requests_mock.get(
            GEOCODING_URL,
            json={
                "results": [
                    {
                        "name": "Portland",
                        "admin1": "Oregon",
                        "country": "United States",
                        "latitude": 45.52,
                        "longitude": -122.68,
                    },
                ],
            },
        )
        results = search_locations("Portland")
        assert results[0]["display_name"] == "Portland, Oregon, United States"

    def test_formats_display_name_without_admin1(self, requests_mock):
        requests_mock.get(
            GEOCODING_URL,
            json={
                "results": [
                    {
                        "name": "Singapore",
                        "country": "Singapore",
                        "latitude": 1.29,
                        "longitude": 103.85,
                    },
                ],
            },
        )
        results = search_locations("Singapore")
        assert results[0]["display_name"] == "Singapore, Singapore"


class TestGetGoogleCredentials:
    def test_no_account_returns_none(self):
        from dashboard.services.google_api import get_google_credentials

        user = _create_user()
        result = get_google_credentials(user)
        assert result is None

    def test_no_token_returns_none(self):
        from allauth.socialaccount.models import SocialAccount

        from dashboard.services.google_api import get_google_credentials

        user = _create_user()
        SocialAccount.objects.create(
            user=user, provider="google", uid="g-123", extra_data={},
        )
        result = get_google_credentials(user)
        assert result is None

    @pytest.mark.django_db()
    def test_builds_credentials(self, settings):
        from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
        from django.contrib.sites.models import Site

        from dashboard.services.google_api import get_google_credentials

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        user = _create_user()
        app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="test-client-id",
            secret="test-client-secret",
        )
        site = Site.objects.get(id=1)
        app.sites.add(site)

        account = SocialAccount.objects.create(
            user=user, provider="google", uid="g-456", extra_data={},
        )
        SocialToken.objects.create(
            account=account,
            app=app,
            token="access-token-xyz",
            token_secret="refresh-token-xyz",
        )

        credentials = get_google_credentials(user)

        assert credentials is not None
        assert credentials.token == "access-token-xyz"
        assert credentials.refresh_token == "refresh-token-xyz"


class TestParseGcalDatetime:
    def test_timed_event(self):
        from dashboard.services.google_api import _parse_gcal_datetime

        result = _parse_gcal_datetime("2026-03-30T10:00:00-04:00", all_day=False)
        assert isinstance(result, datetime)
        assert result.hour == 10
        assert result.year == 2026

    def test_all_day_event(self):
        from dashboard.services.google_api import _parse_gcal_datetime

        result = _parse_gcal_datetime("2026-03-30", all_day=True)
        assert isinstance(result, datetime)
        assert result.hour == 0
        assert result.minute == 0
        assert result.tzinfo == timezone.utc
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 30


def _create_user():
    """Create a plain Django user for service-level tests."""
    from django.contrib.auth.models import User

    return User.objects.create_user(
        username=f"svcuser{User.objects.count()}",
        password="testpass123",
    )
