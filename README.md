# Good Morning Dashboard

A full-stack web dashboard designed for a tablet display in a living room. Shows at-a-glance information you want to see first thing in the morning: time, weather, stocks, calendar, and news headlines.

![Dashboard Screenshot](docs/dashboard-screenshot.png)

## Tech Stack

- **Backend:** Django 5.2 LTS + Django REST Framework + django-allauth (Google OAuth)
- **Frontend:** React 19 + Vite, CSS Modules
- **Database:** PostgreSQL 16 (Docker for dev, native on Pi)
- **Scheduler:** django-apscheduler for periodic data fetching
- **Styling:** CSS Modules, dark gradient theme with glass-morphism cards

## Widgets

| Widget | Data Source | Update Frequency |
|--------|-----------|-----------------|
| Clock | Client-side | Every second |
| Weather | Open-Meteo API (no key required) | Every 15 minutes |
| Stocks | Finnhub API (free tier) | Every 5 minutes |
| Calendar | Google Calendar API (OAuth) | Every 30 minutes |
| News | RSS feeds (BBC, NPR, Reuters) | Every 60 minutes |
| Photos | Google Photos Picker API | Configurable (15-300s) |
| Glucose | Dexcom Share API (CGM) | Every 5 minutes |

## Layout

Uses a **Hero layout** (60/40 split):
- **Left panel:** Clock (multi-timezone: primary + 0-3 configurable aux) and Weather
- **Right panel:** Glucose, Stocks, Calendar, and News stacked vertically

Background photo slideshow from Google Photos with configurable crossfade interval.

**Photo Frame Mode:** Fullscreen photo slideshow with optional dashboard flash — the dashboard appears as a "slide" every N photos for a configurable duration, then fades back to photos.

## Quick Start

### Prerequisites
- Docker Desktop (for PostgreSQL)
- Python 3.12+
- Node.js 20+

### One-command setup

```bash
./deploy.sh
```

This starts Docker, installs all dependencies, runs migrations, seeds sample data, and launches all dev servers.

Other deploy commands:

```bash
./deploy.sh --services   # Start PostgreSQL via Docker
./deploy.sh --backend    # Install Python deps, migrate, seed
./deploy.sh --frontend   # npm install
./deploy.sh --start      # Launch all dev servers
./deploy.sh --stop       # Stop all dev servers
./deploy.sh --test       # Start services + run pytest
```

### Manual setup

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env             # Edit with your API keys
python manage.py migrate
python manage.py seed_data       # Creates admin user + sample data
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Scheduler (optional, for live data):**
```bash
cd backend
source .venv/Scripts/activate
python manage.py run_scheduler
```

After startup:
- **Dashboard:** http://localhost:5173
- **API:** http://localhost:8000/api/
- **Admin:** http://localhost:8000/admin/ (admin / admin)

### Run Tests
```bash
# Backend (128 tests) — requires PostgreSQL running
cd backend
source .venv/Scripts/activate
python -m pytest -v

# Frontend (22 tests)
cd frontend
npm test
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | Default: True |
| `DATABASE_URL` | No | Default: SQLite. Set to `postgres://...` for PostgreSQL |
| `FINNHUB_API_KEY` | For stocks | Free at finnhub.io |
| `WEATHER_LAT` | No | Latitude (default: 40.7128 / NYC) |
| `WEATHER_LON` | No | Longitude (default: -74.0060 / NYC) |
| `GOOGLE_CLIENT_ID` | For Google | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For Google | Google OAuth client secret |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/weather/` | GET | Cached weather data |
| `/api/weather/location/` | POST | Update weather location |
| `/api/stocks/` | GET | Cached stock quotes |
| `/api/calendar/` | GET | Today's calendar events |
| `/api/news/` | GET | Recent news headlines |
| `/api/dashboard/` | GET, PATCH | User dashboard configuration |
| `/api/geocode/` | GET | City search for location picker |
| `/api/auth/status/` | GET | Auth status + CSRF cookie |
| `/api/photos/<index>/` | GET | Photo proxy (Google Photos) |
| `/api/photos/picker/session/` | POST | Create Photos Picker session |
| `/api/photos/picker/session/<id>/poll/` | GET | Poll picker session status |
| `/api/photos/picker/session/<id>/media/` | GET | Fetch picker media items |
| `/api/glucose/` | GET | Current glucose reading + 3hr history |

## Project Structure

```
goodmorning/
  backend/
    config/           # Django project settings
    dashboard/        # Main Django app
      models.py       # UserDashboard, WeatherCache, StockQuote, CalendarEvent, NewsHeadline, GlucoseReading
      views.py        # DRF API views
      serializers.py  # DRF serializers
      services/       # External API integrations (weather, stocks, calendar, news, geocode)
      jobs.py         # Scheduler job definitions
      tests/          # pytest test suite
    manage.py
  frontend/
    src/
      api/            # Fetch wrappers for each endpoint
      hooks/          # TanStack Query hooks
      components/
        widgets/      # ClockWidget, WeatherWidget, StocksWidget, CalendarWidget, NewsWidget, GlucoseWidget
        mocks/        # UI layout and widget design mockups
        Dashboard.jsx # Main Hero layout
        BackgroundSlideshow.jsx  # Google Photos slideshow
        SettingsPanel.jsx        # Settings panel (clock, photos, glucose, Google account)
  docker-compose.yml  # PostgreSQL 16
  deploy.sh           # One-command bootstrap & startup
```

## Deployment Targets

| Target | Database | Status |
|--------|----------|--------|
| Local Windows + Docker | PostgreSQL 16 | Working |
| Raspberry Pi | PostgreSQL 16 (native) | Working |

## Future Work

- Configurable news feeds and keyword filtering
- Privacy Policy page (needed for Google verification)
- PWA support (tablet home screen install)
- Theme customization (dark/light modes)
