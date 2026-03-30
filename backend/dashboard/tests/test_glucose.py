"""Tests for glucose widget: model, view, job, and service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from dashboard.models import GlucoseReading, UserDashboard

from .conftest import UserDashboardFactory, UserFactory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture()
def superuser() -> User:
    return UserFactory(is_superuser=True, username="admin")


def _make_reading(
    user: User,
    *,
    value: int = 120,
    mmol_l: Decimal = Decimal("6.7"),
    trend_direction: str = "Flat",
    trend_arrow: str = "\u2192",
    recorded_at: datetime | None = None,
) -> GlucoseReading:
    if recorded_at is None:
        recorded_at = datetime.now(tz=timezone.utc)
    return GlucoseReading.objects.create(
        user=user,
        value=value,
        mmol_l=mmol_l,
        trend_direction=trend_direction,
        trend_arrow=trend_arrow,
        recorded_at=recorded_at,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestGlucoseReadingModel:
    def test_creation_with_valid_data(self, superuser):
        reading = _make_reading(superuser, value=105, trend_arrow="\u2197")
        assert reading.pk is not None
        assert reading.value == 105
        assert reading.trend_arrow == "\u2197"

    def test_str_representation(self, superuser):
        ts = datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)
        reading = _make_reading(superuser, value=98, trend_arrow="\u2192", recorded_at=ts)
        assert "98 mg/dL" in str(reading)
        assert "\u2192" in str(reading)

    def test_ordering_by_recorded_at_descending(self, superuser):
        now = datetime.now(tz=timezone.utc)
        old = _make_reading(superuser, recorded_at=now - timedelta(hours=2))
        mid = _make_reading(superuser, recorded_at=now - timedelta(hours=1))
        new = _make_reading(superuser, recorded_at=now)

        readings = list(GlucoseReading.objects.filter(user=superuser))
        assert readings == [new, mid, old]


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------


class TestGlucoseView:
    def test_returns_404_when_no_readings(self, api_client, superuser):
        response = api_client.get("/api/glucose/")
        assert response.status_code == 404
        assert "No glucose data" in response.json()["detail"]

    def test_returns_current_and_history(self, api_client, superuser):
        now = datetime.now(tz=timezone.utc)
        _make_reading(superuser, value=110, recorded_at=now - timedelta(hours=1))
        _make_reading(superuser, value=120, recorded_at=now)

        response = api_client.get("/api/glucose/")
        assert response.status_code == 200
        data = response.json()
        assert "current" in data
        assert "history" in data
        assert data["current"]["value"] == 120
        assert len(data["history"]) == 2

    def test_history_limited_to_3_hours(self, api_client, superuser):
        now = datetime.now(tz=timezone.utc)
        _make_reading(superuser, value=100, recorded_at=now - timedelta(hours=4))
        _make_reading(superuser, value=110, recorded_at=now - timedelta(hours=2))
        _make_reading(superuser, value=120, recorded_at=now)

        response = api_client.get("/api/glucose/")
        assert response.status_code == 200
        data = response.json()
        # The 4-hour-old reading should be excluded from history
        assert len(data["history"]) == 2
        values = [r["value"] for r in data["history"]]
        assert 100 not in values

    def test_response_format(self, api_client, superuser):
        now = datetime.now(tz=timezone.utc)
        _make_reading(superuser, value=115, recorded_at=now)

        response = api_client.get("/api/glucose/")
        data = response.json()
        current = data["current"]
        assert "value" in current
        assert "mmol_l" in current
        assert "trend_direction" in current
        assert "trend_arrow" in current
        assert "recorded_at" in current


# ---------------------------------------------------------------------------
# Job tests
# ---------------------------------------------------------------------------


class TestFetchGlucoseJob:
    def _make_glucose_dashboard(
        self,
        *,
        username: str = "dexuser",
        password: str = "dexpass",
        region: str = "us",
        enabled: bool = True,
    ) -> UserDashboard:
        return UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "glucose",
                    "enabled": enabled,
                    "position": 0,
                    "settings": {
                        "dexcom_username": username,
                        "dexcom_password": password,
                        "dexcom_region": region,
                    },
                },
            ]
        )

    def test_skips_dashboards_with_no_glucose_widget(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        with patch("dashboard.services.glucose.fetch_glucose_readings") as mock_fetch:
            from dashboard.jobs import fetch_glucose

            fetch_glucose()

        mock_fetch.assert_not_called()
        assert GlucoseReading.objects.count() == 0

    def test_skips_widgets_with_no_credentials(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "glucose",
                    "enabled": True,
                    "position": 0,
                    "settings": {},
                },
            ]
        )
        with patch("dashboard.services.glucose.fetch_glucose_readings") as mock_fetch:
            from dashboard.jobs import fetch_glucose

            fetch_glucose()

        mock_fetch.assert_not_called()

    def test_creates_readings_from_service_response(self):
        dashboard = self._make_glucose_dashboard()
        now = datetime.now(tz=timezone.utc)
        mock_readings = [
            {
                "value": 120,
                "mmol_l": Decimal("6.7"),
                "trend_direction": "Flat",
                "trend_arrow": "\u2192",
                "recorded_at": now,
            },
            {
                "value": 115,
                "mmol_l": Decimal("6.4"),
                "trend_direction": "FortyFiveDown",
                "trend_arrow": "\u2198",
                "recorded_at": now - timedelta(minutes=5),
            },
        ]
        with patch(
            "dashboard.services.glucose.fetch_glucose_readings",
            return_value=mock_readings,
        ):
            from dashboard.jobs import fetch_glucose

            fetch_glucose()

        assert GlucoseReading.objects.filter(user=dashboard.user).count() == 2
        latest = GlucoseReading.objects.filter(user=dashboard.user).first()
        assert latest.value == 120

    def test_purges_readings_older_than_24_hours(self):
        dashboard = self._make_glucose_dashboard()
        now = datetime.now(tz=timezone.utc)

        # Create an old reading manually
        old_reading = GlucoseReading.objects.create(
            user=dashboard.user,
            value=90,
            mmol_l=Decimal("5.0"),
            trend_direction="Flat",
            trend_arrow="\u2192",
            recorded_at=now - timedelta(hours=25),
        )

        mock_readings = [
            {
                "value": 120,
                "mmol_l": Decimal("6.7"),
                "trend_direction": "Flat",
                "trend_arrow": "\u2192",
                "recorded_at": now,
            },
        ]
        with patch(
            "dashboard.services.glucose.fetch_glucose_readings",
            return_value=mock_readings,
        ):
            from dashboard.jobs import fetch_glucose

            fetch_glucose()

        assert not GlucoseReading.objects.filter(pk=old_reading.pk).exists()
        assert GlucoseReading.objects.filter(user=dashboard.user).count() == 1


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestFetchGlucoseReadingsService:
    def test_returns_list_of_reading_dicts_on_success(self):
        mock_reading = MagicMock()
        mock_reading.value = 120
        mock_reading.mmol_l = Decimal("6.7")
        mock_reading.trend_direction = "Flat"
        mock_reading.trend_arrow = "\u2192"
        mock_reading.datetime = datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)

        mock_dexcom = MagicMock()
        mock_dexcom.get_glucose_readings.return_value = [mock_reading]

        with patch("dashboard.services.glucose.Dexcom", return_value=mock_dexcom):
            from dashboard.services.glucose import fetch_glucose_readings

            result = fetch_glucose_readings("user", "pass")

        assert result is not None
        assert len(result) == 1
        assert result[0]["value"] == 120
        assert result[0]["mmol_l"] == Decimal("6.7")
        assert result[0]["trend_direction"] == "Flat"
        assert result[0]["recorded_at"] == datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)

    def test_returns_none_on_exception(self):
        with patch(
            "dashboard.services.glucose.Dexcom",
            side_effect=Exception("Auth failed"),
        ):
            from dashboard.services.glucose import fetch_glucose_readings

            result = fetch_glucose_readings("user", "badpass")

        assert result is None

    def test_returns_none_when_no_readings_available(self):
        mock_dexcom = MagicMock()
        mock_dexcom.get_glucose_readings.return_value = []

        with patch("dashboard.services.glucose.Dexcom", return_value=mock_dexcom):
            from dashboard.services.glucose import fetch_glucose_readings

            result = fetch_glucose_readings("user", "pass")

        assert result is None
