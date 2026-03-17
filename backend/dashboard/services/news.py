"""RSS feed parser for news headlines."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

logger = logging.getLogger(__name__)


def fetch_news_headlines(feed_url: str, source_name: str = "") -> list[dict]:
    """Parse an RSS feed and return headline dicts.

    Returns a list of dicts suitable for NewsHeadline.objects.update_or_create.
    """
    feed = feedparser.parse(feed_url)

    if feed.bozo and not feed.entries:
        logger.warning(
            "Malformed or empty RSS feed: %s (error: %s)",
            feed_url,
            feed.bozo_exception,
        )
        return []

    resolved_name = source_name or feed.feed.get("title", "")
    headlines: list[dict] = []

    for entry in feed.entries:
        guid = entry.get("id") or entry.get("link", "")
        if not guid:
            continue

        published_at = _parse_published(entry)

        headlines.append({
            "source_name": resolved_name,
            "guid": guid[:500],
            "title": (entry.get("title") or "Untitled")[:1000],
            "link": (entry.get("link") or "")[:2000],
            "summary": entry.get("summary", ""),
            "published_at": published_at,
        })

    logger.info("Parsed %d headlines from %s", len(headlines), feed_url)
    return headlines


def _parse_published(entry: dict) -> datetime | None:
    """Extract a timezone-aware published datetime from a feed entry."""
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        logger.debug("Could not parse date: %s", raw)
        return None
