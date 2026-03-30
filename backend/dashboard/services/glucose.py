"""Dexcom CGM client for glucose readings via the Share API."""

from __future__ import annotations

import logging

from pydexcom import Dexcom

logger = logging.getLogger(__name__)


def fetch_glucose_readings(
    username: str,
    password: str,
    region: str = "us",
    minutes: int = 180,
    max_count: int = 36,
) -> list[dict] | None:
    """Fetch recent glucose readings from Dexcom Share API.

    Args:
        username: Dexcom account email or phone number.
        password: Dexcom account password.
        region: "us", "ous" (outside US), or "jp" (Japan).
        minutes: How far back to fetch readings.
        max_count: Maximum number of readings to return.

    Returns:
        List of reading dicts, or None on failure.
    """
    try:
        dexcom = Dexcom(username=username, password=password)
        readings = dexcom.get_glucose_readings(minutes=minutes, max_count=max_count)
    except Exception:
        logger.exception("Failed to fetch Dexcom glucose readings")
        return None

    if not readings:
        return None

    return [
        {
            "value": r.value,
            "mmol_l": r.mmol_l,
            "trend_direction": r.trend_direction,
            "trend_arrow": r.trend_arrow,
            "recorded_at": r.datetime,
        }
        for r in readings
    ]
