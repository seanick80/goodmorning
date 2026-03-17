# Good Morning Dashboard

A full-stack web dashboard designed for a tablet display in a living room. Shows at-a-glance information you want to see first thing in the morning: time, weather, stocks, calendar, and news headlines.

![Dashboard Screenshot](docs/dashboard-screenshot.png)

## Tech Stack

- **Backend:** Django 5.x + Django REST Framework
- **Frontend:** React 19 + Vite
- **Database:** SQLite (local dev), PostgreSQL (Pi/cloud deployments)
- **Scheduler:** django-apscheduler for periodic data fetching
- **Styling:** CSS Modules, dark gradient theme with glass-morphism cards

## Widgets

| Widget | Data Source | Update Frequency |
|--------|-----------|-----------------|
| Clock | Client-side | Every second |
| Weather | Open-Meteo API (no key required) | Every 15 minutes |
| Stocks | Finnhub API (free tier) | Every 5 minutes |
| Calendar | ICS feed (Google/Outlook/iCloud) | Every 30 minutes |
| News | RSS feeds (BBC, NPR, Reuters) | Every 60 minutes |

## Layout

Uses a **Hero layout** (60/40 split):
- **Left panel:** Clock (multi-timezone: primary + 2 aux) and Weather
- **Right panel:** Stocks, Calendar, and News stacked vertically

## Quick Start (Local Windows Development)

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup
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

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 to view the dashboard.

### Run the Scheduler (optional, for live data)
```bash
cd backend
source .venv/Scripts/activate
python manage.py run_scheduler
```

### Run Tests
```bash
# Backend (55 tests)
cd backend
source .venv/Scripts/activate
python -m pytest -v

# Frontend
cd frontend
npm test
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | Default: True |
| `FINNHUB_API_KEY` | For stocks | Free at finnhub.io |
| `WEATHER_LAT` | No | Latitude (default: 40.7128 / NYC) |
| `WEATHER_LON` | No | Longitude (default: -74.0060 / NYC) |
| `DATABASE_URL` | No | Default: SQLite. Set to `postgres://...` for PostgreSQL |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/weather/` | GET | Cached weather data |
| `/api/stocks/` | GET | Cached stock quotes |
| `/api/calendar/` | GET | Today's calendar events |
| `/api/news/` | GET | Recent news headlines |
| `/api/dashboard/` | GET, PATCH | User dashboard configuration |

## Project Structure

```
goodmorning/
  backend/
    config/           # Django project settings
    dashboard/        # Main Django app
      models.py       # UserDashboard, WeatherCache, StockQuote, CalendarEvent, NewsHeadline
      views.py        # DRF API views
      services/       # External API integrations (weather, stocks, calendar, news)
      jobs.py         # Scheduler job definitions
      tests/          # pytest test suite
    manage.py
  frontend/
    src/
      api/            # Fetch wrappers for each endpoint
      hooks/          # TanStack Query hooks
      components/
        widgets/      # ClockWidget, WeatherWidget, StocksWidget, CalendarWidget, NewsWidget
        mocks/        # UI layout and widget design mockups
        Dashboard.jsx # Main Hero layout
  FRAMEWORK_ANALYSIS.md   # Architecture decisions
  STORAGE_ANALYSIS.md     # Database and persistence decisions
  EXECUTION_PLAN.md       # Full implementation plan
```

## Deployment Targets

| Target | Database | Status |
|--------|----------|--------|
| Local Windows | SQLite | Working |
| Docker + ARM emulation | PostgreSQL | Planned |
| Raspberry Pi | PostgreSQL (tuned) | Planned |
| Cloud (Render/Railway) | PostgreSQL (managed) | Planned |

## Future Work

- Google Account integration (OAuth, Calendar API)
- Docker Compose deployment
- Raspberry Pi deployment with tuned PostgreSQL
- PWA support (tablet home screen install)
- Theme customization (dark/light modes)
- Additional widgets (transit, photos, reminders)
