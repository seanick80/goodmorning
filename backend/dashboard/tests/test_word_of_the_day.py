"""Tests for the Word of the Day widget view."""

from __future__ import annotations

import datetime as dt_module
from datetime import date, timedelta
from unittest.mock import PropertyMock, patch

import pytest
from rest_framework.test import APIClient

from .conftest import UserDashboardFactory, UserFactory


# Keep a reference to the real date class before any mocking
_real_date = date


class _FakeDate(_real_date):
    """A date subclass whose today() can be controlled."""

    _today: _real_date | None = None

    @classmethod
    def today(cls) -> _real_date:
        if cls._today is not None:
            return cls._today
        return _real_date.today()


def _patch_today(target_date: _real_date):
    """Context manager to patch date.today() in the views module."""
    _FakeDate._today = target_date
    return patch("dashboard.views.date", _FakeDate)


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


def _make_wotd_dashboard(
    *,
    grade_level: int = 1,
    start_date: str | None = None,
    enabled: bool = True,
) -> None:
    settings: dict = {"grade_level": grade_level}
    if start_date is not None:
        settings["start_date"] = start_date
    UserDashboardFactory(
        user=UserFactory(is_superuser=True, username="admin"),
        widget_layout=[
            {
                "widget": "wordoftheday",
                "enabled": enabled,
                "position": 0,
                "settings": settings,
            },
        ],
    )


class TestWordOfTheDayView:
    def test_returns_200_with_valid_word_data(self, api_client):
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        assert response.status_code == 200
        data = response.json()
        assert "word" in data
        assert "pattern" in data
        assert "pattern_position" in data
        assert "grade" in data
        assert "week_number" in data
        assert "day_index" in data
        assert "is_weekend" in data

    def test_returns_correct_word_for_monday_week1(self, api_client):
        # Week 1, Monday (day_index=0) -> grade_1 week 1 = "at" family
        # words: ["cat", "bat", "hat", "mat", "sat"]
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["word"] == "cat"
        assert data["pattern"] == "at"
        assert data["pattern_position"] == "end"
        assert data["grade"] == 1
        assert data["week_number"] == 1
        assert data["day_index"] == 0
        assert data["is_weekend"] is False

    def test_returns_correct_word_for_wednesday(self, api_client):
        # Week 1, Wednesday (day_index=2) -> "hat"
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 7)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["word"] == "hat"
        assert data["day_index"] == 2

    def test_weekend_saturday_returns_friday_word(self, api_client):
        # Saturday of week 1 -> day_index=4 -> "sat"
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 10)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["word"] == "sat"
        assert data["day_index"] == 4
        assert data["is_weekend"] is True

    def test_weekend_sunday_returns_friday_word(self, api_client):
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 11)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["is_weekend"] is True
        assert data["day_index"] == 4

    def test_cycles_to_week_2(self, api_client):
        # Week 2, Monday -> "an" family, word "can"
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 12)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["word"] == "can"
        assert data["pattern"] == "an"
        assert data["week_number"] == 2

    def test_weeks_cycle_after_exhaustion(self, api_client):
        # 52 weeks later -> cycles back to week 1
        _make_wotd_dashboard(start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5) + timedelta(weeks=52)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["week_number"] == 1
        assert data["pattern"] == "at"

    def test_grade_2_returns_correct_data(self, api_client):
        _make_wotd_dashboard(grade_level=2, start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["grade"] == 2
        assert data["pattern"] == "tch"
        assert data["word"] == "batch"

    def test_grade_3_returns_correct_data(self, api_client):
        _make_wotd_dashboard(grade_level=3, start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["grade"] == 3
        assert data["pattern"] == "cious"
        assert data["word"] == "gracious"

    def test_invalid_grade_returns_404(self, api_client):
        _make_wotd_dashboard(grade_level=99, start_date="2026-01-05")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        assert response.status_code == 404
        assert "No data for grade 99" in response.json()["detail"]

    def test_no_dashboard_returns_404(self, api_client):
        response = api_client.get("/api/word-of-the-day/")
        assert response.status_code == 404
        assert "No dashboard configured" in response.json()["detail"]

    def test_default_start_date_uses_first_monday_of_year(self, api_client):
        # No start_date in settings -> defaults to first Monday of year
        # 2026-01-05 is the first Monday of 2026 (Jan 1 is Thursday)
        _make_wotd_dashboard(start_date=None)

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["week_number"] == 1
        assert data["day_index"] == 0

    def test_before_start_date_clamps_to_week_1(self, api_client):
        _make_wotd_dashboard(start_date="2026-06-01")

        with _patch_today(date(2026, 1, 5)):
            response = api_client.get("/api/word-of-the-day/")

        data = response.json()
        assert data["week_number"] == 1
