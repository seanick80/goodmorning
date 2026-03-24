"""Shared HTTP utilities with retry and structured logging."""

from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger("dashboard.services")

# Status codes worth retrying — server overloaded or rate-limited
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def fetch_with_retry(
    url: str,
    *,
    params: dict | None = None,
    timeout: tuple[int, int] = (10, 30),
    max_retries: int = 3,
    backoff_base: float = 1.0,
) -> requests.Response:
    """GET with exponential backoff for transient failures.

    Args:
        url: The URL to fetch.
        params: Query parameters.
        timeout: (connect_timeout, read_timeout) in seconds.
        max_retries: Total attempts = 1 + max_retries.
        backoff_base: Initial sleep in seconds; doubles each retry.

    Returns:
        The successful Response object.

    Raises:
        requests.HTTPError: If all retries exhausted on HTTP errors.
        requests.ConnectionError: If all retries exhausted on connection failures.
        requests.Timeout: If all retries exhausted on timeouts.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                wait = backoff_base * (2 ** attempt)
                logger.warning(
                    "Retryable HTTP %d from %s (attempt %d/%d, waiting %.1fs)",
                    response.status_code,
                    url,
                    attempt + 1,
                    max_retries + 1,
                    wait,
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exception = exc
            if attempt < max_retries:
                wait = backoff_base * (2 ** attempt)
                logger.warning(
                    "%s fetching %s (attempt %d/%d, waiting %.1fs)",
                    type(exc).__name__,
                    url,
                    attempt + 1,
                    max_retries + 1,
                    wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "%s fetching %s — all %d attempts exhausted",
                    type(exc).__name__,
                    url,
                    max_retries + 1,
                )
                raise

        except requests.HTTPError:
            logger.error(
                "HTTP %d from %s — non-retryable",
                response.status_code,
                url,
            )
            raise

    # If we exit the loop via continue (retryable status, all retries used)
    logger.error(
        "HTTP %d from %s — all %d attempts exhausted",
        response.status_code,  # type: ignore[possibly-undefined]
        url,
        max_retries + 1,
    )
    response.raise_for_status()  # type: ignore[possibly-undefined]
    return response  # unreachable, but satisfies type checker
