"""API views for the dashboard."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from .models import (
    CalendarEvent,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)
from .serializers import (
    CalendarEventSerializer,
    NewsHeadlineSerializer,
    StockQuoteSerializer,
    UserDashboardSerializer,
    WeatherCacheSerializer,
)


class WeatherView(APIView):
    """GET /api/weather/ -- returns the latest cached weather data."""

    def get(self, request):
        # Get weather for the user's configured location
        location_name = ""
        try:
            user = User.objects.filter(is_superuser=True).first()
            if user and hasattr(user, "dashboard"):
                for widget in user.dashboard.widget_layout:
                    if widget.get("widget") == "weather":
                        lat = widget["settings"].get("latitude")
                        lon = widget["settings"].get("longitude")
                        location_name = widget["settings"].get("location_name", "")
                        if lat and lon:
                            key = f"{round(lat, 2)},{round(lon, 2)}"
                            weather = WeatherCache.objects.filter(location_key=key).first()
                            if weather:
                                data = WeatherCacheSerializer(weather).data
                                data["location_name"] = location_name
                                return Response(data)
        except Exception:
            pass

        weather = WeatherCache.objects.order_by("-fetched_at").first()
        if weather is None:
            return Response(
                {"detail": "No weather data available yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = WeatherCacheSerializer(weather)
        return Response(serializer.data)


class StocksView(APIView):
    """GET /api/stocks/ -- returns cached stock quotes for configured symbols."""

    def get(self, request):
        # Only return symbols the user has configured
        symbols = set()
        try:
            user = User.objects.filter(is_superuser=True).first()
            if user and hasattr(user, "dashboard"):
                for widget in user.dashboard.widget_layout:
                    if widget.get("widget") == "stocks":
                        symbols.update(widget["settings"].get("symbols", []))
        except Exception:
            pass

        qs = StockQuote.objects.all()
        if symbols:
            qs = qs.filter(symbol__in=symbols)
        serializer = StockQuoteSerializer(qs.order_by("symbol"), many=True)
        return Response(serializer.data)


class CalendarView(APIView):
    """GET /api/calendar/ -- returns today's calendar events."""

    def get(self, request):
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)
        events = CalendarEvent.objects.filter(
            start__gte=today_start,
            start__lt=today_end,
        ).order_by("start")
        serializer = CalendarEventSerializer(events, many=True)
        return Response(serializer.data)


class NewsView(APIView):
    """GET /api/news/ -- returns recent news headlines (max 20)."""

    def get(self, request):
        headlines = NewsHeadline.objects.all().order_by("-published_at")[:20]
        serializer = NewsHeadlineSerializer(headlines, many=True)
        return Response(serializer.data)


class DashboardView(APIView):
    """GET/PATCH /api/dashboard/ -- returns or updates dashboard config.

    In Phase 6.1 (single-user), always uses the first superuser's dashboard.
    """

    def _get_dashboard(self):
        user = User.objects.filter(is_superuser=True).first()
        if user is None:
            return None
        dashboard, _created = UserDashboard.objects.get_or_create(
            user=user,
            defaults={"widget_layout": []},
        )
        return dashboard

    def get(self, request):
        dashboard = self._get_dashboard()
        if dashboard is None:
            return Response(
                {"detail": "No dashboard configured. Run seed_data first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserDashboardSerializer(dashboard)
        return Response(serializer.data)

    def patch(self, request):
        dashboard = self._get_dashboard()
        if dashboard is None:
            return Response(
                {"detail": "No dashboard configured. Run seed_data first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserDashboardSerializer(dashboard, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GeocodeView(APIView):
    """GET /api/geocode/?q=hobart -- search cities by name."""

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])

        from .services.geocode import search_locations

        results = search_locations(query)
        return Response(results)


class WeatherLocationView(APIView):
    """POST /api/weather/location/ -- update weather location and fetch new data.

    Expects: {"latitude": float, "longitude": float, "location_name": str}
    """

    def post(self, request):
        lat = request.data.get("latitude")
        lon = request.data.get("longitude")
        location_name = request.data.get("location_name", "")

        if lat is None or lon is None:
            return Response(
                {"detail": "latitude and longitude are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update dashboard config
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            return Response(
                {"detail": "No user configured."},
                status=status.HTTP_404_NOT_FOUND,
            )

        dashboard, _ = UserDashboard.objects.get_or_create(
            user=user, defaults={"widget_layout": []}
        )

        # Find or create weather widget in layout
        found = False
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "weather":
                widget["settings"]["latitude"] = lat
                widget["settings"]["longitude"] = lon
                widget["settings"]["location_name"] = location_name
                found = True
                break

        if not found:
            dashboard.widget_layout.append({
                "widget": "weather",
                "enabled": True,
                "position": 1,
                "settings": {
                    "latitude": lat,
                    "longitude": lon,
                    "location_name": location_name,
                    "units": "fahrenheit",
                },
            })

        dashboard.save()

        # Fetch weather for the new location
        from .services.weather import fetch_weather_data

        location_key = f"{round(lat, 2)},{round(lon, 2)}"
        units = "fahrenheit"
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "weather":
                units = widget["settings"].get("units", "fahrenheit")
                break

        try:
            weather_data = fetch_weather_data(lat, lon, units=units)
            WeatherCache.objects.update_or_create(
                location_key=location_key,
                defaults={
                    "latitude": lat,
                    "longitude": lon,
                    **weather_data,
                },
            )
        except Exception:
            return Response(
                {"detail": "Location updated but weather fetch failed."},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response({"detail": "Location updated.", "location_key": location_key})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AuthStatusView(APIView):
    """GET /api/auth/status/ -- return current auth state."""

    def get(self, request: object) -> Response:
        if not request.user.is_authenticated:
            return Response({"authenticated": False})

        from allauth.socialaccount.models import SocialAccount, SocialToken

        google_account = (
            SocialAccount.objects.filter(
                user=request.user, provider="google"
            ).first()
        )

        data: dict = {
            "authenticated": True,
            "username": request.user.username,
            "email": request.user.email,
        }

        if google_account:
            data["google_connected"] = True
            data["google_email"] = google_account.extra_data.get("email", "")
            token = SocialToken.objects.filter(
                account=google_account
            ).first()
            data["has_refresh_token"] = bool(
                token and token.token_secret
            )
        else:
            data["google_connected"] = False

        return Response(data)


class GoogleCalendarListView(APIView):
    """GET /api/auth/google/calendars/ -- list user's Google calendars."""

    def get(self, request: object) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from .services.google_api import get_google_credentials

        credentials = get_google_credentials(request.user)
        if credentials is None:
            return Response(
                {"detail": "Google account not connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from googleapiclient.discovery import build

        try:
            service = build("calendar", "v3", credentials=credentials)
            result = service.calendarList().list().execute()
            calendars = [
                {
                    "id": cal["id"],
                    "summary": cal.get("summary", ""),
                    "primary": cal.get("primary", False),
                    "background_color": cal.get("backgroundColor", ""),
                }
                for cal in result.get("items", [])
            ]
            return Response(calendars)
        except Exception as exc:
            logger.exception("Failed to list Google calendars")
            return Response(
                {"detail": f"Google API error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class PhotosPickerCreateView(APIView):
    """POST /api/auth/google/photos/picker/ -- create a Picker session."""

    def post(self, request: object) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from .services.google_api import create_picker_session

        try:
            session = create_picker_session(request.user)
            if session is None:
                return Response(
                    {"detail": "Google account not connected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(session)
        except Exception as exc:
            logger.exception("Failed to create Photos Picker session")
            return Response(
                {"detail": f"Google API error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class PhotosPickerPollView(APIView):
    """GET /api/auth/google/photos/picker/<session_id>/ -- poll session status."""

    def get(self, request: object, session_id: str) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from .services.google_api import poll_picker_session

        try:
            result = poll_picker_session(request.user, session_id)
            if result is None:
                return Response(
                    {"detail": "Google account not connected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({
                "media_items_set": result.get("mediaItemsSet", False),
            })
        except Exception as exc:
            logger.exception("Failed to poll Picker session")
            return Response(
                {"detail": f"Google API error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class PhotosPickerMediaView(APIView):
    """GET /api/auth/google/photos/picker/<session_id>/media/ -- get picked photos."""

    def get(self, request: object, session_id: str) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from .services.google_api import fetch_picker_media_items

        try:
            items = fetch_picker_media_items(request.user, session_id)
            return Response(items)
        except Exception as exc:
            logger.exception("Failed to fetch Picker media items")
            return Response(
                {"detail": f"Google API error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class PhotoProxyView(APIView):
    """GET /api/photos/<index>/ -- proxy a cached Google Photos image.

    Streams the image through the backend since Picker API baseUrls
    require authentication and can't be loaded directly in the browser.
    """

    def get(self, request: object, index: int) -> HttpResponse:
        import requests as http_requests

        from .services.google_api import (
            fetch_picker_media_items,
            get_google_credentials,
        )

        user = User.objects.filter(is_superuser=True).first()
        if user is None or not hasattr(user, "dashboard"):
            return Response(
                {"detail": "No dashboard configured."},
                status=status.HTTP_404_NOT_FOUND,
            )

        dashboard = user.dashboard
        photos = []
        session_id = ""
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "photos":
                photos = widget.get("settings", {}).get("cached_media", [])
                session_id = widget.get("settings", {}).get(
                    "picker_session_id", ""
                )
                break

        if index < 0 or index >= len(photos):
            return Response(
                {"detail": "Photo not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from allauth.socialaccount.models import SocialAccount

        google_account = SocialAccount.objects.filter(
            provider="google",
        ).first()
        if not google_account:
            return Response(
                {"detail": "No Google account connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        credentials = get_google_credentials(google_account.user)
        if not credentials:
            return Response(
                {"detail": "Google credentials unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        width = request.query_params.get("w", "1920")
        height = request.query_params.get("h", "1080")
        base_url = photos[index].get("base_url", "")

        # Try cached URL first; if stale (403), refresh from Picker API
        if base_url:
            url = f"{base_url}=w{width}-h{height}"
            resp = http_requests.get(
                url,
                headers={"Authorization": f"Bearer {credentials.token}"},
                timeout=15,
            )
            if resp.status_code == 200:
                return HttpResponse(
                    resp.content,
                    content_type=resp.headers.get("Content-Type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=300"},
                )

        # Refresh URLs from Picker API
        if not session_id:
            return Response(
                {"detail": "No picker session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            fresh = fetch_picker_media_items(google_account.user, session_id)
            if fresh:
                # Update cache in DB
                for widget in dashboard.widget_layout:
                    if widget.get("widget") == "photos":
                        widget["settings"]["cached_media"] = fresh
                        break
                dashboard.save()
                photos = fresh

            if index >= len(photos):
                return Response(
                    {"detail": "Photo not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            base_url = photos[index].get("base_url", "")
            url = f"{base_url}=w{width}-h{height}"
            resp = http_requests.get(
                url,
                headers={"Authorization": f"Bearer {credentials.token}"},
                timeout=15,
            )
            resp.raise_for_status()
            return HttpResponse(
                resp.content,
                content_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=300"},
            )
        except Exception:
            logger.exception("Failed to proxy photo %d", index)
            return Response(
                {"detail": "Failed to fetch photo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
