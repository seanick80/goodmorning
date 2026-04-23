"""Tests for kitchen timer API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from rest_framework.test import APIClient

from dashboard.models import Timer

from .conftest import TimerFactory


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
class TestTimerList:
    def test_get_empty(self, api_client):
        response = api_client.get("/api/timers/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_returns_active_timers(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        TimerFactory(label="pasta", expires_at=future)
        response = api_client.get("/api/timers/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["label"] == "pasta"
        assert data[0]["status"] == "running"

    def test_get_excludes_cancelled_and_dismissed(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        TimerFactory(label="active", expires_at=future)
        TimerFactory(status=Timer.Status.CANCELLED)
        TimerFactory(status=Timer.Status.DISMISSED)
        response = api_client.get("/api/timers/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["label"] == "active"

    def test_get_transitions_expired_to_ringing(self, api_client):
        past = datetime.now(tz=timezone.utc) - timedelta(seconds=10)
        timer = TimerFactory(expires_at=past, status=Timer.Status.RUNNING)
        response = api_client.get("/api/timers/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "ringing"
        timer.refresh_from_db()
        assert timer.status == Timer.Status.RINGING


@pytest.mark.django_db
class TestTimerCreate:
    def test_create_timer(self, api_client):
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 300, "label": "eggs"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "eggs"
        assert data["duration_seconds"] == 300
        assert data["status"] == "running"
        assert Timer.objects.count() == 1

    def test_create_timer_without_label(self, api_client):
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 60},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["label"] == ""

    def test_create_timer_sets_expires_at(self, api_client):
        before = datetime.now(tz=timezone.utc)
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 120},
            format="json",
        )
        after = datetime.now(tz=timezone.utc)
        expires = datetime.fromisoformat(response.json()["expires_at"])
        # Allow 2s tolerance for DB rounding and test execution time
        slack = timedelta(seconds=2)
        assert before + timedelta(seconds=120) - slack <= expires <= after + timedelta(seconds=120) + slack

    def test_max_2_active_timers(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        TimerFactory(expires_at=future)
        TimerFactory(expires_at=future)
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 60},
            format="json",
        )
        assert response.status_code == 409
        assert "Maximum 2" in response.json()["detail"]

    def test_can_create_after_previous_cancelled(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        TimerFactory(expires_at=future)
        TimerFactory(status=Timer.Status.CANCELLED)
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 60},
            format="json",
        )
        assert response.status_code == 201

    def test_rejects_invalid_duration(self, api_client):
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 0},
            format="json",
        )
        assert response.status_code == 400

    def test_rejects_duration_over_24h(self, api_client):
        response = api_client.post(
            "/api/timers/",
            {"duration_seconds": 86401},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestTimerCancel:
    def test_cancel_running_timer(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        timer = TimerFactory(expires_at=future)
        response = api_client.delete(f"/api/timers/{timer.id}/")
        assert response.status_code == 204
        timer.refresh_from_db()
        assert timer.status == Timer.Status.CANCELLED

    def test_cancel_ringing_timer(self, api_client):
        timer = TimerFactory(status=Timer.Status.RINGING)
        response = api_client.delete(f"/api/timers/{timer.id}/")
        assert response.status_code == 204
        timer.refresh_from_db()
        assert timer.status == Timer.Status.CANCELLED

    def test_cancel_nonexistent_returns_404(self, api_client):
        response = api_client.delete("/api/timers/9999/")
        assert response.status_code == 404

    def test_cancel_already_dismissed_returns_404(self, api_client):
        timer = TimerFactory(status=Timer.Status.DISMISSED)
        response = api_client.delete(f"/api/timers/{timer.id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestTimerDismiss:
    def test_dismiss_ringing_timers(self, api_client):
        TimerFactory(status=Timer.Status.RINGING)
        TimerFactory(status=Timer.Status.RINGING)
        response = api_client.post("/api/timers/dismiss/")
        assert response.status_code == 200
        assert response.json()["dismissed"] == 2
        assert Timer.objects.filter(status=Timer.Status.RINGING).count() == 0

    def test_dismiss_does_not_affect_running(self, api_client):
        future = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        TimerFactory(expires_at=future, status=Timer.Status.RUNNING)
        TimerFactory(status=Timer.Status.RINGING)
        response = api_client.post("/api/timers/dismiss/")
        assert response.json()["dismissed"] == 1
        assert Timer.objects.filter(status=Timer.Status.RUNNING).count() == 1

    def test_dismiss_with_none_ringing(self, api_client):
        response = api_client.post("/api/timers/dismiss/")
        assert response.status_code == 200
        assert response.json()["dismissed"] == 0
