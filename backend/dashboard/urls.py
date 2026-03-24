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
]
