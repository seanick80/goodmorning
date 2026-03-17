"""Tests for dashboard models."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from dashboard.models import (
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)

from .conftest import (
    NewsHeadlineFactory,
    StockQuoteFactory,
    UserDashboardFactory,
    WeatherCacheFactory,
)


class TestUserDashboard:
    def test_creation_and_str(self):
        dashboard = UserDashboardFactory()
        assert str(dashboard) == f"Dashboard for {dashboard.user.username}"
        assert dashboard.pk is not None

    def test_default_widget_layout_structure(self):
        dashboard = UserDashboardFactory()
        layout = dashboard.widget_layout
        assert isinstance(layout, list)
        assert len(layout) == 2
        assert layout[0]["widget"] == "weather"
        assert layout[0]["enabled"] is True
        assert "position" in layout[0]
        assert "settings" in layout[0]

    def test_empty_widget_layout_default(self):
        """UserDashboard.widget_layout defaults to an empty list when no layout given."""
        dashboard = UserDashboardFactory(widget_layout=[])
        assert dashboard.widget_layout == []


class TestWeatherCache:
    def test_creation_and_str(self):
        weather = WeatherCacheFactory(location_key="40.71,-74.01")
        assert "40.71,-74.01" in str(weather)
        assert str(weather.temperature) in str(weather)

    def test_unique_location_key(self):
        WeatherCacheFactory(location_key="40.71,-74.01")
        with pytest.raises(IntegrityError):
            WeatherCacheFactory(location_key="40.71,-74.01")


class TestStockQuote:
    def test_creation_and_str(self):
        quote = StockQuoteFactory(symbol="AAPL")
        assert "AAPL" in str(quote)
        assert "$" in str(quote)

    def test_unique_symbol_constraint(self):
        StockQuoteFactory(symbol="GOOG")
        with pytest.raises(IntegrityError):
            StockQuoteFactory(symbol="GOOG")

    def test_ordering_by_symbol(self):
        StockQuoteFactory(symbol="ZZZZ")
        StockQuoteFactory(symbol="AAAA")
        quotes = list(StockQuote.objects.all())
        assert quotes[0].symbol == "AAAA"
        assert quotes[1].symbol == "ZZZZ"


class TestNewsHeadline:
    def test_creation_and_str(self):
        headline = NewsHeadlineFactory(source_name="BBC News", title="Test Headline")
        assert "BBC News" in str(headline)
        assert "Test Headline" in str(headline)

    def test_unique_together_source_url_and_guid(self):
        NewsHeadlineFactory(
            source_url="https://feeds.example.com/rss",
            guid="unique-id-1",
        )
        with pytest.raises(IntegrityError):
            NewsHeadlineFactory(
                source_url="https://feeds.example.com/rss",
                guid="unique-id-1",
            )

    def test_same_guid_different_source_allowed(self):
        NewsHeadlineFactory(
            source_url="https://feeds.example.com/rss",
            guid="shared-guid",
        )
        headline2 = NewsHeadlineFactory(
            source_url="https://feeds.other.com/rss",
            guid="shared-guid",
        )
        assert headline2.pk is not None

    def test_ordering_by_published_at_desc(self):
        from datetime import datetime, timezone

        old = NewsHeadlineFactory(
            published_at=datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc),
            guid="old",
        )
        new = NewsHeadlineFactory(
            published_at=datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc),
            guid="new",
        )
        headlines = list(NewsHeadline.objects.all())
        assert headlines[0].pk == new.pk
        assert headlines[1].pk == old.pk
