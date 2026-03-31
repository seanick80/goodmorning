"""Google API credential helpers and data fetchers."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials

if TYPE_CHECKING:
    from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

GOOGLE_SCOPES = [
    "email",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/photospicker.mediaitems.readonly",
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

    # google-auth compares expiry with utcnow() (naive), so strip tz
    expiry = token.expires_at
    if expiry is not None and expiry.tzinfo is not None:
        expiry = expiry.replace(tzinfo=None)

    credentials = Credentials(
        token=token.token,
        refresh_token=token.token_secret,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
        expiry=expiry,
    )

    # Persist refreshed access token back to allauth
    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request

        credentials.refresh(Request())
        token.token = credentials.token
        token.expires_at = credentials.expiry
        token.save(update_fields=["token", "expires_at"])
        logger.info("Refreshed Google access token for %s", user.username)

    return credentials


def fetch_google_calendar_events(
    user: User,
    calendar_ids: list[str],
) -> list[dict]:
    """Fetch today's events from selected Google Calendars.

    Returns a list of dicts matching CalendarEvent field names.
    """
    credentials = get_google_credentials(user)
    if credentials is None:
        return []

    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=credentials)

    today = date.today()
    time_min = datetime.combine(
        today, datetime.min.time(), tzinfo=timezone.utc,
    ).isoformat()
    time_max = datetime.combine(
        today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc,
    ).isoformat()

    events: list[dict] = []

    for cal_id in calendar_ids:
        try:
            result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=50,
                )
                .execute()
            )
            for item in result.get("items", []):
                start_raw = item["start"].get(
                    "dateTime", item["start"].get("date")
                )
                end_raw = item["end"].get(
                    "dateTime", item["end"].get("date")
                )
                all_day = "date" in item["start"]

                start = _parse_gcal_datetime(start_raw, all_day)
                end = _parse_gcal_datetime(end_raw, all_day)

                events.append({
                    "uid": item["id"],
                    "title": item.get("summary", "Untitled"),
                    "description": item.get("description", ""),
                    "location": item.get("location", ""),
                    "start": start,
                    "end": end,
                    "all_day": all_day,
                })
        except Exception:
            logger.exception(
                "Failed to fetch events from Google Calendar %s", cal_id,
            )

    return events


def create_picker_session(user: User) -> dict | None:
    """Create a Google Photos Picker session.

    Returns dict with 'id' (session ID) and 'pickerUri', or None on failure.
    """
    credentials = get_google_credentials(user)
    if credentials is None:
        return None

    import google.auth.transport.requests
    # Ensure token is fresh
    if credentials.expired or not credentials.token:
        credentials.refresh(google.auth.transport.requests.Request())

    import requests

    resp = requests.post(
        "https://photospicker.googleapis.com/v1/sessions",
        headers={"Authorization": f"Bearer {credentials.token}"},
        json={},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data["id"],
        "picker_uri": data["pickerUri"],
    }


def poll_picker_session(user: User, session_id: str) -> dict | None:
    """Poll a Picker session to check if the user has finished selecting.

    Returns session dict with 'mediaItemsSet' boolean.
    """
    credentials = get_google_credentials(user)
    if credentials is None:
        return None

    import google.auth.transport.requests
    if credentials.expired or not credentials.token:
        credentials.refresh(google.auth.transport.requests.Request())

    import requests

    resp = requests.get(
        f"https://photospicker.googleapis.com/v1/sessions/{session_id}",
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_picker_media_items(
    user: User,
    session_id: str,
) -> list[dict]:
    """Fetch media items selected via the Picker.

    Returns a list of dicts with id, base_url, mime_type.
    """
    credentials = get_google_credentials(user)
    if credentials is None:
        return []

    import google.auth.transport.requests
    if credentials.expired or not credentials.token:
        credentials.refresh(google.auth.transport.requests.Request())

    import requests

    media_items: list[dict] = []
    page_token: str | None = None

    while True:
        params: dict = {"sessionId": session_id}
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(
            "https://photospicker.googleapis.com/v1/mediaItems",
            headers={"Authorization": f"Bearer {credentials.token}"},
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("mediaItems", []):
            media_file = item.get("mediaFile", {})
            media_items.append({
                "id": item.get("id", ""),
                "base_url": media_file.get("baseUrl", ""),
                "mime_type": media_file.get("mimeType", ""),
                "width": media_file.get("mediaFileMetadata", {}).get("width", 0),
                "height": media_file.get("mediaFileMetadata", {}).get("height", 0),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return media_items


def _parse_gcal_datetime(
    raw: str,
    all_day: bool,
) -> datetime:
    """Parse a Google Calendar datetime or date string."""
    if all_day:
        d = date.fromisoformat(raw)
        return datetime.combine(
            d, datetime.min.time(), tzinfo=timezone.utc,
        )
    return datetime.fromisoformat(raw)
