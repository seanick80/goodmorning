"""Tests for the setup_google_oauth management command."""

from __future__ import annotations

import pytest
from django.contrib.sites.models import Site
from django.core.management import CommandError, call_command

from allauth.socialaccount.models import SocialApp


@pytest.mark.django_db()
class TestSetupGoogleOAuth:
    def test_creates_social_app(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")

        call_command("setup_google_oauth")

        app = SocialApp.objects.get(provider="google")
        assert app.client_id == "test-client-id"
        assert app.secret == "test-client-secret"
        assert app.name == "Google"
        assert app.sites.filter(id=1).exists()

    def test_updates_existing_social_app(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "old-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "old-secret")
        call_command("setup_google_oauth")

        monkeypatch.setenv("GOOGLE_CLIENT_ID", "new-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "new-secret")
        call_command("setup_google_oauth")

        assert SocialApp.objects.filter(provider="google").count() == 1
        app = SocialApp.objects.get(provider="google")
        assert app.client_id == "new-id"
        assert app.secret == "new-secret"

    def test_updates_default_site_domain(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")

        site = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example"},
        )[0]
        site.domain = "example.com"
        site.save()

        call_command("setup_google_oauth")

        site.refresh_from_db()
        assert site.domain == "localhost"
        assert site.name == "Good Morning Dashboard"

    def test_raises_without_credentials(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(CommandError, match="GOOGLE_CLIENT_ID"):
            call_command("setup_google_oauth")
