"""Management command to verify Google OAuth configuration.

Google OAuth credentials are now configured via settings.py using the
SOCIALACCOUNT_PROVIDERS['google']['APP'] dict, sourced from environment
variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.

This command verifies the configuration and cleans up any legacy
DB-stored SocialApp entries that would cause MultipleObjectsReturned.
"""

from __future__ import annotations

import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Verify Google OAuth config and clean up legacy DB entries."

    def handle(self, *args: object, **options: object) -> None:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            raise CommandError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set "
                "in environment variables."
            )

        # Clean up any legacy DB-stored SocialApps (settings.py handles this now)
        deleted, _ = SocialApp.objects.filter(provider="google").delete()
        if deleted:
            self.stdout.write(
                self.style.WARNING(
                    f"Removed {deleted} legacy DB SocialApp(s) — "
                    "credentials are now in settings.py"
                )
            )

        # Verify Site domain
        site = Site.objects.filter(id=1).first()
        if site:
            self.stdout.write(f"Site domain: {site.domain}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Google OAuth configured via settings (client_id: {client_id[:20]}...)"
            )
        )
