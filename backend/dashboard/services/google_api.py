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
        update_fields = ["token", "expires_at"]
        # Google may rotate the refresh token; persist it if it changed so we
        # don't keep sending a stale one (which eventually fails with
        # invalid_grant and forces a re-login).
        if credentials.refresh_token and credentials.refresh_token != token.token_secret:
            token.token_secret = credentials.refresh_token
            update_fields.append("token_secret")
        token.save(update_fields=update_fields)
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


def _local_filename(item: dict) -> str:
    """Stable on-disk filename for a picked media item."""
    import hashlib

    key = item.get("id") or item.get("base_url", "")
    ext = ".png" if "png" in item.get("mime_type", "").lower() else ".jpg"
    return hashlib.sha1(key.encode()).hexdigest()[:20] + ext


def persist_media_items(user: User, items: list[dict]) -> list[dict]:
    """Download picked photos to local storage and annotate with 'local_path'.

    Picker baseUrls and sessions are ephemeral, so we download the bytes once
    and serve them locally thereafter. Idempotent: skips items already saved.
    Items that fail to download are returned unchanged (proxy fallback still
    applies) so one bad photo doesn't drop the rest.
    """
    import os

    import requests

    from django.conf import settings

    credentials = get_google_credentials(user)
    if credentials is None:
        return items

    os.makedirs(settings.BACKGROUNDS_DIR, exist_ok=True)

    result: list[dict] = []
    for item in items:
        base_url = item.get("base_url", "")
        if not base_url:
            result.append(item)
            continue

        fname = _local_filename(item)
        fpath = os.path.join(settings.BACKGROUNDS_DIR, fname)

        if not (os.path.exists(fpath) and os.path.getsize(fpath) > 0):
            try:
                resp = requests.get(
                    f"{base_url}=w1920-h1080",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                    timeout=20,
                )
                resp.raise_for_status()
                with open(fpath, "wb") as fh:
                    fh.write(resp.content)
            except Exception:
                logger.exception(
                    "Failed to download picked photo %s", item.get("id", ""),
                )
                result.append(item)
                continue

        result.append({**item, "local_path": fname})

    return result


def prune_orphan_backgrounds() -> int:
    """Delete downloaded background files no longer referenced by any dashboard.

    Returns the number of files removed.
    """
    import os

    from django.conf import settings

    from dashboard.models import UserDashboard

    referenced: set[str] = set()
    for dashboard in UserDashboard.objects.all():
        for widget in dashboard.widget_layout:
            if widget.get("widget") != "photos":
                continue
            for media in widget.get("settings", {}).get("cached_media", []):
                local_path = media.get("local_path")
                if local_path:
                    referenced.add(local_path)

    removed = 0
    try:
        for fname in os.listdir(settings.BACKGROUNDS_DIR):
            if fname not in referenced:
                try:
                    os.remove(os.path.join(settings.BACKGROUNDS_DIR, fname))
                    removed += 1
                except OSError:
                    logger.warning("Could not delete orphan background %s", fname)
    except FileNotFoundError:
        pass

    return removed


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
