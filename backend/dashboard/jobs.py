"""APScheduler job functions for periodic data fetching."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone

from dashboard.models import (
    CalendarEvent,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)
from dashboard.services.calendar import fetch_calendar_events
from dashboard.services.news import fetch_news_headlines
from dashboard.services.stocks import fetch_stock_quote
from dashboard.services.weather import fetch_weather_data

logger = logging.getLogger(__name__)


# TODO: Change this to use Celery instead of APScheduler.

def fetch_weather():
    """Fetch weather for all configured locations."""
    dashboards = UserDashboard.objects.all()
    locations_fetched = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "weather" and widget.get("enabled"):
                lat = widget["settings"].get("latitude")
                lon = widget["settings"].get("longitude")
                if lat is None or lon is None:
                    continue
                location_key = f"{round(lat, 2)},{round(lon, 2)}"
                if location_key in locations_fetched:
                    continue
                try:
                    data = fetch_weather_data(lat, lon)
                    WeatherCache.objects.update_or_create(
                        location_key=location_key,
                        defaults={**data, "latitude": lat, "longitude": lon},
                    )
                    locations_fetched.add(location_key)
                    logger.info("Weather updated for %s", location_key)
                except Exception:
                    logger.exception("Failed to fetch weather for %s", location_key)


def fetch_stocks() -> None:
    """Fetch stock quotes for all configured symbols."""
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        logger.warning("FINNHUB_API_KEY not set; skipping stock fetch")
        return

    dashboards = UserDashboard.objects.all()
    symbols: set[str] = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "stocks" and widget.get("enabled"):
                symbols.update(widget["settings"].get("symbols", []))

    for symbol in sorted(symbols):
        try:
            data = fetch_stock_quote(symbol, api_key)
            if data is None:
                continue
            StockQuote.objects.update_or_create(
                symbol=symbol,
                defaults=data,
            )
            logger.info("Stock updated for %s", symbol)
        except Exception:
            logger.exception("Failed to update stock for %s", symbol)


def fetch_calendar() -> None:
    """Fetch calendar events from all configured ICS feeds."""
    dashboards = UserDashboard.objects.all()
    ics_urls: set[str] = set()

    # Include calendar URL from environment if set (keeps URL out of DB/source)
    env_calendar = os.environ.get("USER_CALENDAR", "")
    if env_calendar:
        ics_urls.add(env_calendar)

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "calendar" and widget.get("enabled"):
                ics_urls.update(widget["settings"].get("ics_urls", []))

    for ics_url in sorted(ics_urls):
        try:
            events = fetch_calendar_events(ics_url)
            # Delete today's old events for this source, then recreate
            today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
            today_end = today_start + timedelta(days=1)
            CalendarEvent.objects.filter(
                source_url=ics_url,
                start__gte=today_start,
                start__lt=today_end,
            ).delete()

            for event_data in events:
                CalendarEvent.objects.create(
                    source_url=ics_url,
                    **event_data,
                )
            logger.info("Calendar updated from %s (%d events)", ics_url, len(events))
        except Exception:
            logger.exception("Failed to fetch calendar from %s", ics_url)


def fetch_news() -> None:
    """Fetch news headlines from all configured RSS feeds."""
    dashboards = UserDashboard.objects.all()
    sources: dict[str, str] = {}  # url -> name

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "news" and widget.get("enabled"):
                for source in widget["settings"].get("sources", []):
                    url = source.get("url", "")
                    if url:
                        sources[url] = source.get("name", "")

    for feed_url, source_name in sorted(sources.items()):
        try:
            headlines = fetch_news_headlines(feed_url, source_name)
            for headline_data in headlines:
                guid = headline_data.pop("guid")
                NewsHeadline.objects.update_or_create(
                    source_url=feed_url,
                    guid=guid,
                    defaults=headline_data,
                )
            logger.info("News updated from %s (%d headlines)", feed_url, len(headlines))
        except Exception:
            logger.exception("Failed to fetch news from %s", feed_url)

    # Purge headlines older than 24 hours
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    deleted, _ = NewsHeadline.objects.filter(fetched_at__lt=cutoff).delete()
    if deleted:
        logger.info("Purged %d old news headlines", deleted)
