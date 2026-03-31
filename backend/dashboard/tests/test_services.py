"""Tests for dashboard services."""

from __future__ import annotations

from datetime import datetime, time, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests
import requests_mock as rm

from dashboard.services.news import fetch_news_headlines
from dashboard.services.stocks import FINNHUB_QUOTE_URL, fetch_stock_quote
from dashboard.services.weather import OPEN_METEO_URL, fetch_weather_data


MOCK_OPEN_METEO_RESPONSE = {
    "current": {
        "temperature_2m": 72.5,
        "relative_humidity_2m": 55,
        "apparent_temperature": 70.0,
        "weather_code": 1,
        "wind_speed_10m": 8.5,
        "wind_direction_10m": 180,
        "precipitation": 0.0,
    },
    "hourly": {
        "time": ["2026-03-17T08:00", "2026-03-17T09:00"],
        "temperature_2m": [65.0, 68.0],
        "weather_code": [0, 1],
        "precipitation_probability": [5, 10],
    },
    "daily": {
        "temperature_2m_max": [78.0],
        "temperature_2m_min": [62.0],
        "sunrise": ["2026-03-17T06:30"],
        "sunset": ["2026-03-17T19:45"],
    },
}


class TestFetchWeatherData:
    def test_returns_correct_structure(self):
        with rm.Mocker() as m:
            m.get(OPEN_METEO_URL, json=MOCK_OPEN_METEO_RESPONSE)
            result = fetch_weather_data(40.71, -74.01)

        assert result["temperature"] == 72.5
        assert result["temperature_unit"] == "fahrenheit"
        assert result["feels_like"] == 70.0
        assert result["humidity"] == 55
        assert result["wind_speed"] == 8.5
        assert result["wind_direction"] == 180
        assert result["weather_code"] == 1
        assert result["daily_high"] == 78.0
        assert result["daily_low"] == 62.0
        assert result["sunrise"] == time(6, 30)
        assert result["sunset"] == time(19, 45)

    def test_returns_hourly_forecast(self):
        with rm.Mocker() as m:
            m.get(OPEN_METEO_URL, json=MOCK_OPEN_METEO_RESPONSE)
            result = fetch_weather_data(40.71, -74.01)

        assert len(result["hourly_forecast"]) == 2
        assert result["hourly_forecast"][0]["temp"] == 65.0
        assert result["hourly_forecast"][1]["precip_prob"] == 10

    def test_celsius_units(self):
        with rm.Mocker() as m:
            m.get(OPEN_METEO_URL, json=MOCK_OPEN_METEO_RESPONSE)
            result = fetch_weather_data(40.71, -74.01, units="celsius")

        assert result["temperature_unit"] == "celsius"
        # Verify the request used celsius params
        assert "temperature_unit=celsius" in m.last_request.url
        assert "wind_speed_unit=kmh" in m.last_request.url

    def test_handles_api_error_response(self):
        with rm.Mocker() as m:
            m.get(OPEN_METEO_URL, status_code=500)
            with pytest.raises(requests.HTTPError):
                fetch_weather_data(40.71, -74.01)

    def test_handles_timeout(self):
        with rm.Mocker() as m:
            m.get(OPEN_METEO_URL, exc=requests.ConnectionError("Connection timeout"))
            with pytest.raises(requests.ConnectionError):
                fetch_weather_data(40.71, -74.01)


MOCK_FINNHUB_RESPONSE = {
    "c": 150.25,
    "d": 2.50,
    "dp": 1.69,
    "h": 152.00,
    "l": 148.00,
    "o": 149.00,
    "pc": 147.75,
    "t": 1742227200,
}


class TestFetchStockQuote:
    def test_returns_correct_structure(self):
        with rm.Mocker() as m:
            m.get(FINNHUB_QUOTE_URL, json=MOCK_FINNHUB_RESPONSE)
            result = fetch_stock_quote("AAPL", "test-api-key")

        assert result is not None
        assert result["current_price"] == 150.25
        assert result["change"] == 2.50
        assert result["change_percent"] == 1.69
        assert result["day_high"] == 152.00
        assert result["day_low"] == 148.00
        assert result["open_price"] == 149.00
        assert result["previous_close"] == 147.75
        assert isinstance(result["timestamp"], datetime)

    def test_handles_api_error(self):
        with rm.Mocker() as m:
            m.get(FINNHUB_QUOTE_URL, status_code=500)
            result = fetch_stock_quote("AAPL", "test-api-key")

        assert result is None

    def test_handles_missing_api_key(self):
        result = fetch_stock_quote("AAPL", "")
        assert result is None

    def test_returns_none_for_invalid_symbol(self):
        with rm.Mocker() as m:
            m.get(FINNHUB_QUOTE_URL, json={"c": 0, "d": None, "dp": None})
            result = fetch_stock_quote("INVALID", "test-api-key")

        assert result is None


class TestFetchNewsHeadlines:
    def test_parses_feed_with_entries(self):
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                "id": "guid-1",
                "title": "Breaking News",
                "link": "https://example.com/1",
                "summary": "A summary",
                "published": "Mon, 17 Mar 2026 08:00:00 GMT",
            },
            {
                "id": "guid-2",
                "title": "More News",
                "link": "https://example.com/2",
                "summary": "Another summary",
                "published": "Mon, 17 Mar 2026 09:00:00 GMT",
            },
        ]
        mock_feed.feed = {"title": "Example Feed"}

        with patch("dashboard.services.news.feedparser.parse", return_value=mock_feed):
            headlines = fetch_news_headlines("https://feeds.example.com/rss")

        assert len(headlines) == 2
        assert headlines[0]["title"] == "Breaking News"
        assert headlines[0]["guid"] == "guid-1"
        assert headlines[0]["source_name"] == "Example Feed"
        assert isinstance(headlines[0]["published_at"], datetime)

    def test_handles_empty_feed(self):
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_feed.feed = {"title": "Empty Feed"}

        with patch("dashboard.services.news.feedparser.parse", return_value=mock_feed):
            headlines = fetch_news_headlines("https://feeds.example.com/rss")

        assert headlines == []

    def test_handles_bozo_malformed_feed(self):
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.entries = []
        mock_feed.bozo_exception = Exception("malformed XML")

        with patch("dashboard.services.news.feedparser.parse", return_value=mock_feed):
            headlines = fetch_news_headlines("https://feeds.example.com/rss")

        assert headlines == []

    def test_uses_explicit_source_name(self):
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                "id": "guid-1",
                "title": "Story",
                "link": "https://example.com/1",
                "summary": "",
                "published": "Mon, 17 Mar 2026 08:00:00 GMT",
            },
        ]
        mock_feed.feed = {"title": "Feed Title"}

        with patch("dashboard.services.news.feedparser.parse", return_value=mock_feed):
            headlines = fetch_news_headlines(
                "https://feeds.example.com/rss", source_name="Custom Name"
            )

        assert headlines[0]["source_name"] == "Custom Name"
