"""Tests for the shared HTTP retry helper."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests
import requests_mock as rm

from dashboard.services._http import fetch_with_retry


class TestFetchWithRetry:
    def test_success_on_first_attempt(self):
        with rm.Mocker() as m:
            m.get("https://api.example.com/data", json={"ok": True})
            response = fetch_with_retry("https://api.example.com/data")

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_passes_params(self):
        with rm.Mocker() as m:
            m.get("https://api.example.com/data", json={"ok": True})
            fetch_with_retry(
                "https://api.example.com/data",
                params={"key": "value"},
            )

        assert "key=value" in m.last_request.url

    def test_raises_on_non_retryable_http_error(self):
        with rm.Mocker() as m:
            m.get("https://api.example.com/data", status_code=404)
            with pytest.raises(requests.HTTPError):
                fetch_with_retry("https://api.example.com/data")

        # Should only have made 1 request (no retry for 404)
        assert m.call_count == 1

    @patch("dashboard.services._http.time.sleep")
    def test_retries_on_503_then_succeeds(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                [
                    {"status_code": 503},
                    {"json": {"ok": True}},
                ],
            )
            response = fetch_with_retry(
                "https://api.example.com/data",
                max_retries=2,
                backoff_base=0.1,
            )

        assert response.status_code == 200
        assert m.call_count == 2
        mock_sleep.assert_called_once()

    @patch("dashboard.services._http.time.sleep")
    def test_retries_on_429_rate_limit(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                [
                    {"status_code": 429},
                    {"json": {"ok": True}},
                ],
            )
            response = fetch_with_retry(
                "https://api.example.com/data",
                max_retries=1,
                backoff_base=0.1,
            )

        assert response.status_code == 200
        assert m.call_count == 2

    @patch("dashboard.services._http.time.sleep")
    def test_retries_on_connection_error_then_succeeds(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                [
                    {"exc": requests.ConnectionError("refused")},
                    {"json": {"ok": True}},
                ],
            )
            response = fetch_with_retry(
                "https://api.example.com/data",
                max_retries=2,
                backoff_base=0.1,
            )

        assert response.status_code == 200
        assert m.call_count == 2

    @patch("dashboard.services._http.time.sleep")
    def test_retries_on_timeout_then_succeeds(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                [
                    {"exc": requests.Timeout("read timeout")},
                    {"json": {"ok": True}},
                ],
            )
            response = fetch_with_retry(
                "https://api.example.com/data",
                max_retries=1,
                backoff_base=0.1,
            )

        assert response.status_code == 200

    @patch("dashboard.services._http.time.sleep")
    def test_exhausts_retries_on_persistent_503(self, mock_sleep):
        with rm.Mocker() as m:
            m.get("https://api.example.com/data", status_code=503)
            with pytest.raises(requests.HTTPError):
                fetch_with_retry(
                    "https://api.example.com/data",
                    max_retries=2,
                    backoff_base=0.1,
                )

        # 1 initial + 2 retries = 3 total
        assert m.call_count == 3

    @patch("dashboard.services._http.time.sleep")
    def test_exhausts_retries_on_persistent_connection_error(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                exc=requests.ConnectionError("refused"),
            )
            with pytest.raises(requests.ConnectionError):
                fetch_with_retry(
                    "https://api.example.com/data",
                    max_retries=2,
                    backoff_base=0.1,
                )

        assert m.call_count == 3

    @patch("dashboard.services._http.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        with rm.Mocker() as m:
            m.get(
                "https://api.example.com/data",
                [
                    {"status_code": 503},
                    {"status_code": 503},
                    {"json": {"ok": True}},
                ],
            )
            fetch_with_retry(
                "https://api.example.com/data",
                max_retries=2,
                backoff_base=1.0,
            )

        # First retry: 1.0 * 2^0 = 1.0s, second: 1.0 * 2^1 = 2.0s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == pytest.approx(1.0)
        assert mock_sleep.call_args_list[1][0][0] == pytest.approx(2.0)
