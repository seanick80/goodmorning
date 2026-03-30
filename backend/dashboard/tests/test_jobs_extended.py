"""Extended tests for dashboard background jobs (Google Calendar, Google Photos)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.sites.models import Site

from dashboard.jobs import fetch_google_calendar, fetch_google_photos
from dashboard.models import CalendarEvent, UserDashboard

from .conftest import UserDashboardFactory, UserFactory


def _create_google_user(*, widget_layout=None):
    """Create a user with a Google SocialAccount, SocialToken, and dashboard."""
    user = UserFactory()

    app, _ = SocialApp.objects.get_or_create(
        provider="google",
        defaults={"name": "Google", "client_id": "cid", "secret": "csec"},
    )
    site = Site.objects.get(id=1)
    if not app.sites.filter(id=site.id).exists():
        app.sites.add(site)

    account = SocialAccount.objects.create(
        user=user, provider="google", uid=f"g-{user.pk}", extra_data={},
    )
    SocialToken.objects.create(
        account=account, app=app, token="tok", token_secret="rtok",
    )

    if widget_layout is not None:
        UserDashboardFactory(user=user, widget_layout=widget_layout)

    return user


class TestFetchGoogleCalendar:
    def test_fetches_events_for_google_user(self):
        user = _create_google_user(
            widget_layout=[
                {
                    "widget": "calendar",
                    "enabled": True,
                    "position": 0,
                    "settings": {
                        "google_calendar_ids": ["primary"],
                    },
                },
            ],
        )

        today = datetime.combine(
            date.today(), datetime.min.time(), tzinfo=timezone.utc,
        )
        mock_events = [
            {
                "uid": "evt-1",
                "title": "Team Standup",
                "description": "",
                "location": "",
                "start": today.replace(hour=9),
                "end": today.replace(hour=9, minute=30),
                "all_day": False,
            },
        ]

        with patch(
            "dashboard.services.google_api.fetch_google_calendar_events",
            return_value=mock_events,
        ):
            fetch_google_calendar()

        events = CalendarEvent.objects.filter(source_url=f"google:{user.id}")
        assert events.count() == 1
        assert events.first().title == "Team Standup"

    def test_skips_user_without_dashboard(self):
        """User has a Google account but no dashboard -- should not error."""
        user = UserFactory()

        app, _ = SocialApp.objects.get_or_create(
            provider="google",
            defaults={"name": "Google", "client_id": "cid", "secret": "csec"},
        )
        site = Site.objects.get(id=1)
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)

        SocialAccount.objects.create(
            user=user, provider="google", uid=f"g-{user.pk}", extra_data={},
        )

        # Should not raise
        fetch_google_calendar()

    def test_skips_user_without_calendar_ids(self):
        _create_google_user(
            widget_layout=[
                {
                    "widget": "calendar",
                    "enabled": True,
                    "position": 0,
                    "settings": {},
                },
            ],
        )

        with patch(
            "dashboard.services.google_api.fetch_google_calendar_events",
        ) as mock_fetch:
            fetch_google_calendar()
            mock_fetch.assert_not_called()


class TestFetchGooglePhotos:
    def test_refreshes_cached_media(self):
        user = _create_google_user(
            widget_layout=[
                {
                    "widget": "photos",
                    "enabled": True,
                    "position": 0,
                    "settings": {
                        "picker_session_id": "sess-abc",
                    },
                },
            ],
        )

        mock_media = [
            {"id": "m1", "base_url": "https://lh3.google.com/m1", "mime_type": "image/jpeg"},
            {"id": "m2", "base_url": "https://lh3.google.com/m2", "mime_type": "image/png"},
        ]

        with patch(
            "dashboard.services.google_api.fetch_picker_media_items",
            return_value=mock_media,
        ):
            fetch_google_photos()

        dashboard = UserDashboard.objects.get(user=user)
        slideshow = next(
            w for w in dashboard.widget_layout if w["widget"] == "photos"
        )
        assert slideshow["settings"]["cached_media"] == mock_media

    def test_skips_user_without_session(self):
        _create_google_user(
            widget_layout=[
                {
                    "widget": "photos",
                    "enabled": True,
                    "position": 0,
                    "settings": {},
                },
            ],
        )

        with patch(
            "dashboard.services.google_api.fetch_picker_media_items",
        ) as mock_fetch:
            fetch_google_photos()
            mock_fetch.assert_not_called()
