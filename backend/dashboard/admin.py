"""Admin configuration for dashboard models."""

from django.contrib import admin

from .models import (
    CalendarEvent,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)


@admin.register(UserDashboard)
class UserDashboardAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ("location_key", "temperature", "weather_code", "fetched_at")
    readonly_fields = ("fetched_at",)


@admin.register(StockQuote)
class StockQuoteAdmin(admin.ModelAdmin):
    list_display = ("symbol", "current_price", "change", "change_percent", "fetched_at")
    readonly_fields = ("fetched_at",)


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "start", "end", "location", "fetched_at")
    readonly_fields = ("fetched_at",)


@admin.register(NewsHeadline)
class NewsHeadlineAdmin(admin.ModelAdmin):
    list_display = ("source_name", "title", "published_at", "fetched_at")
    readonly_fields = ("fetched_at",)
    list_filter = ("source_name",)
