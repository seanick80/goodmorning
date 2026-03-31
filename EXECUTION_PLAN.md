# Good Morning Dashboard -- Execution Plan (Phase 6.1: Windows Local Development)

**Date:** 2026-03-17
**Status:** Plan Complete
**Scope:** Initial version -- local Windows development with SQLite, PostgreSQL-ready architecture

---

## 1. Project Overview

The Good Morning Dashboard is a personal morning information display designed to run on a tablet, Raspberry Pi, or browser. It shows time, weather, stock quotes, calendar events, and news headlines in a single glanceable view. Each user has their own widget layout and configuration.

**Phase 6.1 scope (this plan):**

- Django backend with REST API serving cached data
- React frontend with polling-based widget updates
- Background scheduler fetching weather, stocks, and calendar data
- News headlines fetched via RSS feeds, cached hourly, rotated on screen
- SQLite for local development (PostgreSQL-ready via `dj-database-url`)
- Single-user focus (multi-user model in place but no auth UI yet)
- Django admin for configuration; no custom settings UI in React yet

**Out of scope for Phase 6.1 (completed separately):**

- ~~Docker Compose deployment~~ — PostgreSQL via Docker Compose for dev
- ~~PostgreSQL as active database~~ — PostgreSQL in all environments
- ~~Google OAuth / Calendar API integration~~ — **DONE** (django-allauth, Google Calendar + Photos Picker)
- PWA / kiosk mode
- WebSocket / SSE real-time updates
- ~~Raspberry Pi deployment~~ — **DONE** (Pi 5, native PostgreSQL + nginx + gunicorn)

---

## Completion Summary (as of 2026-03-31)

| Area | Status |
|------|--------|
| Core dashboard (weather, stocks, calendar, news, clock) | DONE |
| PostgreSQL (Docker dev, native Pi) | DONE |
| Raspberry Pi deployment (Pi 5, kiosk mode) | DONE |
| Google OAuth (django-allauth, Calendar + Photos) | DONE |
| Background photo slideshow (Google Photos Picker) | DONE |
| CSRF token handling in frontend | DONE |
| Test suite: 120+ backend + 22 frontend (vitest) | DONE |
| Slideshow crossfade + configurable interval | DONE |
| Dexcom glucose widget (CGM monitoring) | DONE |
| Photo frame mode (with dashboard flash) | DONE |
| Google OAuth token refresh fix | DONE |
| Calendar tomorrow events (smart threshold) | DONE |
| UI polish (stock links, calendar links, precip chart, names) | DONE |
| Configurable aux time zones (0-3, dropdown picker) | DONE |
| ICS calendar removal (Google Calendar only) | DONE |
| Deploy verification (pre-swap + post-deploy checks) | DONE |
| Deploy scp+tar extraction bug fix | DONE |
| Configurable news feeds + keywords | Backlog |
| Privacy policy page | Not started |

---

## 1A. UI Mock Phase (Pre-Implementation)

Before building functional components, generate 3-4 static layout mockups using React components with hardcoded data. This phase pauses for user review and feedback before proceeding with implementation.

### Purpose

- Explore different visual arrangements for the dashboard
- Validate the layout on actual target devices (tablet, browser, Pi display)
- Make layout decisions before investing in functional code
- Low cost to iterate: static components with no API calls or state management

### Mockup Variants

Each variant is a standalone React component importing from a shared `mockData.js` file. No API calls, no hooks, no state management -- pure presentational JSX + CSS.

| # | Layout Name | Description |
|---|-------------|-------------|
| 1 | **Grid** | Equal-sized cards in a responsive CSS Grid (2 columns on tablet, auto-fit on larger). Default layout. |
| 2 | **Hero + Sidebar** | Clock and weather occupy a large left panel (~60%). Stocks, calendar, and news stack vertically in a narrower right panel (~40%). |
| 3 | **Horizontal Bands** | Full-width horizontal rows. Clock bar at top, weather band, then stocks and calendar side-by-side, news ticker at bottom. |
| 4 | **Featured Card** | One large "featured" widget (weather with full forecast) centered. Smaller cards (clock, stocks, calendar, news) arranged around it. |

### Mock Data

```javascript
// frontend/src/components/mocks/mockData.js

export const mockWeather = {
  temperature: 72.5,
  temperature_unit: "fahrenheit",
  feels_like: 70.0,
  humidity: 55,
  weather_code: 1,
  weather_description: "Mainly Clear",
  daily_high: 78.0,
  daily_low: 62.0,
  sunrise: "06:45",
  sunset: "19:12",
};

export const mockStocks = [
  { symbol: "AAPL", current_price: "178.23", change: "1.15", change_percent: "0.65" },
  { symbol: "GOOGL", current_price: "141.80", change: "-0.45", change_percent: "-0.32" },
  { symbol: "MSFT", current_price: "415.60", change: "3.20", change_percent: "0.78" },
];

export const mockCalendar = [
  { title: "Team standup", start: "09:00", end: "09:15", location: "Zoom" },
  { title: "Product review", start: "14:00", end: "15:00", location: "Conf Room B" },
];

export const mockNews = [
  { source_name: "BBC News", title: "Major climate agreement reached at UN summit", published_at: "2h ago" },
  { source_name: "NPR", title: "Federal Reserve holds interest rates steady", published_at: "4h ago" },
  { source_name: "Reuters", title: "Tech stocks rally on strong earnings reports", published_at: "5h ago" },
];
```

### Switcher Component

A `MockSwitcher.jsx` component with tabs/buttons to switch between the 4 layouts. Each layout imports and arranges the same mock data differently.

### How to Use

1. Build the mock components (static JSX + CSS only)
2. Temporarily set `MockSwitcher` as the root component in `App.jsx`
3. Run `npm run dev` and open in the browser / target tablet
4. Review all 4 layouts, provide feedback on preferred direction
5. Once a layout is chosen, proceed with functional implementation using that layout's CSS structure
6. Delete the `mocks/` directory after the layout is finalized (or keep as a reference)

### Exit Criteria

- User has reviewed all layout variants on at least one target device
- A layout direction is chosen (may be a hybrid of multiple variants)
- Feedback incorporated into the CSS structure used for implementation

---

## 2. Code Layout

```
goodmorning/                          # Project root (git repo)
|-- backend/                          # Django project
|   |-- manage.py
|   |-- requirements.txt
|   |-- requirements-dev.txt
|   |-- .env.example
|   |-- goodmorning/                  # Django project package (settings, urls, wsgi)
|   |   |-- __init__.py
|   |   |-- settings.py
|   |   |-- urls.py
|   |   |-- wsgi.py
|   |   |-- asgi.py
|   |-- dashboard/                    # Main Django app
|   |   |-- __init__.py
|   |   |-- apps.py
|   |   |-- models.py                 # UserDashboard, WeatherCache, StockQuote, CalendarEvent, NewsHeadline
|   |   |-- serializers.py            # DRF serializers for all models
|   |   |-- views.py                  # DRF ViewSets and APIViews
|   |   |-- urls.py                   # /api/ route definitions
|   |   |-- admin.py                  # Admin registrations for all models
|   |   |-- jobs.py                   # APScheduler job functions (fetch_weather, fetch_stocks, fetch_calendar, fetch_news)
|   |   |-- scheduler.py             # Scheduler setup and registration
|   |   |-- services/                 # External API client modules
|   |   |   |-- __init__.py
|   |   |   |-- weather.py            # Open-Meteo API client
|   |   |   |-- stocks.py             # Finnhub API client
|   |   |   |-- calendar.py           # ICS feed parser
|   |   |   |-- news.py              # RSS feed parser (feedparser)
|   |   |-- management/
|   |   |   |-- commands/
|   |   |   |   |-- runapscheduler.py # Management command to start scheduler
|   |   |   |   |-- seed.py           # Seed default data for development
|   |   |-- migrations/
|   |   |-- tests/
|   |   |   |-- __init__.py
|   |   |   |-- test_models.py
|   |   |   |-- test_views.py
|   |   |   |-- test_serializers.py
|   |   |   |-- test_services.py      # Tests for external API clients (mocked)
|   |   |   |-- test_jobs.py          # Tests for scheduler jobs
|   |   |   |-- factories.py          # factory_boy factories
|   |   |   |-- conftest.py           # Shared pytest fixtures
|   |-- conftest.py                   # Root-level pytest config
|   |-- pytest.ini
|-- frontend/                         # React + Vite project
|   |-- package.json
|   |-- vite.config.js
|   |-- vitest.config.js
|   |-- index.html
|   |-- public/
|   |-- src/
|   |   |-- main.jsx                  # React entry point, QueryClient setup
|   |   |-- App.jsx                   # Root component, layout
|   |   |-- api/
|   |   |   |-- client.js             # Fetch wrapper (base URL, error handling)
|   |   |   |-- weather.js            # GET /api/weather/
|   |   |   |-- stocks.js             # GET /api/stocks/
|   |   |   |-- calendar.js           # GET /api/calendar/
|   |   |   |-- news.js              # GET /api/news/
|   |   |   |-- dashboard.js          # GET/PATCH /api/dashboard/
|   |   |-- hooks/
|   |   |   |-- useWeather.js         # TanStack Query hook for weather
|   |   |   |-- useStocks.js          # TanStack Query hook for stocks
|   |   |   |-- useCalendar.js        # TanStack Query hook for calendar
|   |   |   |-- useNews.js           # TanStack Query hook for news headlines
|   |   |   |-- useDashboard.js       # TanStack Query hook for dashboard config
|   |   |-- components/
|   |   |   |-- Dashboard.jsx         # Main dashboard grid layout
|   |   |   |-- widgets/
|   |   |   |   |-- ClockWidget.jsx   # Time + greeting display
|   |   |   |   |-- WeatherWidget.jsx # Current conditions + forecast
|   |   |   |   |-- StocksWidget.jsx  # Stock quotes with sparklines
|   |   |   |   |-- CalendarWidget.jsx# Today's events list
|   |   |   |   |-- NewsWidget.jsx   # Rotating news headlines display
|   |   |   |-- mocks/               # UI mock layout variations (Phase 1A)
|   |   |   |   |-- MockLayoutGrid.jsx
|   |   |   |   |-- MockLayoutHero.jsx
|   |   |   |   |-- MockLayoutBand.jsx
|   |   |   |   |-- MockLayoutFeatured.jsx
|   |   |   |   |-- MockSwitcher.jsx  # Tab bar to switch between layouts
|   |   |   |   |-- mockData.js       # Hardcoded sample data for all widgets
|   |   |   |-- WidgetCard.jsx        # Shared card wrapper (title, loading state, error)
|   |   |-- styles/
|   |   |   |-- index.css             # Global styles, CSS custom properties
|   |   |   |-- dashboard.module.css  # Dashboard grid layout
|   |   |   |-- widgets.module.css    # Widget-specific styles
|   |   |-- __tests__/
|   |   |   |-- setup.js              # Vitest setup (MSW server)
|   |   |   |-- mocks/
|   |   |   |   |-- handlers.js       # MSW request handlers
|   |   |   |   |-- server.js         # MSW setupServer
|   |   |   |-- components/
|   |   |   |   |-- ClockWidget.test.jsx
|   |   |   |   |-- WeatherWidget.test.jsx
|   |   |   |   |-- StocksWidget.test.jsx
|   |   |   |   |-- CalendarWidget.test.jsx
|   |   |   |   |-- NewsWidget.test.jsx
|   |   |   |-- hooks/
|   |   |   |   |-- useWeather.test.jsx
|-- docker-compose.yml                # For PostgreSQL phase (stubbed now)
|-- .env.example                      # Root-level env template
|-- .gitignore
|-- FRAMEWORK_ANALYSIS.md
|-- STORAGE_ANALYSIS.md
|-- EXECUTION_PLAN.md                 # This document
|-- README.md
```

**Key layout decisions:**

- **Monorepo with `backend/` and `frontend/` directories** -- keeps concerns separated while sharing a single git repo.
- **Single Django app (`dashboard`)** -- the domain is small enough that one app covering weather, stocks, calendar, news, and dashboard config is appropriate. Split into multiple apps only if the project grows significantly.
- **`services/` directory** -- isolates external API clients from Django views and scheduler jobs, making them independently testable with mocked HTTP responses.
- **CSS Modules** over MUI -- lighter weight for a dashboard with 4-5 widgets. MUI is 300+ KB gzipped and adds complexity disproportionate to the UI needs. CSS Grid + CSS Modules provide a responsive layout with minimal overhead.

---

## 3. Component Diagram

```
+------------------------------------------------------------------------+
|                           BROWSER / TABLET                              |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |  React App (Vite dev server :5173)                                |  |
|  |                                                                    |  |
|  |  +------------------+  +------------------+  +-----------------+  |  |
|  |  | ClockWidget      |  | WeatherWidget    |  | StocksWidget    |  |  |
|  |  | (client-side     |  | useWeather()     |  | useStocks()     |  |  |
|  |  |  useTime hook)   |  | poll: 5 min      |  | poll: 60s mkt   |  |  |
|  |  +------------------+  +------------------+  +-----------------+  |  |
|  |                                                                    |  |
|  |  +------------------+  +------------------+                      |  |
|  |  | CalendarWidget   |  | NewsWidget       |                      |  |
|  |  | useCalendar()    |  | useNews()        |                      |  |
|  |  | poll: 10 min     |  | poll: 5 min      |                      |  |
|  |  +------------------+  +------------------+                      |  |
|  |                                                                    |  |
|  |  +--------------------------------------+                          |  |
|  |  | Dashboard (CSS Grid layout)          |                          |  |
|  |  | useDashboard() for widget config     |                          |  |
|  |  +--------------------------------------+                          |  |
|  |                                                                    |  |
|  |  TanStack Query (QueryClient)  <--- manages cache + refetch       |  |
|  +---------|------|------|------|-------------------------------------+  |
|            |      |      |      |                                        |
+------------------------------------------------------------------------+
             |      |      |      |
     HTTP    |      |      |      |  (Vite proxy forwards /api/* to :8000)
             v      v      v      v
+------------------------------------------------------------------------+
|                    DJANGO BACKEND (:8000)                                |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |  Django REST Framework                                            |  |
|  |                                                                    |  |
|  |  GET /api/weather/     --> WeatherView     --> WeatherCache model  |  |
|  |  GET /api/stocks/      --> StocksView      --> StockQuote model    |  |
|  |  GET /api/calendar/    --> CalendarView    --> CalendarEvent model  |  |
|  |  GET /api/news/        --> NewsView        --> NewsHeadline model  |  |
|  |  GET /api/dashboard/   --> DashboardView   --> UserDashboard model |  |
|  |  PATCH /api/dashboard/ --> DashboardView   --> UserDashboard model |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |  Background Scheduler (django-apscheduler)                        |  |
|  |  Started via: python manage.py runapscheduler                     |  |
|  |                                                                    |  |
|  |  [every 15 min] fetch_weather_job()                               |  |
|  |      --> services/weather.py --> Open-Meteo API                    |  |
|  |      --> writes WeatherCache                                       |  |
|  |                                                                    |  |
|  |  [every 5 min, market hours] fetch_stocks_job()                   |  |
|  |      --> services/stocks.py --> Finnhub API                        |  |
|  |      --> writes StockQuote                                         |  |
|  |                                                                    |  |
|  |  [every 30 min] fetch_calendar_job()                              |  |
|  |      --> services/calendar.py --> ICS URL (HTTP GET)               |  |
|  |      --> writes CalendarEvent                                      |  |
|  |                                                                    |  |
|  |  [every 60 min] fetch_news_job()                                  |  |
|  |      --> services/news.py --> RSS feeds (feedparser)               |  |
|  |      --> writes NewsHeadline                                       |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |  SQLite Database (~/goodmorning-data/db.sqlite3)                  |  |
|  |                                                                    |  |
|  |  Tables:                                                           |  |
|  |  - dashboard_userdashboard  (1:1 with auth_user)                  |  |
|  |  - dashboard_weathercache   (latest + hourly forecast rows)       |  |
|  |  - dashboard_stockquote     (one row per tracked symbol)          |  |
|  |  - dashboard_calendarevent  (today's events from ICS)             |  |
|  |  - dashboard_newsheadline   (cached RSS news headlines)           |  |
|  |  - django_apscheduler_*     (APScheduler job state tables)        |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+------------------------------------------------------------------------+
             |              |              |
             v              v              v
      +------------+  +----------+  +-----------+
      | Open-Meteo |  | Finnhub  |  | ICS Feed  |
      | (no key)   |  | (API key)|  | (HTTP GET)|
      +------------+  +----------+  +-----------+

Data Flow Summary:
  1. Scheduler fetches external APIs on intervals --> writes to DB
  2. React polls Django REST endpoints --> reads cached data from DB
  3. Clock widget is pure client-side (no API call)
  4. Dashboard config loaded once, cached by TanStack Query
```

**Model Relationships:**

```
auth_user (Django built-in)
    |
    |-- 1:1 --> UserDashboard
                    |-- widget_layout (JSONField: list of widget configs)
                    |   Each entry: {widget, enabled, position, settings}

WeatherCache (standalone, shared across users)
    |-- location_key (lat,lon string)
    |-- current conditions fields
    |-- hourly forecast JSON
    |-- fetched_at timestamp

StockQuote (standalone, shared across users)
    |-- symbol (unique)
    |-- price, change, change_percent, etc.
    |-- fetched_at timestamp

CalendarEvent (standalone, per-user when multi-user is added)
    |-- source_url (ICS feed URL)
    |-- title, start, end, location, description
    |-- fetched_at timestamp
```

---

## 4. Storage Layer

### Django Models

```python
# backend/dashboard/models.py

from django.conf import settings
from django.db import models


class UserDashboard(models.Model):
    """Per-user dashboard configuration. One-to-one with User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard",
    )
    widget_layout = models.JSONField(
        default=list,
        help_text="Ordered list of widget configs: [{widget, enabled, position, settings}, ...]",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Dashboard"
        verbose_name_plural = "User Dashboards"

    def __str__(self):
        return f"Dashboard for {self.user.username}"


class WeatherCache(models.Model):
    """Cached weather data from Open-Meteo. One row per location."""

    location_key = models.CharField(
        max_length=50,
        unique=True,
        help_text="'lat,lon' string, e.g. '40.71,-74.01'",
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature = models.FloatField(help_text="Current temperature")
    temperature_unit = models.CharField(max_length=10, default="fahrenheit")
    feels_like = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True, help_text="Relative humidity %")
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.IntegerField(null=True, blank=True, help_text="Degrees")
    weather_code = models.IntegerField(
        help_text="WMO weather interpretation code (0=clear, 1-3=cloudy, etc.)"
    )
    precipitation_probability = models.IntegerField(null=True, blank=True)
    sunrise = models.TimeField(null=True, blank=True)
    sunset = models.TimeField(null=True, blank=True)
    hourly_forecast = models.JSONField(
        default=list,
        help_text="List of hourly data: [{time, temp, weather_code, precip_prob}, ...]",
    )
    daily_high = models.FloatField(null=True, blank=True)
    daily_low = models.FloatField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Weather Cache"
        verbose_name_plural = "Weather Cache"

    def __str__(self):
        return f"Weather at {self.location_key} ({self.temperature})"


class StockQuote(models.Model):
    """Cached stock quote from Finnhub. One row per symbol."""

    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200, blank=True, default="")
    current_price = models.DecimalField(max_digits=12, decimal_places=4)
    change = models.DecimalField(max_digits=12, decimal_places=4, help_text="Price change")
    change_percent = models.DecimalField(
        max_digits=8, decimal_places=4, help_text="Change %"
    )
    day_high = models.DecimalField(max_digits=12, decimal_places=4)
    day_low = models.DecimalField(max_digits=12, decimal_places=4)
    open_price = models.DecimalField(max_digits=12, decimal_places=4)
    previous_close = models.DecimalField(max_digits=12, decimal_places=4)
    timestamp = models.DateTimeField(help_text="Quote timestamp from Finnhub")
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock Quote"
        verbose_name_plural = "Stock Quotes"
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol}: ${self.current_price}"


class CalendarEvent(models.Model):
    """Cached calendar event from ICS feed."""

    source_url = models.URLField(help_text="ICS feed URL this event came from")
    uid = models.CharField(max_length=255, help_text="iCal UID for deduplication")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=500, blank=True, default="")
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Calendar Event"
        verbose_name_plural = "Calendar Events"
        ordering = ["start"]
        unique_together = [("source_url", "uid")]

    def __str__(self):
        return f"{self.title} ({self.start})"


class NewsHeadline(models.Model):
    """Cached news headline from RSS feed."""

    source_url = models.URLField(help_text="RSS feed URL this headline came from")
    source_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Display name for the source (e.g., 'BBC News')",
    )
    guid = models.CharField(
        max_length=500,
        help_text="RSS item guid/id for deduplication",
    )
    title = models.CharField(max_length=1000)
    link = models.URLField(max_length=2000, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication timestamp from the RSS feed",
    )
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "News Headline"
        verbose_name_plural = "News Headlines"
        ordering = ["-published_at"]
        unique_together = [("source_url", "guid")]

    def __str__(self):
        return f"{self.source_name}: {self.title[:80]}"
```

### Database Configuration

```python
# backend/goodmorning/settings.py (database section)

import dj_database_url
import os

DATA_DIR = os.environ.get(
    "GOODMORNING_DATA_DIR",
    os.path.expanduser("~/goodmorning-data"),
)
os.makedirs(DATA_DIR, exist_ok=True)

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{os.path.join(DATA_DIR, 'db.sqlite3')}",
    )
}

# SQLite optimizations (applied only when using SQLite)
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["init_command"] = (
        "PRAGMA journal_mode=wal;"
        "PRAGMA busy_timeout=5000;"
    )
    DATABASES["default"]["OPTIONS"]["transaction_mode"] = "IMMEDIATE"
```

To switch to PostgreSQL, set `DATABASE_URL=postgres://user:pass@host:5432/dbname` in `.env`. No code changes needed.

### Migration Strategy

1. Run `python manage.py makemigrations dashboard` after creating models
2. Run `python manage.py migrate` to apply
3. A data migration (`0002_seed_defaults.py`) creates a default superuser dashboard

### Seed Data (Development)

The `seed` management command creates:
- A superuser account (admin/admin) if none exists
- A `UserDashboard` with default widget layout (all widgets enabled, default stock symbols AAPL/GOOGL/MSFT, default weather location New York)
- Sample `WeatherCache`, `StockQuote`, `CalendarEvent`, and `NewsHeadline` rows so the dashboard renders without waiting for the scheduler

---

## 5. Backend Server

### Django Project Setup

**Python version:** 3.12+

**settings.py structure:**

```python
# backend/goodmorning/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-me")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_apscheduler",
    # Project
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Database (see section 4)
# ...

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Phase 6.1: no auth required
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}

# CORS (Vite dev server)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# APScheduler
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # seconds

# External API keys
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
```

### API Endpoints

**URL configuration:**

```python
# backend/goodmorning/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("dashboard.urls")),
]
```

```python
# backend/dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("weather/", views.WeatherView.as_view(), name="weather"),
    path("stocks/", views.StocksView.as_view(), name="stocks"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("news/", views.NewsView.as_view(), name="news"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/defaults/", views.DashboardDefaultsView.as_view(), name="dashboard-defaults"),
]
```

**Endpoint definitions:**

| Endpoint | Method | Description | Response Shape |
|----------|--------|-------------|----------------|
| `/api/weather/` | GET | Current weather + forecast | See below |
| `/api/stocks/` | GET | All tracked stock quotes | See below |
| `/api/calendar/` | GET | Today's calendar events | See below |
| `/api/news/` | GET | Cached news headlines | See below |
| `/api/dashboard/` | GET | Current dashboard config | See below |
| `/api/dashboard/` | PATCH | Update widget layout/settings | See below |
| `/api/dashboard/defaults/` | POST | Reset to default layout | `{status: "ok"}` |

**Response shapes:**

```json
// GET /api/weather/
{
  "location_key": "40.71,-74.01",
  "temperature": 72.5,
  "temperature_unit": "fahrenheit",
  "feels_like": 70.0,
  "humidity": 55,
  "wind_speed": 8.2,
  "weather_code": 1,
  "weather_description": "Mainly Clear",
  "precipitation_probability": 10,
  "sunrise": "06:45",
  "sunset": "19:12",
  "daily_high": 78.0,
  "daily_low": 62.0,
  "hourly_forecast": [
    {"time": "2026-03-17T08:00", "temp": 65, "weather_code": 0, "precip_prob": 5},
    {"time": "2026-03-17T09:00", "temp": 67, "weather_code": 1, "precip_prob": 5}
  ],
  "fetched_at": "2026-03-17T07:30:00Z"
}

// GET /api/stocks/
{
  "quotes": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "current_price": "178.2300",
      "change": "1.1500",
      "change_percent": "0.6500",
      "day_high": "179.0000",
      "day_low": "176.5000",
      "open_price": "177.0000",
      "previous_close": "177.0800",
      "fetched_at": "2026-03-17T15:30:00Z"
    }
  ]
}

// GET /api/calendar/
{
  "events": [
    {
      "uid": "abc123@google.com",
      "title": "Team standup",
      "start": "2026-03-17T09:00:00-04:00",
      "end": "2026-03-17T09:15:00-04:00",
      "location": "Conference Room B",
      "all_day": false
    }
  ],
  "fetched_at": "2026-03-17T07:00:00Z"
}

// GET /api/news/
{
  "headlines": [
    {
      "id": 1,
      "source_name": "BBC News",
      "title": "Major climate agreement reached at UN summit",
      "link": "https://www.bbc.com/news/...",
      "summary": "World leaders have agreed to...",
      "published_at": "2026-03-17T06:30:00Z"
    }
  ],
  "fetched_at": "2026-03-17T07:00:00Z"
}

// GET /api/dashboard/
{
  "widget_layout": [
    {"widget": "clock", "enabled": true, "position": 0, "settings": {"format": "12h", "show_greeting": true}},
    {"widget": "weather", "enabled": true, "position": 1, "settings": {"units": "fahrenheit", "latitude": 40.7128, "longitude": -74.006}},
    {"widget": "stocks", "enabled": true, "position": 2, "settings": {"symbols": ["AAPL", "GOOGL", "MSFT"]}},
    {"widget": "calendar", "enabled": true, "position": 3, "settings": {"ics_urls": []}},
    {"widget": "news", "enabled": true, "position": 4, "settings": {
        "sources": [
            {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
            {"name": "NPR", "url": "https://feeds.npr.org/1001/rss.xml"}
        ],
        "rotation_interval": 30,
        "max_headlines": 20
    }}
  ]
}

// PATCH /api/dashboard/
// Request body: partial update to widget_layout
{
  "widget_layout": [
    {"widget": "stocks", "enabled": true, "position": 2, "settings": {"symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"]}}
  ]
}
```

### Authentication Approach

Phase 6.1 uses `AllowAny` permissions -- no authentication required. The dashboard always operates as a single default user. This simplifies initial development.

Future phases will add:
1. Django session auth (login page for admin + dashboard)
2. Token-based auth (DRF TokenAuthentication or SimpleJWT) for API clients
3. Google OAuth (django-allauth) for Google Calendar integration

### CORS Configuration

The Vite dev server runs on `:5173` and the Django dev server on `:8000`. CORS headers allow cross-origin requests from Vite. In production (nginx reverse proxy), both are served from the same origin, so CORS is not needed.

---

## 6. Periodic Update Pipeline

### django-apscheduler Setup

**Installation:** `pip install django-apscheduler`

**How jobs start:** Via a dedicated management command `runapscheduler`, run in a separate terminal alongside `runserver`. This avoids the double-execution issue that occurs when starting the scheduler in `AppConfig.ready()` (which Django calls twice in dev due to the auto-reloader).

```python
# backend/dashboard/management/commands/runapscheduler.py

import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler import util

from dashboard.jobs import fetch_weather, fetch_stocks, fetch_calendar, fetch_news

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs APScheduler for periodic data fetching."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            fetch_weather,
            trigger=IntervalTrigger(minutes=15),
            id="fetch_weather",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_stocks,
            trigger=IntervalTrigger(minutes=5),
            id="fetch_stocks",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_calendar,
            trigger=IntervalTrigger(minutes=30),
            id="fetch_calendar",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            fetch_news,
            trigger=IntervalTrigger(minutes=60),
            id="fetch_news",
            max_instances=1,
            replace_existing=True,
        )

        logger.info("Starting scheduler...")
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully.")
```

### Job Definitions

```python
# backend/dashboard/jobs.py

import logging
from django.utils import timezone
from dashboard.services.weather import fetch_weather_data
from dashboard.services.stocks import fetch_stock_quotes
from dashboard.services.calendar import fetch_calendar_events
from dashboard.services.news import fetch_news_headlines
from dashboard.models import UserDashboard, WeatherCache, StockQuote, CalendarEvent, NewsHeadline

logger = logging.getLogger(__name__)


def fetch_weather():
    """Fetch weather for all configured locations."""
    dashboards = UserDashboard.objects.all()
    locations_fetched = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "weather" and widget.get("enabled"):
                lat = widget["settings"].get("latitude")
                lon = widget["settings"].get("longitude")
                if lat is None or lon is None:
                    continue
                location_key = f"{round(lat, 2)},{round(lon, 2)}"
                if location_key in locations_fetched:
                    continue
                try:
                    data = fetch_weather_data(lat, lon)
                    WeatherCache.objects.update_or_create(
                        location_key=location_key,
                        defaults={**data, "latitude": lat, "longitude": lon},
                    )
                    locations_fetched.add(location_key)
                    logger.info("Weather updated for %s", location_key)
                except Exception:
                    logger.exception("Failed to fetch weather for %s", location_key)


def fetch_stocks():
    """Fetch quotes for all tracked symbols."""
    dashboards = UserDashboard.objects.all()
    symbols = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "stocks" and widget.get("enabled"):
                symbols.update(widget["settings"].get("symbols", []))

    for symbol in symbols:
        try:
            data = fetch_stock_quotes(symbol)
            StockQuote.objects.update_or_create(
                symbol=symbol,
                defaults=data,
            )
            logger.info("Stock updated: %s = $%s", symbol, data["current_price"])
        except Exception:
            logger.exception("Failed to fetch stock quote for %s", symbol)


def fetch_calendar():
    """Fetch calendar events from all configured ICS feeds."""
    dashboards = UserDashboard.objects.all()
    urls_fetched = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "calendar" and widget.get("enabled"):
                for url in widget["settings"].get("ics_urls", []):
                    if url in urls_fetched:
                        continue
                    try:
                        events = fetch_calendar_events(url)
                        # Delete old events for this source, insert fresh
                        CalendarEvent.objects.filter(source_url=url).delete()
                        CalendarEvent.objects.bulk_create([
                            CalendarEvent(source_url=url, **event)
                            for event in events
                        ])
                        urls_fetched.add(url)
                        logger.info("Calendar updated from %s: %d events", url, len(events))
                    except Exception:
                        logger.exception("Failed to fetch calendar from %s", url)


def fetch_news():
    """Fetch news headlines from all configured RSS sources."""
    dashboards = UserDashboard.objects.all()
    source_urls = set()

    for dashboard in dashboards:
        for widget in dashboard.widget_layout:
            if widget.get("widget") == "news" and widget.get("enabled"):
                for source in widget["settings"].get("sources", []):
                    source_urls.add((source.get("name", ""), source["url"]))

    for source_name, url in source_urls:
        try:
            headlines = fetch_news_headlines(url)
            for headline in headlines:
                NewsHeadline.objects.update_or_create(
                    source_url=url,
                    guid=headline["guid"],
                    defaults={
                        "source_name": source_name,
                        "title": headline["title"],
                        "link": headline.get("link", ""),
                        "summary": headline.get("summary", ""),
                        "published_at": headline.get("published_at"),
                    },
                )
            logger.info("News updated from %s: %d headlines", url, len(headlines))
        except Exception:
            logger.exception("Failed to fetch news from %s", url)

    # Purge headlines older than 24 hours
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    deleted_count, _ = NewsHeadline.objects.filter(fetched_at__lt=cutoff).delete()
    if deleted_count:
        logger.info("Purged %d old news headlines", deleted_count)
```

### External API Service Modules

```python
# backend/dashboard/services/weather.py

import requests
from datetime import datetime

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_weather_data(latitude, longitude, units="fahrenheit"):
    """Fetch current weather and hourly forecast from Open-Meteo.

    Returns a dict suitable for WeatherCache.objects.update_or_create(defaults=...).
    """
    temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
    wind_unit = "mph" if units == "fahrenheit" else "kmh"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_direction_10m,"
                   "precipitation",
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "forecast_days": 1,
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    current = data["current"]
    daily = data["daily"]

    # Build hourly forecast list
    hourly = data.get("hourly", {})
    hourly_forecast = []
    for i, time_str in enumerate(hourly.get("time", [])):
        hourly_forecast.append({
            "time": time_str,
            "temp": hourly["temperature_2m"][i],
            "weather_code": hourly["weather_code"][i],
            "precip_prob": hourly.get("precipitation_probability", [None])[i],
        })

    sunrise_str = daily["sunrise"][0] if daily.get("sunrise") else None
    sunset_str = daily["sunset"][0] if daily.get("sunset") else None

    return {
        "temperature": current["temperature_2m"],
        "temperature_unit": units,
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "weather_code": current["weather_code"],
        "precipitation_probability": None,  # Current doesn't include this
        "sunrise": datetime.fromisoformat(sunrise_str).time() if sunrise_str else None,
        "sunset": datetime.fromisoformat(sunset_str).time() if sunset_str else None,
        "daily_high": daily["temperature_2m_max"][0] if daily.get("temperature_2m_max") else None,
        "daily_low": daily["temperature_2m_min"][0] if daily.get("temperature_2m_min") else None,
        "hourly_forecast": hourly_forecast,
    }
```

```python
# backend/dashboard/services/stocks.py

import requests
from datetime import datetime, timezone
from django.conf import settings

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def fetch_stock_quotes(symbol):
    """Fetch a single stock quote from Finnhub.

    Returns a dict suitable for StockQuote.objects.update_or_create(defaults=...).
    Finnhub response fields: c (current), d (change), dp (change %), h (high),
    l (low), o (open), pc (previous close), t (timestamp).
    """
    response = requests.get(
        f"{FINNHUB_BASE_URL}/quote",
        params={"symbol": symbol, "token": settings.FINNHUB_API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "current_price": data["c"],
        "change": data["d"],
        "change_percent": data["dp"],
        "day_high": data["h"],
        "day_low": data["l"],
        "open_price": data["o"],
        "previous_close": data["pc"],
        "timestamp": datetime.fromtimestamp(data["t"], tz=timezone.utc),
    }
```

```python
# backend/dashboard/services/calendar.py

import requests
from datetime import date, datetime, timezone
from icalendar import Calendar


def fetch_calendar_events(ics_url):
    """Fetch and parse an ICS feed, returning today's events.

    Returns a list of dicts suitable for CalendarEvent(**item).
    """
    response = requests.get(ics_url, timeout=15)
    response.raise_for_status()

    cal = Calendar.from_ical(response.text)
    today = date.today()
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("dtstart")
        if dtstart is None:
            continue
        start = dtstart.dt

        # Handle all-day events (date vs datetime)
        all_day = isinstance(start, date) and not isinstance(start, datetime)

        if all_day:
            if start != today:
                continue
            start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        else:
            if hasattr(start, "date") and start.date() != today:
                continue
            start_dt = start

        dtend = component.get("dtend")
        end_dt = None
        if dtend:
            end = dtend.dt
            if isinstance(end, date) and not isinstance(end, datetime):
                end_dt = datetime.combine(end, datetime.min.time(), tzinfo=timezone.utc)
            else:
                end_dt = end

        events.append({
            "uid": str(component.get("uid", "")),
            "title": str(component.get("summary", "Untitled")),
            "description": str(component.get("description", "")),
            "location": str(component.get("location", "")),
            "start": start_dt,
            "end": end_dt,
            "all_day": all_day,
        })

    return events
```

```python
# backend/dashboard/services/news.py

import logging
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)


def fetch_news_headlines(rss_url):
    """Fetch and parse an RSS feed, returning a list of headline dicts.

    Returns a list of dicts suitable for NewsHeadline.objects.update_or_create(defaults=...).
    Uses feedparser which handles RSS 2.0, Atom, and RDF feeds.
    """
    feed = feedparser.parse(rss_url)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Failed to parse RSS feed: {feed.bozo_exception}")

    headlines = []
    for entry in feed.entries:
        guid = entry.get("id") or entry.get("link") or entry.get("title", "")
        if not guid:
            continue

        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        headlines.append({
            "guid": guid[:500],
            "title": entry.get("title", "Untitled")[:1000],
            "link": entry.get("link", "")[:2000],
            "summary": entry.get("summary", ""),
            "published_at": published_at,
        })

    return headlines
```

### Error Handling for RSS Feeds

- `feedparser` handles malformed XML gracefully (sets `feed.bozo` flag). Only raise if the feed has no entries at all.
- Network errors (DNS, timeout) from `feedparser.parse()` with a URL are caught by the job's try/except.
- Missing fields (guid, pubDate) are handled with fallbacks -- guid falls back to link or title.
- Feed entries without any usable guid are skipped silently.

### Error Handling and Retry Logic

- Each job wraps individual API calls in try/except, logging failures without crashing the scheduler.
- `max_instances=1` prevents overlapping executions if a job runs long.
- The scheduler itself runs in a `BlockingScheduler` (separate process from Django), so a job failure does not affect the web server.
- Rate limit awareness: Finnhub allows 60 calls/minute. With 5-20 tracked symbols fetched every 5 minutes, usage stays well under the limit. If more symbols are needed, batch them with a small delay between calls.
- Open-Meteo allows 600 calls/minute -- no concern for a personal dashboard.
- No automatic retry on failure. The next scheduled execution (5-30 minutes later) will retry. For a morning dashboard, this is sufficient.

---

## 7. Frontend Framework

### React + Vite Setup

**Node.js version:** 20.x LTS or later

**Project creation:**
```bash
cd goodmorning/frontend
npm create vite@latest . -- --template react
```

**vite.config.js:**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

The proxy configuration lets the React dev server forward `/api/*` requests to Django, eliminating CORS issues during development and mirroring the production nginx setup.

### TanStack Query Configuration

```javascript
// frontend/src/main.jsx

import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles/index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,          // Data is fresh for 1 minute
      retry: 2,                       // Retry failed requests twice
      refetchOnWindowFocus: true,     // Refetch when tab regains focus
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**Per-widget polling intervals:**

| Widget | `refetchInterval` | Rationale |
|--------|-------------------|-----------|
| Weather | `5 * 60 * 1000` (5 min) | Server updates every 15 min; 5 min ensures freshness |
| Stocks | `60 * 1000` (1 min) | Server updates every 5 min; 1 min for responsiveness |
| Calendar | `10 * 60 * 1000` (10 min) | Server updates every 30 min; 10 min is sufficient |
| News | `5 * 60 * 1000` (5 min) | Server updates every 60 min; 5 min ensures freshness |
| Dashboard config | None (manual refetch only) | Changes only on user action |

### Routing

No client-side routing. This is a single-page dashboard. If a settings page is added later, use React Router with two routes: `/` (dashboard) and `/settings`.

### State Management

TanStack Query handles all server state. No additional state management library (Redux, Zustand) is needed. Local UI state (e.g., clock format toggle) uses React `useState`.

### API Service Layer

```javascript
// frontend/src/api/client.js

const BASE_URL = "/api";

async function apiFetch(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = new Error(`API error: ${response.status} ${response.statusText}`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export function fetchWeather() {
  return apiFetch("/weather/");
}

export function fetchStocks() {
  return apiFetch("/stocks/");
}

export function fetchCalendar() {
  return apiFetch("/calendar/");
}

export function fetchNews() {
  return apiFetch("/news/");
}

export function fetchDashboard() {
  return apiFetch("/dashboard/");
}

export function updateDashboard(data) {
  return apiFetch("/dashboard/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
```

### Layout Approach

CSS Grid for the dashboard layout. CSS Modules for component-scoped styles. CSS custom properties (variables) for theming (dark mode later).

```css
/* frontend/src/styles/dashboard.module.css */

.dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* On tablets (768px+), 2 columns */
@media (min-width: 768px) {
  .dashboard {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* On large screens, clock spans full width */
.clockWidget {
  grid-column: 1 / -1;
}
```

---

## 8. Initial Widget Inclusion

### Clock Widget

**Approach:** Custom component (no external package needed).

A digital clock with greeting is trivial to build and does not warrant a dependency. A `useEffect` with `setInterval(1000)` updates the time every second. The greeting message changes based on the hour (Good Morning / Good Afternoon / Good Evening).

**Data flow:** Pure client-side. No API call.

**Implementation notes:**
- Display format configurable via dashboard settings (`12h` or `24h`)
- Show the current date (e.g., "Monday, March 17, 2026")
- Use `Intl.DateTimeFormat` for locale-aware formatting
- Greeting based on hour: Morning (5-12), Afternoon (12-17), Evening (17-5)

### Weather Widget

**Approach:** Custom component. No existing package fits well.

**Evaluated packages:**
- `@daniel-szulc/react-weather-widget` -- fetches its own data from Open-Meteo or OpenWeather. This conflicts with our architecture where Django caches weather data and serves it via REST API. We would need to bypass the widget's built-in fetching, which defeats its purpose.
- `react-open-weather` -- same issue: expects to make its own API calls to OpenWeather.

**Why custom:** Weather widgets on npm are designed as self-contained components that call weather APIs directly. Our architecture has Django as the data layer, so we need a presentational component that accepts weather data as props. This is straightforward to build.

**Data flow:** `useWeather()` hook (TanStack Query) polls `GET /api/weather/` every 5 minutes. Data passed as props to `WeatherWidget`.

**Implementation notes:**
- Display: current temp (large), feels like, high/low, humidity, wind, weather description
- WMO weather code mapped to an icon (use emoji or a small icon set like `weather-icons` CSS font)
- Sunrise/sunset times
- Hourly forecast as a simple row of temp + icon for next 6-8 hours

### Stocks Widget

**Approach:** Custom component for the quote list + `recharts` for optional sparklines.

**Evaluated packages:**
- `lightweight-charts` (TradingView) -- full candlestick/OHLC chart library (45 KB). Excellent for a dedicated stock chart page, but overkill for a dashboard widget showing 3-5 stock quotes. Also requires TradingView attribution.
- `recharts` -- general-purpose React chart library built on D3. Its `<Sparkline>` or `<LineChart>` component can render a small price trend line. Lightweight for the dashboard use case.
- `react-sparklines` -- dedicated sparkline library, very lightweight. Good alternative to recharts if only sparklines are needed.

**Recommendation:** Start with a simple table/list of quotes (symbol, price, change, change%). Add `recharts` sparklines in a later iteration if historical price data is collected (currently Finnhub free tier provides only the latest quote, not historical data).

**Data flow:** `useStocks()` hook polls `GET /api/stocks/` every 60 seconds. Renders a list of `StockQuote` items.

**Implementation notes:**
- Display: symbol, current price, change (+ or -), change percent
- Color coding: green for positive change, red for negative
- Market status indicator (open/closed based on time)

### Calendar Widget

**Approach:** Custom component. The full calendar libraries are designed for month/week views, not a simple "today's events" list.

**Evaluated packages:**
- `react-big-calendar` -- full-featured month/week/day calendar view. Far too heavy for showing today's event list on a dashboard. Would be appropriate if we wanted a full calendar page.
- `react-calendar` -- a date picker, not an event display component.
- `react-event-calendar` -- month view with event indicators. Not what we need.

**Why custom:** Dashboard calendars show a vertical list of today's events sorted by time. This is a simple `<ul>` with styled list items, not a calendar grid.

**Data flow:** `useCalendar()` hook polls `GET /api/calendar/` every 10 minutes. Renders a sorted list of events.

**Implementation notes:**
- Display: time (or "All Day"), title, location (if present)
- Events sorted by start time, all-day events first
- Current/upcoming event highlighted
- Empty state: "No events today"

### News Widget

**Approach:** Custom component. Uses `feedparser` on the backend to parse RSS feeds from BBC News, NPR, Reuters, and other configurable sources. No API key required -- RSS feeds are free and publicly available.

**Data flow:** `useNews()` hook (TanStack Query) polls `GET /api/news/` every 5 minutes. The backend scheduler fetches and caches RSS headlines every 60 minutes. The widget rotates through cached headlines on a configurable interval.

**Implementation notes:**
- Display: source name, headline title, publication time (relative, e.g., "2h ago")
- Headline rotation: `useEffect` + `setInterval(30000)` cycles through headlines with a CSS opacity transition
- Configurable: sources (RSS feed URLs), rotation interval (seconds), max headlines to display
- Empty state: "No news available" when no headlines are cached
- Click behavior: headline links open in a new tab

### Summary of External Widget Dependencies

| Widget | External Package | Rationale |
|--------|-----------------|-----------|
| Clock | None | Trivial to build, no dependency needed |
| Weather | None | Existing packages fetch their own data; incompatible with Django cache architecture |
| Stocks | `recharts` (optional, later) | Only if historical sparklines are added |
| Calendar | None | A simple event list does not need a calendar library |
| News | None (`feedparser` on backend only) | RSS parsing is backend-side; frontend is a simple presentational component |

---

## 9. Unit and Integration Tests

### Backend Testing Stack

**Packages:**
```
pytest==8.*
pytest-django==4.*
factory-boy==3.*
requests-mock==1.*
```

**pytest.ini:**
```ini
# backend/pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = goodmorning.settings
python_files = tests.py test_*.py
python_classes = Test*
python_functions = test_*
```

**conftest.py:**
```python
# backend/conftest.py
import pytest
from django.contrib.auth.models import User
from dashboard.models import UserDashboard


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def dashboard(user):
    return UserDashboard.objects.create(
        user=user,
        widget_layout=[
            {"widget": "clock", "enabled": True, "position": 0, "settings": {"format": "12h"}},
            {"widget": "weather", "enabled": True, "position": 1, "settings": {"latitude": 40.71, "longitude": -74.01, "units": "fahrenheit"}},
            {"widget": "stocks", "enabled": True, "position": 2, "settings": {"symbols": ["AAPL", "MSFT"]}},
            {"widget": "calendar", "enabled": True, "position": 3, "settings": {"ics_urls": []}},
        ],
    )
```

**Test categories:**

1. **Model tests** (`test_models.py`):
   - `UserDashboard` creation with default layout
   - `WeatherCache.update_or_create` with location_key
   - `StockQuote` uniqueness on symbol
   - `CalendarEvent` ordering by start time
   - `CalendarEvent` unique_together on (source_url, uid)

2. **API endpoint tests** (`test_views.py`):
   - `GET /api/weather/` returns cached weather data
   - `GET /api/weather/` returns empty response when no cache exists
   - `GET /api/stocks/` returns all quotes ordered by symbol
   - `GET /api/calendar/` returns today's events only
   - `GET /api/dashboard/` returns user's widget layout
   - `PATCH /api/dashboard/` updates widget settings
   - `POST /api/dashboard/defaults/` resets layout

3. **Service tests** (`test_services.py`) -- external APIs mocked with `requests-mock`:
   - `fetch_weather_data()` parses Open-Meteo response correctly
   - `fetch_weather_data()` raises on HTTP error
   - `fetch_weather_data()` handles missing optional fields
   - `fetch_stock_quotes()` maps Finnhub fields correctly
   - `fetch_stock_quotes()` raises on invalid symbol
   - `fetch_calendar_events()` parses ICS with multiple events
   - `fetch_calendar_events()` filters to today's events only
   - `fetch_calendar_events()` handles all-day events

4. **Scheduler job tests** (`test_jobs.py`) -- services mocked:
   - `fetch_weather()` updates WeatherCache for configured locations
   - `fetch_weather()` skips duplicate locations across users
   - `fetch_stocks()` aggregates symbols across all dashboards
   - `fetch_stocks()` logs and continues on individual symbol failure
   - `fetch_calendar()` replaces old events with fresh data
   - `fetch_news()` deduplicates source URLs across dashboards
   - `fetch_news()` uses update_or_create by (source_url, guid)
   - `fetch_news()` purges headlines older than 24 hours

5. **News service tests** (`test_services.py` additions):
   - `fetch_news_headlines()` parses RSS feed with multiple items
   - `fetch_news_headlines()` handles missing optional fields (guid, pubDate)
   - `fetch_news_headlines()` raises on HTTP error
   - `fetch_news_headlines()` returns empty list for empty feed

6. **News model tests** (`test_models.py` additions):
   - `NewsHeadline` creation with all fields
   - `NewsHeadline` unique_together on (source_url, guid)
   - `NewsHeadline` ordering by -published_at

7. **News API view tests** (`test_views.py` additions):
   - `GET /api/news/` returns cached headlines
   - `GET /api/news/` returns empty list when no headlines exist

**Factories:**

```python
# backend/dashboard/tests/factories.py

import factory
from django.contrib.auth.models import User
from dashboard.models import UserDashboard, WeatherCache, StockQuote, CalendarEvent, NewsHeadline
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "testpass")


class WeatherCacheFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WeatherCache

    location_key = "40.71,-74.01"
    latitude = 40.71
    longitude = -74.01
    temperature = 72.5
    weather_code = 0
    hourly_forecast = []


class StockQuoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockQuote

    symbol = factory.Sequence(lambda n: f"SYM{n}")
    current_price = 150.00
    change = 1.50
    change_percent = 1.01
    day_high = 152.00
    day_low = 148.00
    open_price = 149.00
    previous_close = 148.50
    timestamp = factory.LazyFunction(timezone.now)


class NewsHeadlineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsHeadline

    source_url = "https://feeds.bbci.co.uk/news/rss.xml"
    source_name = "BBC News"
    guid = factory.Sequence(lambda n: f"guid-{n}")
    title = factory.Sequence(lambda n: f"News headline {n}")
    link = factory.LazyAttribute(lambda o: f"https://www.bbc.com/news/{o.guid}")
    summary = "A test news headline summary."
    published_at = factory.LazyFunction(timezone.now)
```

### Frontend Testing Stack

**Packages:**
```json
{
  "devDependencies": {
    "vitest": "^3.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "msw": "^2.0.0",
    "jsdom": "^25.0.0"
  }
}
```

**vitest.config.js:**
```javascript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.js"],
    globals: true,
  },
});
```

**MSW setup:**

```javascript
// frontend/src/__tests__/mocks/handlers.js

import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/weather/", () => {
    return HttpResponse.json({
      location_key: "40.71,-74.01",
      temperature: 72.5,
      temperature_unit: "fahrenheit",
      weather_code: 0,
      weather_description: "Clear sky",
      daily_high: 78,
      daily_low: 62,
      hourly_forecast: [],
      fetched_at: "2026-03-17T07:30:00Z",
    });
  }),

  http.get("/api/stocks/", () => {
    return HttpResponse.json({
      quotes: [
        {
          symbol: "AAPL",
          current_price: "178.23",
          change: "1.15",
          change_percent: "0.65",
        },
      ],
    });
  }),

  http.get("/api/calendar/", () => {
    return HttpResponse.json({
      events: [],
      fetched_at: "2026-03-17T07:00:00Z",
    });
  }),

  http.get("/api/news/", () => {
    return HttpResponse.json({
      headlines: [
        {
          id: 1,
          source_name: "BBC News",
          title: "Major climate agreement reached at UN summit",
          link: "https://www.bbc.com/news/climate-123",
          summary: "World leaders have agreed to...",
          published_at: "2026-03-17T06:30:00Z",
        },
      ],
      fetched_at: "2026-03-17T07:00:00Z",
    });
  }),

  http.get("/api/dashboard/", () => {
    return HttpResponse.json({
      widget_layout: [
        { widget: "clock", enabled: true, position: 0, settings: { format: "12h" } },
        { widget: "weather", enabled: true, position: 1, settings: {} },
        { widget: "stocks", enabled: true, position: 2, settings: { symbols: ["AAPL"] } },
        { widget: "calendar", enabled: true, position: 3, settings: {} },
        { widget: "news", enabled: true, position: 4, settings: { sources: [{ name: "BBC News", url: "https://feeds.bbci.co.uk/news/rss.xml" }], rotation_interval: 30, max_headlines: 20 } },
      ],
    });
  }),
];
```

```javascript
// frontend/src/__tests__/mocks/server.js
import { setupServer } from "msw/node";
import { handlers } from "./handlers";
export const server = setupServer(...handlers);
```

```javascript
// frontend/src/__tests__/setup.js
import "@testing-library/jest-dom";
import { server } from "./mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

**Frontend test categories:**

1. **Widget rendering tests:**
   - `ClockWidget` renders current time and greeting
   - `WeatherWidget` renders temperature, conditions, and forecast
   - `WeatherWidget` shows loading state
   - `WeatherWidget` shows error state on API failure
   - `StocksWidget` renders list of quotes with correct colors
   - `CalendarWidget` renders event list sorted by time
   - `CalendarWidget` shows "No events" empty state
   - `NewsWidget` renders headline and source name
   - `NewsWidget` rotates to next headline after interval
   - `NewsWidget` wraps around to first headline after last
   - `NewsWidget` shows empty state when no headlines
   - `NewsWidget` shows loading state

2. **Hook tests:**
   - `useWeather` returns data from API
   - `useStocks` refetches at configured interval
   - Custom MSW overrides for error scenarios

### CI Considerations

Not implemented in Phase 6.1, but the test setup is CI-ready:
- `cd backend && python -m pytest` for backend
- `cd frontend && npx vitest run` for frontend
- Both commands exit non-zero on failure
- No external service dependencies (all APIs mocked)

---

## 10. Debug Logging

### Django Logging Configuration

```python
# backend/goodmorning/settings.py (LOGGING section)

import os

LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "DEBUG",
        },
        "file_general": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "goodmorning.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 3,
            "formatter": "verbose",
            "level": "INFO",
        },
        "file_scheduler": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "scheduler.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
            "level": "DEBUG",
        },
        "file_errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "errors.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_general"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file_general", "file_errors"],
            "level": "INFO",
            "propagate": False,
        },
        "dashboard": {
            "handlers": ["console", "file_general"],
            "level": "DEBUG",
            "propagate": False,
        },
        "dashboard.jobs": {
            "handlers": ["console", "file_scheduler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "dashboard.services": {
            "handlers": ["console", "file_scheduler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apscheduler": {
            "handlers": ["console", "file_scheduler"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_general", "file_errors"],
        "level": "WARNING",
    },
}
```

**Log files produced:**

| File | Contents | Rotation |
|------|----------|----------|
| `~/goodmorning-data/logs/goodmorning.log` | General application log (INFO+) | 5 MB x 3 backups |
| `~/goodmorning-data/logs/scheduler.log` | Scheduler jobs + external API calls (DEBUG+) | 5 MB x 3 backups |
| `~/goodmorning-data/logs/errors.log` | Errors only from all modules | 5 MB x 5 backups |

### Scheduler Job Logging

Each job function logs:
- Job start: `"Fetching weather for 40.71,-74.01"`
- Success: `"Weather updated for 40.71,-74.01"` (with duration if useful)
- External API response codes: logged at DEBUG level
- Failures: `logger.exception(...)` captures full traceback

### Frontend Logging

Phase 6.1 uses `console.log/warn/error` in development. No remote logging. TanStack Query's `onError` callbacks log API failures to the console.

Future: Add a lightweight error boundary that catches rendering errors and displays a fallback UI per widget.

---

## 11. Deployment Process (Local Windows)

### Step-by-Step Setup from Fresh Clone

```bash
# 1. Clone the repository
git clone <repo-url> c:/sourcecode/goodmorning
cd c:/sourcecode/goodmorning

# 2. Create Python virtual environment
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows

# 3. Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install frontend dependencies
cd ../frontend
npm install

# 5. Environment setup
cd ..
cp .env.example .env
# Edit .env: set FINNHUB_API_KEY (required for stocks)
# All other values have working defaults for local dev

# 6. Database migration
cd backend
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser
# Or use the seed command which creates admin/admin:
python manage.py seed

# 8. Start backend (Terminal 1)
python manage.py runserver

# 9. Start scheduler (Terminal 2)
cd backend
source .venv/Scripts/activate
python manage.py runapscheduler

# 10. Start frontend (Terminal 3)
cd frontend
npm run dev

# Dashboard is now at: http://localhost:5173
# Django admin at: http://localhost:8000/admin/
```

### .env.example

```bash
# Django
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (leave unset for SQLite default)
# DATABASE_URL=postgres://user:pass@localhost:5432/goodmorning_db

# Data directory (leave unset for ~/goodmorning-data)
# GOODMORNING_DATA_DIR=c:/path/to/data

# External APIs
FINNHUB_API_KEY=your_finnhub_api_key_here

# Weather defaults (can also be configured per-user in admin)
DEFAULT_WEATHER_LAT=40.7128
DEFAULT_WEATHER_LON=-74.0060
```

### Automation Scripts

Create a `scripts/` directory in the project root:

```bash
# scripts/dev-backend.sh -- Start Django dev server
#!/bin/bash
cd "$(dirname "$0")/../backend"
source .venv/Scripts/activate
python manage.py runserver
```

```bash
# scripts/dev-scheduler.sh -- Start background scheduler
#!/bin/bash
cd "$(dirname "$0")/../backend"
source .venv/Scripts/activate
python manage.py runapscheduler
```

```bash
# scripts/dev-frontend.sh -- Start Vite dev server
#!/bin/bash
cd "$(dirname "$0")/../frontend"
npm run dev
```

```bash
# scripts/dev-all.sh -- Start all three services
#!/bin/bash
# Start backend and scheduler in background, frontend in foreground
DIR="$(dirname "$0")"
"$DIR/dev-backend.sh" &
"$DIR/dev-scheduler.sh" &
"$DIR/dev-frontend.sh"
```

### requirements.txt

```
django>=5.2,<6.0
djangorestframework>=3.15
django-apscheduler>=0.7
django-cors-headers>=4.0
dj-database-url>=2.0
python-dotenv>=1.0
requests>=2.31
icalendar>=6.0
feedparser>=6.0
psycopg[binary]>=3.1
```

### requirements-dev.txt

```
pytest>=8.0
pytest-django>=4.8
factory-boy>=3.3
requests-mock>=1.12
```

### frontend/package.json (key dependencies)

```json
{
  "name": "goodmorning-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^6.0.0",
    "vite": "^8.0.0",
    "vitest": "^3.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "msw": "^2.0.0",
    "jsdom": "^25.0.0"
  }
}
```

---

## 12. Install Package Creation

### Phase 6.1: Script-Based Installation

For Phase 6.1 (local Windows dev), the setup script in Section 11 is sufficient. No packaging beyond the git repository.

### Phase 6.2+: Docker Compose

The production packaging strategy is Docker Compose, which bundles Django, React (built), and PostgreSQL into a single `docker compose up`:

**Multi-stage Dockerfile:**

```dockerfile
# goodmorning/Dockerfile (conceptual)

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + built frontend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/staticfiles/frontend

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "goodmorning.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50"]
```

### .env.example Template

See Section 11 above.

### Minimum System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.12+ | 3.12+ |
| Node.js | 20.x LTS | 20.x LTS |
| RAM | 512 MB | 1 GB |
| Disk | 500 MB | 1 GB |
| OS | Windows 10+, macOS 12+, Linux | Windows 11, Ubuntu 22.04+ |

---

## 13. Future Work

### Near-Term (Phase 6.2 - 6.3) — DONE

- ~~**PostgreSQL migration:**~~ PostgreSQL via Docker Compose for dev, native on Pi.
- ~~**Raspberry Pi deployment:**~~ Live on Pi 5 (goodmorning.local). Native PostgreSQL + nginx + gunicorn, XDG autostart fullscreen Chromium kiosk. Manual scp+rsync deployment (deploy.sh doesn't handle full Pi deployment).
- **Docker Compose deployment:** Dev only (PostgreSQL container). No full-stack Docker Compose.

### Google Account Integration (Phase 7) — DONE

- **OAuth 2.0 flow:** `django-allauth` with Google provider. GCP project in Testing mode.
- **Required scopes:** `profile`, `email`, `calendar.readonly`, `photospicker.mediaitems.readonly`
- **What was implemented:**
  - Google Calendar API — real-time event sync via background jobs, replaced ICS feeds
  - Google Photos Picker API — album/photo selection, background photo slideshow
  - Photo proxy endpoint (`/api/photos/<index>/`) serves images through backend with Google OAuth
  - Picker API baseUrls expire; proxy auto-refreshes from Picker API on 403
  - Frontend auth UI: AuthStatus, CalendarPicker, PhotosPicker components
  - CSRF token handling added to frontend `apiFetch`
- **Architecture notes:**
  - Google account user ("nick") and dashboard owner ("admin") are different users
  - Background jobs use first Google-linked account for API credentials
  - Widget name is "photos" (not "slideshow") in `widget_layout`
  - `access_type=offline` for refresh tokens — background jobs keep working without re-auth
- **Redirect URIs:** `http://goodmorning.local/api/auth/callback/` (Pi), `http://localhost:8000/api/auth/callback/` (dev)

### Additional Widgets

| Widget | Data Source | Complexity |
|--------|-----------|------------|
| ~~News headlines~~ | ~~RSS feeds~~ | **Implemented in Phase 6.1** |
| Transit/commute | Google Maps Directions API | Medium |
| ~~Photo slideshow~~ | ~~Google Photos Picker API~~ | **Implemented — background slideshow via Google Photos** |
| Reminders/to-do | Google Tasks API or local model | Low |
| System status | psutil (CPU, RAM, disk) | Low |
| Dexcom glucose | pydexcom (Dexcom Share API, no dev account needed) | Medium (see details below) |
| Cryptocurrency | CoinGecko API (free, no key) | Low |

### Dexcom Glucose Monitor Widget

Display real-time CGM (continuous glucose monitor) readings from a Dexcom sensor on the dashboard.

**Library:** `pydexcom` (`pip install pydexcom`, v0.5.1, actively maintained, used by Home Assistant)

**How it works:**
- Uses Dexcom's reverse-engineered Share API — NOT the official developer API
- Only needs the user's regular Dexcom app credentials (email + password)
- Share must be enabled in the Dexcom app (at least one follower added)
- Auto-handles session refresh, no manual token management

**Backend:**
- `GlucoseReading` model: value (mg/dL), mmol_l, trend_direction, trend_arrow, recorded_at
- `services/glucose.py`: pydexcom client wrapper
- APScheduler job: **5-minute interval** (matches CGM reading frequency)
- `GET /api/glucose/` — latest reading + last 3 hours for sparkline

**Frontend:**
- Large glucose number, color-coded (green 70-180, yellow 55-70/180-250, red <55/>250)
- Unicode trend arrow (↗ ↑ → ↘ ↓)
- Mini sparkline of last 3 hours
- Stale indicator if reading >15 minutes old
- Configurable label (e.g. "Lizzii's Glucose")

**Caveats:**
- Share API is undocumented — could break if Dexcom changes their backend (has been stable for years)
- Fallback: Nightscout (self-hosted Node.js middleware) if Share API is blocked

### Photo Slideshow Mode — DONE

Background photo slideshow implemented using Google Photos Picker API.

**Implementation:**
- Google Photos Picker API for photo selection (not the deprecated Library API)
- Photos proxied through backend via `/api/photos/<index>/` (avoids CORS, handles auth)
- Picker API `baseUrl`s expire; proxy auto-refreshes from Picker API on 403
- Full-screen background behind all widgets with dark overlay
- Crossfade transitions between photos
- Frontend `PhotoBackground` component handles cycling and transitions

**Not implemented (deferred):**
- Local folder mode (Phase 1 skipped — went straight to Google Photos)
- Ken Burns pan/zoom effect
- Multiple transition styles (only crossfade)
- Configurable widget transparency
- Sequential ordering (shuffle only)

### UI Enhancements

- **Custom clock labels:** Allow renaming aux clock locations with personal labels (e.g., "Lizzii" instead of "Guernsey", "Mark" instead of "Gig Harbor"). Store custom labels in the clock widget settings. Display format: custom label on top, timezone city below in smaller text, so users see family names at a glance while retaining location context.
- **Theme customization:** Dark mode via CSS custom properties toggle. User preference stored in `UserDashboard.widget_layout` or a separate theme field.
- **Multi-dashboard support:** Multiple `UserDashboard` rows per user (e.g., "Morning" vs "Evening" layouts). Add a `name` field and modify the API to support switching.
- **PWA / kiosk mode:** `vite-plugin-pwa` for installable app. Android tablets support kiosk mode for full-screen display.
- **Drag-and-drop widget arrangement:** Use `@dnd-kit/core` for reordering widgets in the React grid.

### Real-Time Updates

- **Server-Sent Events (SSE):** Django ASGI + `StreamingHttpResponse` for push updates. Eliminates polling overhead. Only worthwhile if the dashboard needs sub-minute updates.
- **WebSocket:** Django Channels + Redis. Maximum complexity, only justified for live trading or collaborative features. Not recommended for a morning dashboard.

### Cloud Deployment

- **Render:** Free tier web service + Neon PostgreSQL. Auto-deploy on git push.
- **Railway:** $5/mo minimum. PostgreSQL add-on. Simpler than Render.
- **VPS (Hetzner/DigitalOcean):** $4-6/mo. Same Docker Compose as Pi. Let's Encrypt for HTTPS via Caddy or nginx.

---

## Appendix: WMO Weather Codes Reference

For mapping `weather_code` to display text and icons in the weather widget:

| Code | Description | Suggested Icon |
|------|-------------|----------------|
| 0 | Clear sky | sun |
| 1 | Mainly clear | sun-cloud |
| 2 | Partly cloudy | cloud-sun |
| 3 | Overcast | cloud |
| 45, 48 | Fog | fog |
| 51, 53, 55 | Drizzle (light/moderate/dense) | cloud-drizzle |
| 61, 63, 65 | Rain (slight/moderate/heavy) | cloud-rain |
| 71, 73, 75 | Snow (slight/moderate/heavy) | cloud-snow |
| 80, 81, 82 | Rain showers | cloud-showers |
| 95, 96, 99 | Thunderstorm (with/without hail) | cloud-lightning |

---

## Appendix: Default News RSS Feed Sources

Reliable RSS feeds for the news widget. All are free, require no API key, and are maintained by major news organizations.

| Source | Feed URL | Content |
|--------|----------|---------|
| BBC News (Top Stories) | `https://feeds.bbci.co.uk/news/rss.xml` | UK and world news |
| BBC News (World) | `https://feeds.bbci.co.uk/news/world/rss.xml` | International news |
| NPR (Top Stories) | `https://feeds.npr.org/1001/rss.xml` | US and world news |
| Reuters (Top News) | `https://www.reutersagency.com/feed/` | Wire service headlines |
