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
    path("auth/google/photos/picker/", views.PhotosPickerCreateView.as_view(), name="photos-picker-create"),
    path("auth/google/photos/picker/<str:session_id>/", views.PhotosPickerPollView.as_view(), name="photos-picker-poll"),
    path("auth/google/photos/picker/<str:session_id>/media/", views.PhotosPickerMediaView.as_view(), name="photos-picker-media"),
    path("photos/<int:index>/", views.PhotoProxyView.as_view(), name="photo-proxy"),
]
