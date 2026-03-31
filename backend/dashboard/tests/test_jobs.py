"""Tests for dashboard scheduled jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from dashboard.models import NewsHeadline, StockQuote, WeatherCache

from .conftest import UserDashboardFactory


class TestFetchWeatherJob:
    def test_creates_weather_cache_entry(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        mock_data = {
            "temperature": 72.5,
            "temperature_unit": "fahrenheit",
            "feels_like": 70.0,
            "humidity": 55,
            "wind_speed": 8.5,
            "wind_direction": 180,
            "weather_code": 0,
            "precipitation_probability": 10,
            "sunrise": None,
            "sunset": None,
            "daily_high": 78.0,
            "daily_low": 62.0,
            "hourly_forecast": [],
        }
        with patch("dashboard.jobs.fetch_weather_data", return_value=mock_data):
            from dashboard.jobs import fetch_weather

            fetch_weather()

        cache = WeatherCache.objects.get(location_key="40.71,-74.01")
        assert cache.temperature == 72.5
        assert cache.latitude == 40.71
        assert cache.longitude == -74.01

    def test_handles_service_errors_gracefully(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        with patch(
            "dashboard.jobs.fetch_weather_data",
            side_effect=Exception("API unavailable"),
        ):
            from dashboard.jobs import fetch_weather

            # Should not raise — errors are caught and logged
            fetch_weather()

        assert WeatherCache.objects.count() == 0

    def test_skips_disabled_weather_widgets(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": False,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        with patch("dashboard.jobs.fetch_weather_data") as mock_fetch:
            from dashboard.jobs import fetch_weather

            fetch_weather()

        mock_fetch.assert_not_called()
        assert WeatherCache.objects.count() == 0

    def test_skips_widgets_without_coordinates(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {},
                },
            ]
        )
        with patch("dashboard.jobs.fetch_weather_data") as mock_fetch:
            from dashboard.jobs import fetch_weather

            fetch_weather()

        mock_fetch.assert_not_called()

    def test_deduplicates_same_location(self):
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "weather",
                    "enabled": True,
                    "position": 0,
                    "settings": {"latitude": 40.71, "longitude": -74.01},
                },
            ]
        )
        mock_data = {
            "temperature": 72.5,
            "temperature_unit": "fahrenheit",
            "feels_like": 70.0,
            "humidity": 55,
            "wind_speed": 8.5,
            "wind_direction": 180,
            "weather_code": 0,
            "precipitation_probability": 10,
            "sunrise": None,
            "sunset": None,
            "daily_high": 78.0,
            "daily_low": 62.0,
            "hourly_forecast": [],
        }
        with patch("dashboard.jobs.fetch_weather_data", return_value=mock_data) as mock_fetch:
            from dashboard.jobs import fetch_weather

            fetch_weather()

        # Should only fetch once despite two dashboards with same location
        mock_fetch.assert_called_once()
        assert WeatherCache.objects.count() == 1


class TestFetchStocksJob:
    def _make_stocks_dashboard(self, symbols: list[str]) -> None:
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "stocks",
                    "enabled": True,
                    "position": 0,
                    "settings": {"symbols": symbols},
                },
            ]
        )

    @patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})
    def test_creates_stock_quote_entries(self):
        self._make_stocks_dashboard(["AAPL", "GOOG"])
        mock_data = {
            "current_price": 150.25,
            "change": 2.50,
            "change_percent": 1.69,
            "day_high": 152.00,
            "day_low": 148.00,
            "open_price": 149.00,
            "previous_close": 147.75,
            "timestamp": datetime(2026, 3, 17, 16, 0, tzinfo=timezone.utc),
        }
        with patch("dashboard.jobs.fetch_stock_quote", return_value=mock_data):
            from dashboard.jobs import fetch_stocks

            fetch_stocks()

        assert StockQuote.objects.count() == 2
        assert StockQuote.objects.filter(symbol="AAPL").exists()
        assert StockQuote.objects.filter(symbol="GOOG").exists()

    @patch.dict("os.environ", {"FINNHUB_API_KEY": ""})
    def test_handles_missing_api_key(self):
        self._make_stocks_dashboard(["AAPL"])

        from dashboard.jobs import fetch_stocks

        fetch_stocks()

        assert StockQuote.objects.count() == 0

    @patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})
    def test_skips_when_service_returns_none(self):
        self._make_stocks_dashboard(["INVALID"])
        with patch("dashboard.jobs.fetch_stock_quote", return_value=None):
            from dashboard.jobs import fetch_stocks

            fetch_stocks()

        assert StockQuote.objects.count() == 0


class TestFetchNewsJob:
    def _make_news_dashboard(self, sources: list[dict]) -> None:
        UserDashboardFactory(
            widget_layout=[
                {
                    "widget": "news",
                    "enabled": True,
                    "position": 0,
                    "settings": {"sources": sources},
                },
            ]
        )

    def test_creates_news_headlines(self):
        self._make_news_dashboard([
            {"url": "https://feeds.example.com/rss", "name": "Example News"},
        ])
        mock_headlines = [
            {
                "source_name": "Example News",
                "guid": "headline-1",
                "title": "Breaking Story",
                "link": "https://example.com/1",
                "summary": "Summary text",
                "published_at": datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc),
            },
        ]
        with patch("dashboard.jobs.fetch_news_headlines", return_value=mock_headlines):
            from dashboard.jobs import fetch_news

            fetch_news()

        assert NewsHeadline.objects.count() == 1
        headline = NewsHeadline.objects.first()
        assert headline.title == "Breaking Story"
        assert headline.source_url == "https://feeds.example.com/rss"

    def test_purges_old_headlines(self):
        from datetime import timedelta

        from dashboard.tests.conftest import NewsHeadlineFactory

        # Create an old headline (fetched > 24h ago)
        old = NewsHeadlineFactory()
        # Manually set fetched_at to old (auto_now prevents normal save)
        NewsHeadline.objects.filter(pk=old.pk).update(
            fetched_at=datetime.now(tz=timezone.utc) - timedelta(hours=25)
        )

        self._make_news_dashboard([
            {"url": "https://feeds.example.com/rss", "name": "Example News"},
        ])
        with patch("dashboard.jobs.fetch_news_headlines", return_value=[]):
            from dashboard.jobs import fetch_news

            fetch_news()

        assert not NewsHeadline.objects.filter(pk=old.pk).exists()

    def test_handles_service_error_gracefully(self):
        self._make_news_dashboard([
            {"url": "https://feeds.example.com/rss", "name": "Example News"},
        ])
        with patch(
            "dashboard.jobs.fetch_news_headlines",
            side_effect=Exception("Parse error"),
        ):
            from dashboard.jobs import fetch_news

            # Should not raise
            fetch_news()

        assert NewsHeadline.objects.count() == 0
