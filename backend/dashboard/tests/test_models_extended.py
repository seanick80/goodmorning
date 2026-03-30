"""Extended tests for dashboard models (CalendarEvent)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from django.db import IntegrityError

from dashboard.models import CalendarEvent

from .conftest import CalendarEventFactory


class TestCalendarEvent:
    def test_creation(self):
        event = CalendarEventFactory(
            title="Sprint Planning",
            location="Room B",
            all_day=False,
        )
        assert event.pk is not None
        assert event.title == "Sprint Planning"
        assert event.location == "Room B"
        assert event.all_day is False

    def test_str(self):
        start = datetime(2026, 3, 30, 14, 0, tzinfo=timezone.utc)
        event = CalendarEventFactory(title="Design Review", start=start)
        result = str(event)
        assert "Design Review" in result
        assert "2026" in result

    def test_unique_together(self):
        CalendarEventFactory(
            source_url="https://cal.example.com/feed.ics",
            uid="unique-event-1",
        )
        with pytest.raises(IntegrityError):
            CalendarEventFactory(
                source_url="https://cal.example.com/feed.ics",
                uid="unique-event-1",
            )

    def test_ordering(self):
        early = datetime(2026, 3, 30, 8, 0, tzinfo=timezone.utc)
        late = datetime(2026, 3, 30, 16, 0, tzinfo=timezone.utc)
        CalendarEventFactory(title="Afternoon", start=late)
        CalendarEventFactory(title="Morning", start=early)

        events = list(CalendarEvent.objects.values_list("title", flat=True))
        assert events == ["Morning", "Afternoon"]
