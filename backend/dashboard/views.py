"""API views for the dashboard."""

from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
