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

    credentials = Credentials(
        token=token.token,
        refresh_token=token.token_secret,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )

    # Persist refreshed access token back to allauth
    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request

        credentials.refresh(Request())
        token.token = credentials.token
        token.save(update_fields=["token"])
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


def fetch_google_photos_media(
    user: User,
    album_id: str,
) -> list[dict]:
    """Fetch media items from a Google Photos album.

    Returns a list of dicts with id, url, width, height, mime_type.
    """
    credentials = get_google_credentials(user)
    if credentials is None:
        return []

    from googleapiclient.discovery import build

    service = build(
        "photoslibrary", "v1",
        credentials=credentials,
        static_discovery=False,
    )

    media_items: list[dict] = []
    page_token: str | None = None

    while True:
        body: dict = {"albumId": album_id, "pageSize": 100}
        if page_token:
            body["pageToken"] = page_token

        result = service.mediaItems().search(body=body).execute()

        for item in result.get("mediaItems", []):
            base_url = item.get("baseUrl", "")
            metadata = item.get("mediaMetadata", {})
            width = metadata.get("width", "0")
            height = metadata.get("height", "0")

            media_items.append({
                "id": item["id"],
                "url": f"{base_url}=w{width}-h{height}",
                "width": int(width),
                "height": int(height),
                "mime_type": item.get("mimeType", ""),
            })

        page_token = result.get("nextPageToken")
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
