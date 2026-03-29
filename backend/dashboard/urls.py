"""URL patterns for the dashboard API."""

from django.urls import path

from . import views

urlpatterns = [
    path("weather/", views.WeatherView.as_view(), name="weather"),
    path("stocks/", views.StocksView.as_view(), name="stocks"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("news/", views.NewsView.as_view(), name="news"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("geocode/", views.GeocodeView.as_view(), name="geocode"),
    path("weather/location/", views.WeatherLocationView.as_view(), name="weather-location"),
    # Auth
    path("auth/status/", views.AuthStatusView.as_view(), name="auth-status"),
    path("auth/google/calendars/", views.GoogleCalendarListView.as_view(), name="google-calendars"),
    path("auth/google/photos/albums/", views.GooglePhotosAlbumsView.as_view(), name="google-photos-albums"),
]
