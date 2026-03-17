"""Finnhub API client for stock quote data."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"


def fetch_stock_quote(symbol: str, api_key: str) -> dict | None:
    """Fetch a stock quote from Finnhub for the given symbol.

    Returns a dict suitable for StockQuote.objects.update_or_create(defaults=...),
    or None if the request fails or returns no data.
    """
    if not api_key:
        logger.warning("FINNHUB_API_KEY not set; skipping stock fetch for %s", symbol)
        return None

    try:
        response = requests.get(
            FINNHUB_QUOTE_URL,
            params={"symbol": symbol, "token": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        logger.exception("Failed to fetch stock quote for %s", symbol)
        return None

    # Finnhub returns c=0 when the symbol is invalid or market data unavailable
    if not data or data.get("c", 0) == 0:
        logger.warning("No quote data returned for %s", symbol)
        return None

    return {
        "current_price": data["c"],
        "change": data["d"],
        "change_percent": data["dp"],
        "day_high": data["h"],
        "day_low": data["l"],
        "open_price": data["o"],
        "previous_close": data["pc"],
        "timestamp": datetime.fromtimestamp(data.get("t", 0), tz=timezone.utc),
    }
