"""API views for the dashboard."""

from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CalendarEvent, NewsHeadline, StockQuote, UserDashboard, WeatherCache
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
        weather = WeatherCache.objects.first()
        if weather is None:
            return Response(
                {"detail": "No weather data available yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = WeatherCacheSerializer(weather)
        return Response(serializer.data)


class StocksView(APIView):
    """GET /api/stocks/ -- returns all cached stock quotes."""

    def get(self, request):
        quotes = StockQuote.objects.all().order_by("symbol")
        serializer = StockQuoteSerializer(quotes, many=True)
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
