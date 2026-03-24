"""ICS calendar feed parser."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

import recurring_ical_events
import requests
from icalendar import Calendar

from ._http import fetch_with_retry

logger = logging.getLogger(__name__)


def fetch_calendar_events(ics_url: str) -> list[dict]:
    """Fetch and parse an ICS feed, returning today's events.

    Uses recurring-ical-events to expand RRULE recurrences so that
    repeating events show up on the correct dates.

    Returns a list of dicts suitable for CalendarEvent creation.
    """
    try:
        response = fetch_with_retry(ics_url)
    except requests.RequestException:
        logger.exception("Failed to fetch ICS feed: %s", ics_url)
        return []

    try:
        cal = Calendar.from_ical(response.content)
    except Exception:
        logger.exception("Failed to parse ICS data from %s", ics_url)
        return []

    today = date.today()
    tomorrow = today.replace(day=today.day + 1) if today.day < 28 else (
        today + __import__("datetime").timedelta(days=1)
    )

    try:
        recurring = recurring_ical_events.of(cal).between(today, tomorrow)
    except Exception:
        logger.exception("Failed to expand recurring events from %s", ics_url)
        recurring = []

    events: list[dict] = []

    for component in recurring:
        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        dt_value = dtstart.dt

        all_day = isinstance(dt_value, date) and not isinstance(dt_value, datetime)

        dtend = component.get("dtend")
        end_value = dtend.dt if dtend else None

        start = dt_value if isinstance(dt_value, datetime) else datetime.combine(
            dt_value, datetime.min.time(), tzinfo=timezone.utc,
        )
        end = end_value if isinstance(end_value, datetime) else (
            datetime.combine(end_value, datetime.min.time(), tzinfo=timezone.utc)
            if end_value else None
        )

        events.append({
            "uid": str(component.get("uid", "")),
            "title": str(component.get("summary", "Untitled")),
            "description": str(component.get("description", "")),
            "location": str(component.get("location", "")),
            "start": start,
            "end": end,
            "all_day": all_day,
        })

    logger.info("Parsed %d events for today from %s", len(events), ics_url)
    return events
