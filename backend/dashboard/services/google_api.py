"""Google API credential helpers using django-allauth tokens."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials

if TYPE_CHECKING:
    from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/photoslibrary.readonly",
]


def get_google_credentials(user: User) -> Credentials | None:
    """Build google.oauth2.credentials.Credentials from allauth SocialToken.

    Returns None if the user has no connected Google account.
    """
    from allauth.socialaccount.models import SocialAccount, SocialToken

    account = SocialAccount.objects.filter(
        user=user, provider="google"
    ).first()
    if account is None:
        return None

    token = SocialToken.objects.filter(account=account).first()
    if token is None:
        return None

    from django.conf import settings

    return Credentials(
        token=token.token,
        refresh_token=token.token_secret,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )
