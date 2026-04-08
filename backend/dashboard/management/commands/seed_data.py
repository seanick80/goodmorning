"""Management command to seed default development data."""

from datetime import time
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import (
    CalendarEvent,
    NewsHeadline,
    StockQuote,
    UserDashboard,
    WeatherCache,
)

DEFAULT_WIDGET_LAYOUT = [
    {
        "widget": "clock",
        "enabled": True,
        "position": 0,
        "panel": "left",
        "settings": {"format": "12h", "show_greeting": True},
    },
    {
        "widget": "weather",
        "enabled": True,
        "position": 1,
        "panel": "left",
        "settings": {"units": "fahrenheit", "latitude": 40.7128, "longitude": -74.006},
    },
    {
        "widget": "stocks",
        "enabled": True,
        "position": 0,
        "panel": "right",
        "settings": {"symbols": ["AAPL", "GOOGL", "MSFT"]},
    },
    {
        "widget": "calendar",
        "enabled": True,
        "position": 1,
        "panel": "right",
        "settings": {"google_calendar_ids": []},
    },
    {
        "widget": "wordoftheday",
        "enabled": False,
        "position": 2,
        "panel": "left",
        "settings": {"grade_level": 2},
    },
    {
        "widget": "news",
        "enabled": True,
        "position": 2,
        "panel": "right",
        "settings": {
            "sources": [
                {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
                {"name": "NPR", "url": "https://feeds.npr.org/1001/rss.xml"},
                {"name": "Reuters", "url": "https://feeds.reuters.com/rss/topNews"},
                {"name": "AP News", "url": "https://rsshub.app/apnews/topics/apf-topnews"},
                {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
                {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
            ],
            "rotation_interval": 30,
            "max_headlines": 20,
        },
    },
]


class Command(BaseCommand):
    help = "Seeds default data for development."

    def handle(self, *args, **options):
        # Create superuser
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "email": "admin@localhost",
            },
        )
        if created:
            user.set_password("admin")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        # Create dashboard
        dashboard, created = UserDashboard.objects.get_or_create(
            user=user,
            defaults={"widget_layout": DEFAULT_WIDGET_LAYOUT},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created default dashboard config."))
        else:
            self.stdout.write("Dashboard config already exists.")

        # Sample weather data
        now = timezone.now()
        WeatherCache.objects.update_or_create(
            location_key="40.71,-74.01",
            defaults={
                "latitude": 40.7128,
                "longitude": -74.006,
                "temperature": 72.5,
                "temperature_unit": "fahrenheit",
                "feels_like": 70.0,
                "humidity": 55,
                "wind_speed": 8.2,
                "wind_direction": 180,
                "weather_code": 1,
                "precipitation_probability": 10,
                "sunrise": time(6, 45),
                "sunset": time(19, 12),
                "daily_high": 78.0,
                "daily_low": 62.0,
                "hourly_forecast": [],
            },
        )
        self.stdout.write(self.style.SUCCESS("Seeded weather data."))

        # Sample stock quotes
        stocks = [
            ("AAPL", "Apple Inc.", "178.2300", "1.1500", "0.6500", "179.0000", "176.5000", "177.0000", "177.0800"),
            ("GOOGL", "Alphabet Inc.", "141.8000", "-0.4500", "-0.3200", "142.5000", "140.1000", "141.0000", "142.2500"),
            ("MSFT", "Microsoft Corp.", "415.6000", "3.2000", "0.7800", "417.0000", "412.0000", "413.0000", "412.4000"),
            ("AMZN", "Amazon.com Inc.", "185.6000", "2.3500", "1.2800", "186.5000", "183.2000", "184.0000", "183.2500"),
            ("TSLA", "Tesla Inc.", "175.4200", "-3.8000", "-2.1200", "179.0000", "174.5000", "178.5000", "179.2200"),
        ]
        for symbol, name, price, chg, chg_pct, high, low, opn, prev in stocks:
            StockQuote.objects.update_or_create(
                symbol=symbol,
                defaults={
                    "company_name": name,
                    "current_price": Decimal(price),
                    "change": Decimal(chg),
                    "change_percent": Decimal(chg_pct),
                    "day_high": Decimal(high),
                    "day_low": Decimal(low),
                    "open_price": Decimal(opn),
                    "previous_close": Decimal(prev),
                    "timestamp": now,
                },
            )
        self.stdout.write(self.style.SUCCESS("Seeded stock quotes."))

        # Sample calendar events
        CalendarEvent.objects.update_or_create(
            source_url="google:1",
            uid="standup-001",
            defaults={
                "title": "Team standup",
                "location": "Zoom",
                "start": now.replace(hour=9, minute=0, second=0, microsecond=0),
                "end": now.replace(hour=9, minute=15, second=0, microsecond=0),
                "all_day": False,
            },
        )
        CalendarEvent.objects.update_or_create(
            source_url="google:1",
            uid="review-001",
            defaults={
                "title": "Product review",
                "location": "Conf Room B",
                "start": now.replace(hour=14, minute=0, second=0, microsecond=0),
                "end": now.replace(hour=15, minute=0, second=0, microsecond=0),
                "all_day": False,
            },
        )
        CalendarEvent.objects.update_or_create(
            source_url="google:1",
            uid="lunch-001",
            defaults={
                "title": "Lunch with Sarah",
                "location": "Cafe Milo",
                "start": now.replace(hour=12, minute=0, second=0, microsecond=0),
                "end": now.replace(hour=13, minute=0, second=0, microsecond=0),
                "all_day": False,
            },
        )
        self.stdout.write(self.style.SUCCESS("Seeded calendar events."))

        # Sample news headlines
        headlines = [
            ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "bbc-001", "Major climate agreement reached at UN summit"),
            ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "bbc-002", "Scientists discover high-temperature superconductor"),
            ("NPR", "https://feeds.npr.org/1001/rss.xml", "npr-001", "Federal Reserve holds interest rates steady"),
            ("NPR", "https://feeds.npr.org/1001/rss.xml", "npr-002", "New study reveals benefits of urban green spaces"),
            ("Reuters", "https://feeds.reuters.com/rss/topNews", "reuters-001", "Tech stocks rally on strong earnings reports"),
        ]
        for source_name, source_url, guid, title in headlines:
            NewsHeadline.objects.update_or_create(
                source_url=source_url,
                guid=guid,
                defaults={
                    "source_name": source_name,
                    "title": title,
                    "link": f"https://example.com/{guid}",
                    "summary": f"Sample summary for: {title}",
                    "published_at": now,
                },
            )
        self.stdout.write(self.style.SUCCESS("Seeded news headlines."))

        self.stdout.write(self.style.SUCCESS("Seed data complete."))
