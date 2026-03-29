"""Management command to configure Google OAuth via django-allauth."""

from __future__ import annotations

import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Configure Google OAuth SocialApp from environment variables."

    def handle(self, *args: object, **options: object) -> None:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            raise CommandError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set "
                "in environment variables."
            )

        # Ensure the default Site has a sensible domain
        site = Site.objects.get_or_create(
            id=1,
            defaults={"domain": "localhost", "name": "Good Morning Dashboard"},
        )[0]
        if site.domain == "example.com":
            site.domain = "localhost"
            site.name = "Good Morning Dashboard"
            site.save()
            self.stdout.write(
                self.style.SUCCESS("Updated Site domain to 'localhost'")
            )

        app, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={
                "name": "Google",
                "client_id": client_id,
                "secret": client_secret,
            },
        )

        # Link to current site
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)

        if created:
            self.stdout.write(
                self.style.SUCCESS("Created Google OAuth SocialApp")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Updated Google OAuth SocialApp")
            )
