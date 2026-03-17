"""ICS calendar feed parser."""

from __future__ import annotations

import logging
from datetime import date, datetime

import requests
from icalendar import Calendar

logger = logging.getLogger(__name__)


def fetch_calendar_events(ics_url: str) -> list[dict]:
    """Fetch and parse an ICS feed, returning today's events.

    Returns a list of dicts suitable for CalendarEvent creation.
    """
    try:
        response = requests.get(ics_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to fetch ICS feed: %s", ics_url)
        return []

    try:
        cal = Calendar.from_ical(response.content)
    except Exception:
        logger.exception("Failed to parse ICS data from %s", ics_url)
        return []

    today = date.today()
    events: list[dict] = []

    for component in cal.walk("VEVENT"):
        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        dt_value = dtstart.dt

        # Determine if this is an all-day event (date vs datetime)
        all_day = isinstance(dt_value, date) and not isinstance(dt_value, datetime)

        # Filter to today's events
        event_date = dt_value if all_day else dt_value.date()
        if event_date != today:
            continue

        dtend = component.get("dtend")
        end_value = dtend.dt if dtend else None

        events.append({
            "uid": str(component.get("uid", "")),
            "title": str(component.get("summary", "Untitled")),
            "description": str(component.get("description", "")),
            "location": str(component.get("location", "")),
            "start": dt_value if isinstance(dt_value, datetime) else datetime.combine(dt_value, datetime.min.time()),
            "end": end_value if isinstance(end_value, datetime) else (
                datetime.combine(end_value, datetime.min.time()) if end_value else None
            ),
            "all_day": all_day,
        })

    logger.info("Parsed %d events for today from %s", len(events), ics_url)
    return events
