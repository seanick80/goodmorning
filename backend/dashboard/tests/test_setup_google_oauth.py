"""Tests for the setup_google_oauth management command."""

from __future__ import annotations

import pytest
from django.core.management import CommandError, call_command

from allauth.socialaccount.models import SocialApp


@pytest.mark.django_db()
class TestSetupGoogleOAuth:
    def test_verifies_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")

        call_command("setup_google_oauth")

        # Command should NOT create DB entries (settings-based config)
        assert SocialApp.objects.filter(provider="google").count() == 0

    def test_removes_legacy_db_entries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")

        # Create a legacy DB SocialApp
        SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="old-id",
            secret="old-secret",
        )
        assert SocialApp.objects.filter(provider="google").count() == 1

        call_command("setup_google_oauth")

        # Legacy entry should be cleaned up
        assert SocialApp.objects.filter(provider="google").count() == 0

    def test_raises_without_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(CommandError, match="GOOGLE_CLIENT_ID"):
            call_command("setup_google_oauth")
