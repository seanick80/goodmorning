# Good Morning Dashboard -- Framework Analysis

**Date:** 2026-03-17
**Status:** Research Complete

---

## 1. Executive Summary / Recommendation

**Recommended stack: Django + React (Vite) + PostgreSQL + Docker**

Django with Django REST Framework on the backend, React (via Vite) on the frontend. This combination has the strongest ecosystem for the required integrations (weather, stocks, calendar) and runs comfortably on a Raspberry Pi with 1GB+ RAM when configured with 2 Gunicorn workers and a tuned PostgreSQL instance. Data is fetched on a schedule by a lightweight background task runner (django-apscheduler or Huey), cached in PostgreSQL, and served to the React frontend via REST endpoints. The frontend polls every 60 seconds or uses Server-Sent Events for push updates. PostgreSQL is used across all deployment targets past local Windows development (where SQLite remains the default for zero-config simplicity). The dashboard supports multiple users, each with their own widget configuration stored in per-user models.

**Confidence:** High -- all components are mature, well-documented, and have proven ARM/Pi deployments.

---

## 2. Frontend Framework Comparison

| Criterion               | React (Vite)         | Vue 3 (Vite)         | Svelte (SvelteKit)   | Plain HTML/JS        |
|--------------------------|----------------------|----------------------|----------------------|----------------------|
| **Ecosystem size**       | Largest              | Large                | Growing (smaller)    | N/A                  |
| **Bundle size**          | ~45 KB gzipped       | ~33 KB gzipped       | ~5-10 KB gzipped     | Zero framework       |
| **PWA support**          | Excellent (vite-pwa) | Excellent (vite-pwa) | Good                 | Manual               |
| **Tablet UI libraries**  | MUI, Chakra, Ant     | Vuetify, Quasar      | Skeleton UI          | CSS frameworks       |
| **Auto-refresh/polling** | React Query          | Vue Query/TanStack   | Native stores        | setInterval/fetch    |
| **Learning curve**       | Moderate             | Low-moderate         | Low                  | Lowest               |
| **Real-time (SSE/WS)**   | Native EventSource   | Native EventSource   | Native EventSource   | Native EventSource   |
| **Dev experience**       | Hot reload, DevTools | Hot reload, DevTools | Hot reload           | Browser DevTools     |

### Analysis

**React** is the preferred choice. Its ecosystem provides the richest selection of dashboard-oriented component libraries (MUI's data display components, Recharts/Nivo for stock charts). TanStack Query (React Query) handles data fetching, caching, and automatic refetching with minimal boilerplate -- ideal for a polling-based dashboard.

**Svelte** would be the best pure-technical choice for a resource-constrained display (smallest bundle, fastest rendering), but React's larger ecosystem and community support make it a stronger long-term choice.

**Plain HTML/JS** would be simplest for this scope but sacrifices component reusability and state management.

### Recommendation: React with Vite

- **Vite** over Create React App (CRA is deprecated; Vite is the current standard)
- **TanStack Query** for data fetching with configurable refetch intervals
- **MUI (Material UI)** or **CSS Modules + a lightweight grid** for tablet-friendly layout
- **vite-plugin-pwa** for PWA/installable app capability (tablet homescreen icon)

---

## 3. Backend Framework Comparison

| Criterion                    | Django + DRF           | FastAPI                | Flask                  | Express (Node)         |
|-------------------------------|------------------------|------------------------|------------------------|------------------------|
| **Batteries included**        | ORM, admin, auth, etc. | Minimal (assemble)     | Minimal (assemble)     | Minimal (assemble)     |
| **API development**           | DRF serializers/views  | Pydantic + auto-docs   | Manual/Flask-RESTX     | express-router         |
| **Background tasks**          | django-apscheduler, Huey, Celery | APScheduler, Celery | APScheduler, Celery | node-cron, Bull        |
| **Admin panel**               | Built-in (excellent)   | None (add manually)    | Flask-Admin            | None                   |
| **Pi memory footprint**       | ~80-150 MB (2 workers) | ~50-80 MB (uvicorn)    | ~40-60 MB              | ~50-80 MB              |
| **Pi CPU impact**             | Moderate               | Low (async)            | Low                    | Low (event loop)       |
| **Async support**             | Django 4.2+ (ASGI)     | Native async           | Limited                | Native async           |
| **Deployment maturity**       | Excellent              | Good                   | Excellent              | Excellent              |
| **Cloud PaaS support**        | All major platforms    | All major platforms    | All major platforms    | All major platforms    |
| **Community/docs**            | Largest Python web     | Fast-growing           | Large                  | Largest overall        |

### Analysis

**Django** is heavier than alternatives but brings substantial advantages: the admin panel doubles as a configuration UI (add/remove tracked stocks, set location for weather, configure calendar URL), the ORM simplifies data caching to SQLite, and the entire Django ecosystem (authentication, middleware, management commands) is mature and well-documented.

**Memory on Raspberry Pi:** Django with 2 Gunicorn sync workers uses approximately 80-150 MB. On a 1GB Pi, this leaves ample room for the OS, nginx, and background tasks. Using `--max-requests 1000 --max-requests-jitter 50` prevents memory creep over time.

**FastAPI** would be technically superior for pure API performance (async, auto-generated OpenAPI docs), but it lacks the admin panel and ORM-integrated migrations that Django provides out of the box.

**Key insight:** Django's admin panel eliminates the need to build a separate settings/configuration UI in the early phases. Users can add stocks to track, change weather location, and configure calendar sources through `/admin/` immediately.

### Recommendation: Django 5.x + Django REST Framework

- **Django 5.x** with ASGI support (for optional SSE later)
- **Django REST Framework** for clean API endpoints
- **Gunicorn** (2 sync workers) for production serving on Pi
- **django-apscheduler** for lightweight scheduled data fetching (no Redis dependency)
- **PostgreSQL** as the database (first-class Django support, multi-user capable, consistent across Pi and cloud)
- **SQLite** for local Windows development only (zero-config convenience)

---

## 4. Architecture Overview

```
+------------------+       +-----------------------+       +------------------+
|   React (Vite)   | <---> |   Django + DRF API    | <---> |  PostgreSQL DB   |
|   Browser/Tablet |  HTTP |   /api/weather/       |       |  (cached data +  |
|                  |       |   /api/stocks/        |       |   user configs)  |
|  TanStack Query  |       |   /api/calendar/      |       +------------------+
|  (polls every    |       |   /api/dashboard/     |
|   60-300s)       |       +-----------+-----------+       +------------------+
+------------------+                   |                   |  External APIs   |
                              Background Scheduler         |  - Open-Meteo    |
                              (django-apscheduler)         |  - Finnhub       |
                              fetches every 5-15 min  ---> |  - Google Cal    |
                                       |                   +------------------+
                              Writes to PostgreSQL cache
```

### Data Flow

1. **Background scheduler** runs inside the Django process via django-apscheduler
   - Weather: fetches from Open-Meteo every 15 minutes, stores in `WeatherCache` model
   - Stocks: fetches from Finnhub every 5 minutes (during market hours), stores in `StockQuote` model
   - Calendar: fetches ICS feed or Google Calendar API every 30 minutes, stores in `CalendarEvent` model

2. **API endpoints** serve cached data from PostgreSQL (fast, no external calls on request)
   - `GET /api/weather/` -- current conditions + today's forecast
   - `GET /api/stocks/` -- latest quotes for tracked symbols
   - `GET /api/calendar/` -- today's events
   - `GET /api/settings/` -- dashboard configuration (location, symbols, etc.)

4. **Per-user configuration** stored in PostgreSQL via `UserDashboard` model
   - Each user has a `widget_layout` JSONField with their enabled widgets, positions, and widget-specific settings
   - `GET /api/dashboard/` -- current user's widget layout and settings
   - `PATCH /api/dashboard/` -- update widget layout or settings
   - Default layout created automatically on first login (via Django signal or DRF view logic)

5. **React frontend** uses TanStack Query to poll endpoints
   - Weather: refetch every 5 minutes (data changes every 15 min server-side)
   - Stocks: refetch every 60 seconds during market hours, every 5 min otherwise
   - Calendar: refetch every 10 minutes
   - Clock/greeting: client-side, no API needed

### Why Polling Over SSE/WebSockets

For a dashboard that updates weather every 15 minutes and stocks every few minutes, simple HTTP polling is the right choice:

- **Simplicity:** No WebSocket infrastructure, no Django Channels, no Redis
- **Pi-friendly:** No persistent connections consuming memory
- **Resilient:** Browser tab sleep/wake just resumes polling
- **Sufficient:** 1 request per endpoint per minute = ~4 requests/minute total; negligible load

SSE or WebSockets would be appropriate if the dashboard needed sub-second updates (live trading), but for a morning dashboard they add complexity without benefit.

---

## 5. Data Sources (Free APIs)

### Weather: Open-Meteo

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **URL**         | https://open-meteo.com/                    |
| **API Key**     | None required                              |
| **Rate Limit**  | 10,000 calls/day, 5,000/hour, 600/minute   |
| **Data**        | Current conditions, hourly/daily forecast   |
| **Cost**        | Free for non-commercial use                |
| **Reliability** | Open-source, backed by national weather services |

**Why Open-Meteo over alternatives:**
- No API key or account registration needed (simplest setup)
- Generous rate limits (far more than needed)
- High-resolution data from national weather services
- Returns sunrise/sunset, precipitation probability, UV index
- Alternative: OpenWeatherMap (free tier requires API key, 1,000 calls/day)

### Stocks: Finnhub

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **URL**         | https://finnhub.io/                        |
| **API Key**     | Required (free registration)               |
| **Rate Limit**  | 60 calls/minute                            |
| **Data**        | Real-time US quotes, company profiles      |
| **WebSocket**   | Available (50 symbols free tier)           |
| **Cost**        | Free tier sufficient for dashboard use     |

**Why Finnhub:**
- Real-time US stock data on free tier (not delayed like many competitors)
- 60 calls/minute is generous for tracking 5-20 stocks
- Simple REST API: `GET /api/v1/quote?symbol=AAPL`
- Alternative: Alpha Vantage (only 25 calls/day on free tier -- too restrictive)

### Calendar: Two-Tier Approach

**Tier 1 -- ICS Feed (simplest, recommended to start):**

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **Protocol**    | HTTP GET of `.ics` URL                     |
| **Auth**        | None (use secret/private calendar URL)     |
| **Libraries**   | `icalendar` Python package to parse        |
| **Providers**   | Google Calendar, Outlook, iCloud all export ICS |
| **Limitation**  | Read-only, updates can lag 12-24 hours on some providers |

Google Calendar provides a "Secret address in iCal format" URL per calendar that can be fetched without OAuth. This is the simplest path for a personal dashboard.

**Tier 2 -- Google Calendar API (richer, add later):**

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **Auth**        | OAuth 2.0 (one-time setup via Google Cloud Console) |
| **Rate Limit**  | 1,000,000 queries/day                     |
| **Data**        | Full event details, attendees, reminders   |
| **Cost**        | Free                                       |
| **Complexity**  | Requires OAuth flow, token refresh         |

Recommendation: Start with ICS in Phase 1. Add Google Calendar API as an enhancement later if real-time accuracy matters.

---

## 6. Deployment Strategy

### 6.1 Local Windows Development

```
Development machine (Windows 11)
+-- Django dev server (manage.py runserver)
+-- Vite dev server (npm run dev) with proxy to Django
+-- SQLite database (file in project root)
+-- No Docker needed for development
```

- `python manage.py runserver` for backend
- `npm run dev` (Vite) for frontend with hot reload
- Vite proxy config forwards `/api/` requests to Django
- SQLite is the default for local dev (zero-config, no Docker dependency)
- **Optional:** Run PostgreSQL locally via Docker (`docker run -p 5432:5432 postgres:17-alpine`) and set `DATABASE_URL` to match Pi/cloud environments. This ensures full parity but is not required for day-to-day development.

### 6.2 Local ARM Emulation (Pre-Hardware Testing)

Before physical Raspberry Pi hardware arrives, validate the Docker-based ARM deployment on your Windows machine using emulation.

#### Recommended: Docker Desktop ARM Emulation (Primary Method)

Docker Desktop for Windows includes QEMU-based ARM emulation. Adding `platform: linux/arm64/v8` to each service in `docker-compose.yml` runs the entire stack under ARM64 — no additional setup required.

```yaml
# docker-compose.yml (add platform to each service)
services:
  db:
    platform: linux/arm64/v8
    image: postgres:17-alpine
    environment:
      - POSTGRES_DB=goodmorning_db
      - POSTGRES_USER=goodmorning
      - POSTGRES_PASSWORD=devpassword
    volumes:
      - db-data:/var/lib/postgresql/data
  web:
    platform: linux/arm64/v8
    build: .
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgres://goodmorning:devpassword@db:5432/goodmorning_db
  nginx:
    platform: linux/arm64/v8
    image: nginx:alpine
volumes:
  db-data:
```

```bash
# Or run individual ARM64 containers directly
docker run --platform linux/arm64 -it python:3.12-slim uname -m
# Output: aarch64

# Build for ARM64
docker buildx build --platform linux/arm64 -t goodmorning:arm64 .
```

| Property | Details |
|----------|---------|
| **Setup** | Trivial — Docker Desktop already has QEMU built in |
| **ARM fidelity** | High — runs real ARM64 binaries |
| **Docker Compose** | Fully supported with `platform:` directive |
| **Performance** | 5-20x slowdown (acceptable for dev/testing) |
| **What it catches** | Package compatibility, base image availability, architecture-specific build failures |
| **What it misses** | Pi-specific hardware (GPIO, VideoCore), exact kernel behavior |

**Tip:** React/Vite builds are CPU-intensive and noticeably slower under emulation. Consider building the frontend natively on x86 and copying the build artifacts into the ARM container via a multi-stage Dockerfile.

#### Alternative: Oracle Cloud Free-Tier ARM Instance

For highest fidelity without real Pi hardware, Oracle Cloud's free tier includes Ampere A1 ARM instances (up to 4 cores, 24 GB RAM). This provides a real ARM64 environment with native performance — SSH in, install Docker, and test your Compose stack.

#### Approaches to Skip

| Approach | Why skip |
|----------|----------|
| QEMU full system VM | Complex setup, 10-50x slowdown, impractical for iteration |
| Raspberry Pi Desktop VM (x86) | Runs x86, not ARM — doesn't test the thing most likely to break |
| dockerpi nested emulation | Docker-inside-QEMU-inside-Docker is too slow and fragile |

### 6.3 Raspberry Pi (Production, Local Network)

```
Raspberry Pi (1GB+ RAM, ARM64, Raspberry Pi OS)
+-- Docker Compose
    +-- nginx (serves React build + reverse proxy to Django)
    +-- Django + Gunicorn (2 workers, WSGI)
    +-- PostgreSQL 17 (Alpine, tuned for Pi)
```

**Resource budget (1GB RAM Pi):**

| Component       | Estimated RAM | Notes                                           |
|-----------------|---------------|-------------------------------------------------|
| Raspberry Pi OS | ~150 MB       | Lite (headless) recommended                     |
| Docker engine   | ~50 MB        |                                                 |
| nginx           | ~5 MB         |                                                 |
| PostgreSQL      | ~60-80 MB     | Tuned: `shared_buffers=64MB`, `max_connections=20` |
| Gunicorn (2w)   | ~100-150 MB   | `--max-requests 1000`                           |
| Scheduler       | In-process    | django-apscheduler, no extra                    |
| **Total**       | ~415-485 MB   | Leaves ~500 MB headroom on 1GB Pi               |

**Docker considerations for ARM:**
- Use official Python, nginx, and PostgreSQL images (all support `linux/arm64`)
- Multi-stage Dockerfile: build React in a Node stage, copy static files to nginx
- `docker buildx` for cross-platform builds from Windows if needed
- PostgreSQL data on a named Docker volume (`db-data:/var/lib/postgresql/data`)
- Tune PostgreSQL for Pi: `shared_buffers=64MB`, `work_mem=2MB`, `max_connections=20`

**PostgreSQL ARM64 image:** The official `postgres:17-alpine` image supports `linux/arm64` natively. The Alpine variant keeps the image small (~80 MB compressed). All PostgreSQL versions 14-17 are available for ARM64.

**Accessing from tablet:** Tablet connects to `http://<pi-ip>/` on local network. The React PWA can be added to the tablet home screen for a fullscreen, app-like experience.

### 6.4 Cloud VPS / PaaS

**Option A: Render (recommended for simplicity)**

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **Free tier**   | 750 hours/month (one always-on service)    |
| **Django**      | Web Service with Gunicorn                  |
| **Static files**| Whitenoise or Render static site           |
| **Database**    | Free PostgreSQL for 90 days, then $7/mo    |
| **HTTPS**       | Automatic                                  |
| **Deploy**      | Git push triggers build                    |

**Option B: Railway**

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **Free tier**   | Trial only (~$5 credit), then $5/mo min    |
| **Django**      | Auto-detected from requirements.txt        |
| **Database**    | PostgreSQL add-on                          |
| **HTTPS**       | Automatic                                  |

**Option C: VPS (DigitalOcean, Hetzner)**

| Property        | Details                                    |
|-----------------|--------------------------------------------|
| **Cost**        | $4-6/mo for smallest VPS                   |
| **Setup**       | Same Docker Compose as Pi                  |
| **HTTPS**       | Let's Encrypt + Caddy or nginx             |
| **Control**     | Full root access                           |

**Cloud database note:** PostgreSQL is already the standard database across all deployment targets past local dev. Cloud deployments use platform-managed PostgreSQL (Neon free tier, Render, or Railway add-on) or a self-hosted PostgreSQL container on a VPS. The `DATABASE_URL` environment variable points to the cloud instance -- no code or settings changes required vs. the Pi deployment.

### 6.5 Unified Docker Compose

A single `docker-compose.yml` works across ARM emulation, Pi, and cloud VPS with no changes (only environment variables differ):

```yaml
# Conceptual structure (not implementation)
services:
  db:
    image: postgres:17-alpine
    environment:
      - POSTGRES_DB=goodmorning_db
      - POSTGRES_USER=goodmorning
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
    command: >
      postgres
        -c shared_buffers=64MB
        -c work_mem=2MB
        -c max_connections=20
  web:
    build: .                    # Multi-stage: Node build + Python + Gunicorn
    environment:
      - DATABASE_URL=postgres://goodmorning:${DB_PASSWORD}@db:5432/goodmorning_db
      - FINNHUB_API_KEY=${FINNHUB_API_KEY}
    depends_on:
      - db
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - static:/app/static

volumes:
  db-data:      # PostgreSQL data, survives container rebuilds
  static:       # Collected static files
```

For cloud PaaS deployments (Render, Railway) where PostgreSQL is platform-managed, the `db` service is omitted and `DATABASE_URL` points to the managed instance.

### 6.6 Per-User Widget Configuration

The dashboard supports multiple users, each with their own widget layout and settings.

#### Data Model

```python
# Conceptual model (not implementation)
class UserDashboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard')
    widget_layout = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

The `widget_layout` field stores an ordered list of widget configurations:

```json
[
  {"widget": "clock", "enabled": true, "position": 0, "settings": {"format": "12h"}},
  {"widget": "weather", "enabled": true, "position": 1, "settings": {"units": "fahrenheit"}},
  {"widget": "stocks", "enabled": true, "position": 2, "settings": {"symbols": ["AAPL", "GOOGL", "MSFT"]}},
  {"widget": "calendar", "enabled": true, "position": 3, "settings": {"ics_urls": ["https://..."]}}
]
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/` | GET | Current user's widget layout and settings |
| `/api/dashboard/` | PATCH | Update widget layout, positions, or widget-specific settings |
| `/api/dashboard/defaults/` | POST | Reset to default widget layout |

#### Default Layout

On first login (or account creation), a default `UserDashboard` is created via a Django signal or the API view's `get_or_create` logic. The default layout includes all widgets enabled in a standard order.

#### Why JSONField Over Normalized Tables

For the initial implementation, a single JSONField is simpler and sufficient:
- One query loads the entire dashboard configuration
- Widget ordering is trivially stored as array position
- Widget-specific settings vary by type (weather needs lat/lon, stocks need symbols) -- JSON handles this naturally
- PostgreSQL's JSONField supports querying into the JSON structure if needed later

If the dashboard later needs to query across users (e.g., "which users track AAPL?"), a normalized `WidgetConfig` table with a ForeignKey to `UserDashboard` is a straightforward migration path.

### 6.7 Data Backup and Restore

#### Primary: pg_dump / pg_restore

```bash
# Full backup (custom format, compressed, portable)
docker exec goodmorning-db pg_dump -Fc -U goodmorning goodmorning_db > backup_$(date +%Y%m%d).dump

# Restore to a fresh database
docker exec -i goodmorning-db pg_restore -U goodmorning -d goodmorning_db < backup_20260317.dump

# SQL format (human-readable, useful for inspection)
docker exec goodmorning-db pg_dump -U goodmorning goodmorning_db > backup.sql
```

#### Portable: Django dumpdata / loaddata

```bash
# Export as DB-agnostic JSON (works across SQLite and PostgreSQL)
python manage.py dumpdata --indent 2 --exclude=contenttypes --exclude=auth.Permission > backup.json

# Import on any backend
python manage.py loaddata backup.json
```

Useful for migrating data from local SQLite (dev) to PostgreSQL (Pi/cloud), or for seeding a fresh deployment.

#### Automated Scheduled Backups

**On Raspberry Pi (cron):**
```bash
# /etc/cron.d/goodmorning-backup
0 2 * * * docker exec goodmorning-db pg_dump -Fc -U goodmorning goodmorning_db > /home/pi/backups/gm-$(date +\%F).dump
0 3 * * * find /home/pi/backups -name "gm-*.dump" -mtime +7 -delete
```

**On Windows (Task Scheduler):**
Create a scheduled task that runs a PowerShell script calling `docker exec ... pg_dump` daily and prunes backups older than 7 days.

**Docker sidecar (alternative):**
```yaml
# Add to docker-compose.yml
services:
  db-backup:
    image: prodrigestivill/postgres-backup-local
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_DB=goodmorning_db
      - POSTGRES_USER=goodmorning
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - SCHEDULE=@daily
      - BACKUP_KEEP_DAYS=7
    volumes:
      - ./backups:/backups
    depends_on:
      - db
```

#### Docker Volume Backup

For full volume-level backup (includes PostgreSQL internal files):
```bash
# Stop PostgreSQL first for consistency
docker compose stop db
docker run --rm -v goodmorning_db-data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/pg-volume-$(date +%Y%m%d).tar.gz -C /data .
docker compose start db
```

#### Point-in-Time Recovery (WAL Archiving)

PostgreSQL supports continuous archiving via WAL (Write-Ahead Log) shipping, enabling recovery to any point in time. This requires `archive_mode=on` and a WAL archive destination. **This is overkill for a personal dashboard** -- the cached API data (weather, stocks, calendar) is ephemeral and re-fetched by the scheduler within minutes. Daily `pg_dump` backups provide more than sufficient protection for user settings and widget configurations.

---

## 7. Recommended Tech Stack (Summary)

| Layer              | Choice                  | Justification                                              |
|--------------------|-------------------------|------------------------------------------------------------|
| **Frontend**       | React 19 + Vite         | Preferred framework, largest ecosystem, TanStack Query      |
| **UI Components**  | MUI or custom CSS       | Tablet-friendly Material Design components                  |
| **Data Fetching**  | TanStack Query          | Declarative polling, caching, background refetch            |
| **PWA**            | vite-plugin-pwa         | Installable on tablet, offline shell                        |
| **Backend**        | Django 5.x + DRF        | Preferred framework, admin panel, ORM, mature ecosystem     |
| **Task Scheduler** | django-apscheduler      | No Redis needed, stores jobs in DB, lightweight             |
| **Database (dev)** | SQLite                  | Zero-config for local Windows development                   |
| **Database (Pi/cloud)** | PostgreSQL 17       | First-class Django support, multi-user, consistent across environments |
| **Weather API**    | Open-Meteo              | Free, no API key, generous limits                           |
| **Stock API**      | Finnhub                 | Free real-time US quotes, 60 calls/min                      |
| **Calendar**       | ICS feed (Phase 1)      | Simplest integration, works with all providers              |
| **Web Server**     | nginx                   | Serves React static files + reverse proxy to Gunicorn       |
| **WSGI Server**    | Gunicorn (2 workers)    | Production-grade, memory-efficient for Pi                   |
| **Containerization**| Docker + Compose       | Same config for Pi and cloud                                |
| **Data transport**  | HTTP polling (TanStack) | Simple, resilient, sufficient for minute-level updates      |

### What This Stack Does NOT Include (and Why)

| Excluded           | Reason                                                      |
|--------------------|-------------------------------------------------------------|
| Redis              | Not needed; SQLite caching + in-process scheduler suffices  |
| Celery             | Overkill; django-apscheduler handles periodic fetches       |
| WebSockets         | Dashboard doesn't need sub-second updates                   |
| Django Channels    | Only needed for WebSocket support                           |
| Next.js/SSR        | Dashboard is a single-page app; no SEO needs                |
| TypeScript         | Optional enhancement; plain JS is fine to start             |
| SQLite (Pi/cloud)  | PostgreSQL is used past local dev; SQLite only for Windows development |

---

## Appendix A: Key Python Packages

```
django>=5.0
djangorestframework
django-apscheduler
requests
icalendar          # ICS parsing
gunicorn
whitenoise         # Static file serving (alternative to nginx for simple deploys)
django-cors-headers
python-dotenv
psycopg[binary]    # PostgreSQL adapter (psycopg 3)
dj-database-url    # Parse DATABASE_URL env var into Django DATABASES dict
```

## Appendix B: Key npm Packages

```
react
react-dom
@tanstack/react-query
@mui/material (or alternative)
vite
@vite-pwa/vite-plugin-pwa
recharts (or lightweight chart lib for stock sparklines)
```

## Appendix C: Sources

- [React vs Vue vs Svelte Comparison](https://www.frontendtools.tech/blog/best-frontend-frameworks-2025-comparison)
- [Django vs FastAPI vs Flask Decision Matrix](https://medium.com/@anas-issath/django-vs-fastapi-vs-flask-the-2025-framework-decision-matrix-6a8d9741e7ee)
- [Lightweight Django Task Queues Beyond Celery](https://medium.com/@g.suryawanshi/lightweight-django-task-queues-in-2025-beyond-celery-74a95e0548ec)
- [SSE vs WebSockets vs Polling](https://dev.to/haraf/server-sent-events-sse-vs-websockets-vs-long-polling-whats-best-in-2025-5ep8)
- [Open-Meteo Free Weather API](https://open-meteo.com/)
- [Finnhub Stock API](https://finnhub.io/docs/api/rate-limit)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Google Calendar API Auth](https://developers.google.com/workspace/calendar/api/auth)
- [Django on Raspberry Pi -- Gunicorn Memory](https://djangodeployment.readthedocs.io/en/latest/06-gunicorn.html)
- [Render vs Railway vs Heroku 2026](https://thesoftwarescout.com/railway-vs-render-2026-best-platform-for-deploying-apps/)
- [Docker Django React Nginx](https://dev.to/kurealnum/implementing-react-and-django-with-docker-and-nginx-247o)
- [PWA Kiosk Mode on Tablets](https://blog.scalefusion.com/run-progressive-web-applications-pwa-in-kiosk-mode/)
- [ICS Feed vs Real-Time Sync](https://calendarbridge.com/blog/ics-icalendar-feeds-vs-real-time-sync-whats-the-difference/)
