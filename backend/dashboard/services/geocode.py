"""Open-Meteo Geocoding API client for city search."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_locations(query: str, max_results: int = 5) -> list[dict]:
    """Search for cities/locations by name using Open-Meteo's free geocoding API.

    Returns a list of location dicts with name, country, latitude, longitude.
    """
    if not query or len(query) < 2:
        return []

    try:
        response = requests.get(
            GEOCODING_URL,
            params={"name": query, "count": max_results, "language": "en"},
            timeout=(5, 10),
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        logger.exception("Geocoding search failed for query: %s", query)
        return []

    results = []
    for item in data.get("results", []):
        admin1 = item.get("admin1", "")
        country = item.get("country", "")
        parts = [item.get("name", "")]
        if admin1:
            parts.append(admin1)
        if country:
            parts.append(country)

        results.append({
            "name": item.get("name", ""),
            "display_name": ", ".join(parts),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "country": country,
            "admin1": admin1,
        })

    return results
