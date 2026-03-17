# Good Morning Dashboard -- Storage & Persistence Analysis

**Date:** 2026-03-17
**Status:** Research Complete
**Confidence:** High

---

## 1. Executive Summary

PostgreSQL is the standard database for this project across all deployment targets past local Windows development. On Windows dev, SQLite remains the default for zero-config simplicity (with optional PostgreSQL for full parity). On Raspberry Pi, ARM emulation, cloud, and Docker Compose deployments, PostgreSQL provides multi-user support, first-class Django ORM integration, and consistency across environments. The tuned PostgreSQL instance (shared_buffers=64MB, max_connections=20) adds approximately 60-80 MB of RAM on a Pi -- comfortably within the 1GB budget. A hybrid configuration approach is used: environment variables for secrets and infrastructure settings, Django models for per-user dashboard configuration and cached API data.

---

## 2. The Actual SQLite Risk: When Data Gets Lost

### Scenarios Where SQLite Data Disappears

| Scenario | Cause | Likelihood for This Project |
|----------|-------|-----------------------------|
| Docker container rebuild without volume | DB file is in the container's writable layer; `docker compose down && up --build` destroys it | **High if misconfigured** |
| `pip install --force-reinstall` | Only affects packages in site-packages; DB files are never stored there | **Zero** (not applicable) |
| App directory deleted/replaced | If `db.sqlite3` lives inside the project repo and the repo is cloned fresh | **Medium** (common mistake) |
| Network filesystem (NFS/CIFS) | SQLite file locking does not work on network mounts; corruption, not just loss | **Low** (unlikely for this project) |
| SD card corruption on Pi | SD cards wear out; sudden power loss during write can corrupt | **Low-Medium** (mitigated by WAL mode + UPS) |
| Cloud PaaS ephemeral filesystem | Render, Heroku, etc. wipe the filesystem on each deploy | **High on cloud** (must use PostgreSQL or persistent volume) |

### Root Cause Analysis

The concern boils down to one thing: **where the database file lives relative to the application code**. If the DB file is inside the app directory (the Django default of `BASE_DIR / 'db.sqlite3'`), any operation that replaces the app directory (git clone, Docker rebuild, deploy) will destroy the data.

### Mitigation (Simple, Complete)

Configure the database path to a **dedicated data directory outside the application tree**:

```python
# settings.py
import os

DATA_DIR = os.environ.get('GOODMORNING_DATA_DIR', os.path.expanduser('~/goodmorning-data'))
os.makedirs(DATA_DIR, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'db.sqlite3'),
    }
}
```

Docker Compose:
```yaml
services:
  web:
    volumes:
      - app-data:/data    # Named volume, survives container rebuilds
    environment:
      - GOODMORNING_DATA_DIR=/data

volumes:
  app-data:               # Managed by Docker, never deleted by `docker compose down`
                           # Only deleted with explicit `docker compose down -v`
```

With this configuration:
- `docker compose down && docker compose up --build` preserves data
- `pip install --upgrade goodmorning` preserves data (DB is not in site-packages)
- Git pull / fresh clone preserves data (DB is not in repo)
- Only `docker compose down -v` (explicit volume removal) or manual deletion of `~/goodmorning-data` destroys data

**Verdict:** SQLite's persistence risk is a configuration problem, not a technology problem. A 5-line settings change eliminates it entirely.

---

## 3. Django 5.x SQLite Optimizations

Django 5.1+ added native support for SQLite PRAGMA configuration, making SQLite significantly more robust:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'db.sqlite3'),
        'OPTIONS': {
            'init_command': (
                'PRAGMA journal_mode=wal;'
                'PRAGMA busy_timeout=5000;'
            ),
            'transaction_mode': 'IMMEDIATE',
        }
    }
}
```

| PRAGMA | Effect |
|--------|--------|
| `journal_mode=wal` | Write-Ahead Logging: concurrent reads are no longer blocked by writes |
| `busy_timeout=5000` | Wait up to 5 seconds for a lock instead of failing immediately |
| `transaction_mode=IMMEDIATE` | Prevents "database is locked" errors from read-to-write upgrades |

For Django versions before 5.1, use a signal handler in `apps.py`:

```python
from django.db.backends.signals import connection_created

@receiver(connection_created)
def setup_sqlite_pragmas(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=wal;')
        cursor.execute('PRAGMA busy_timeout=5000;')
        cursor.close()
```

---

## 4. Alternative Database Evaluation

### 4.1 PostgreSQL

| Criterion | Assessment |
|-----------|------------|
| **Persistence** | Excellent -- separate server process, data directory independent of app |
| **Pi RAM usage** | ~100-200 MB idle (server process + shared_buffers) |
| **Pi compatibility** | Official ARM64 Docker image; runs well on Pi 4 (2GB+) and Pi 5 |
| **Setup complexity** | Medium -- requires separate container/service, connection string, credentials |
| **Cloud portability** | Excellent -- every cloud platform offers managed PostgreSQL |
| **Django support** | First-class; Django's ORM was designed for PostgreSQL |
| **Concurrent access** | Full MVCC, handles multiple writers without issues |

**When PostgreSQL makes sense for this project:**
- Cloud deployment (Render, Railway, VPS) where the filesystem is ephemeral
- If the dashboard grows to serve multiple users or devices simultaneously
- If you want full-text search, JSON fields, or advanced query features

**When SQLite is preferred instead:**
- Local Windows development without Docker (zero-config convenience, no install needed)

**Pi resource impact:**

| Component | RAM (SQLite) | RAM (PostgreSQL, default) | RAM (PostgreSQL, tuned) |
|-----------|-------------|---------------------------|-------------------------|
| Django + Gunicorn (2 workers) | 100-150 MB | 100-150 MB | 100-150 MB |
| Database server | 0 MB (in-process) | 100-200 MB | 60-80 MB |
| **Total** | **100-150 MB** | **200-350 MB** | **160-230 MB** |

Tuned PostgreSQL settings for Pi: `shared_buffers=64MB`, `work_mem=2MB`, `max_connections=20`, `maintenance_work_mem=32MB`. These are passed via the `postgres` command in Docker Compose.

**Note:** With tuned settings, PostgreSQL uses only ~60-80 MB on a Pi -- well within the 1GB budget alongside Django/Gunicorn (~415-485 MB total stack). The 100-200 MB figure in the "default" column assumes default PostgreSQL configuration.

**Performance on Pi:** PostgreSQL achieves ~200 TPS (TPC-B benchmark) on a Pi 3B, which is roughly 17 million transactions per day -- far more than a morning dashboard needs. Tuning `shared_buffers=128MB` and `work_mem=4MB` keeps memory usage reasonable.

### 4.2 MariaDB / MySQL

| Criterion | Assessment |
|-----------|------------|
| **Persistence** | Same as PostgreSQL -- separate server, independent data directory |
| **Pi RAM usage** | ~80-150 MB idle (slightly less than PostgreSQL) |
| **Pi compatibility** | Official ARM64 Docker image available |
| **Setup complexity** | Medium -- same as PostgreSQL |
| **Cloud portability** | Good, but fewer free managed tiers than PostgreSQL |
| **Django support** | Good but second-class -- some Django features (e.g., `JSONField` with lookups) work better on PostgreSQL |

**Verdict:** MariaDB has a marginally smaller memory footprint than PostgreSQL but offers fewer Django-specific features. PostgreSQL is the better choice if you need a client-server database, because Django's ORM was designed around its capabilities. MariaDB adds complexity without compensating advantages for this project.

### 4.3 MongoDB

| Criterion | Assessment |
|-----------|------------|
| **Persistence** | Separate server process; robust journaling |
| **Pi RAM usage** | ~200-400 MB minimum (WiredTiger cache) |
| **Pi compatibility** | **Pi 4 and earlier: limited to MongoDB 4.4** (ARMv8.0 only); Pi 5: supports MongoDB 8.x |
| **Setup complexity** | High -- unofficial Pi binaries, no Django ORM support |
| **Cloud portability** | Good (MongoDB Atlas has a free tier) |
| **Django support** | **None** -- requires `djongo` (poorly maintained) or abandoning Django's ORM entirely |

**Verdict:** MongoDB is a poor fit. It requires abandoning Django's ORM (a core advantage of the stack), consumes significantly more RAM than SQLite or PostgreSQL, and has limited Pi compatibility. The dashboard's data (weather cache, stock quotes, calendar events, settings) is inherently relational. There is no document-store advantage here.

### 4.4 Redis (as Primary Store)

| Criterion | Assessment |
|-----------|------------|
| **Persistence** | RDB snapshots (periodic) or AOF (append log); hybrid mode available since Redis 4.0 |
| **Pi RAM usage** | ~30-50 MB base, but all data must fit in RAM |
| **Pi compatibility** | Official ARM64 Docker image; runs well |
| **Setup complexity** | High -- no Django ORM integration, manual data modeling |
| **Cloud portability** | Limited free tiers (Upstash, Redis Cloud) |
| **Django support** | Cache backend only; not a Django database backend |

**Persistence modes:**
- **RDB**: Point-in-time snapshots every N seconds. Data loss window = time since last snapshot.
- **AOF**: Logs every write. Options: `everysec` (lose 1 second of data max), `always` (durable but slow).
- **Hybrid (RDB+AOF)**: Recommended for durability. Periodic snapshots + incremental AOF between snapshots.

**Risk:** Redis `fork()` for RDB snapshots can be problematic on Pi with limited RAM (briefly doubles memory usage during snapshot).

**Verdict:** Redis is excellent as a cache layer alongside SQLite/PostgreSQL, but inappropriate as a primary store. It lacks relational modeling, Django ORM integration, and migrations. The dashboard's data (user settings, tracked stocks, calendar URLs) is small, relational, and needs schema migrations -- all things Redis does not provide.

### 4.5 Cloud-Managed PostgreSQL

For cloud deployments where SQLite is not viable (ephemeral filesystem), these are the recommended free tiers:

| Provider | Free Storage | Free Compute | Connections | Gotchas |
|----------|-------------|--------------|-------------|---------|
| **Neon** | 0.5 GB/branch | 100 CU-hours/month (~400 hrs at 0.25 CU) | Pooled | Scale-to-zero (5 min idle timeout = cold start latency) |
| **Supabase** | 500 MB | Shared compute | Pooled (via Supavisor) | 2 free projects; pauses after 1 week of inactivity |
| **Aiven** | 5 GB | 1 vCPU, 1 GB RAM | Standard | Single node; no HA |
| **Render** | 1 GB (for 90 days, then $7/mo) | Shared | Standard | Free tier expires |

**Recommendation for cloud:** **Neon** for indefinite free hosting (generous compute, no expiration) or **Supabase** if you want auth/storage bundled. Both are PostgreSQL-compatible -- Django connects with a standard `DATABASE_URL`.

**Important:** Cloud databases add network latency (50-200 ms per query). The dashboard's architecture (background scheduler caches data, API serves from cache) means the frontend never waits on external DB queries, so this latency only affects the scheduler, which is not latency-sensitive.

---

## 5. File-Based Configuration Alternatives

### 5.1 JSON/YAML Config Files

Store user preferences (tracked stocks, weather location, calendar URLs) in a YAML file:

```yaml
# ~/goodmorning-data/config.yaml
weather:
  latitude: 40.7128
  longitude: -74.0060
  units: fahrenheit

stocks:
  symbols: [AAPL, GOOGL, MSFT, TSLA]
  show_after_hours: false

calendar:
  ics_urls:
    - https://calendar.google.com/calendar/ical/...
```

| Advantage | Disadvantage |
|-----------|-------------|
| Human-readable and editable | No admin UI -- must edit file manually |
| Survives any update (outside app dir) | No validation without custom code |
| Version-controllable (can commit defaults) | No change history / audit trail |
| No database dependency | Must restart app or implement file watching |
| Easy to back up (single file copy) | Cannot be edited from the React frontend |

### 5.2 Environment Variables / .env Files

```bash
# .env
WEATHER_LAT=40.7128
WEATHER_LON=-74.0060
FINNHUB_API_KEY=your_key_here
STOCK_SYMBOLS=AAPL,GOOGL,MSFT,TSLA
```

| Advantage | Disadvantage |
|-----------|-------------|
| Standard 12-factor app practice | Flat structure -- poor for nested config |
| Works everywhere (Docker, Pi, cloud) | Cannot change at runtime without restart |
| `python-dotenv` already in the stack | Not user-friendly for non-developers |
| Ideal for secrets (API keys) | Terrible for list/structured data |

### 5.3 Django-Constance (Database-Backed Dynamic Settings)

django-constance stores settings in the database (or Redis) and exposes them in the Django admin panel:

```python
# settings.py
CONSTANCE_CONFIG = {
    'WEATHER_LATITUDE': (40.7128, 'Weather location latitude'),
    'WEATHER_LONGITUDE': (-74.0060, 'Weather location longitude'),
    'STOCK_SYMBOLS': ('AAPL,GOOGL,MSFT', 'Comma-separated stock symbols'),
    'WEATHER_UNITS': ('fahrenheit', 'Temperature units'),
}
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
```

| Advantage | Disadvantage |
|-----------|-------------|
| Editable from Django admin (no file access needed) | Another dependency |
| Changes take effect immediately (no restart) | Settings stored in DB (tied to DB persistence) |
| Type validation and defaults built in | Flat key-value only (no deep nesting) |
| Cached for performance | Adds complexity vs. simple Django models |

### 5.4 Plain Django Models (Recommended)

Since the dashboard already needs Django models for cached API data, settings can be stored as a Django model:

```python
class DashboardSettings(models.Model):
    weather_latitude = models.FloatField(default=40.7128)
    weather_longitude = models.FloatField(default=-74.0060)
    weather_units = models.CharField(max_length=20, default='fahrenheit')
    stock_symbols = models.JSONField(default=list)
    calendar_urls = models.JSONField(default=list)

    class Meta:
        verbose_name_plural = "Dashboard Settings"

    def save(self, *args, **kwargs):
        # Singleton pattern: only one settings row
        self.pk = 1
        super().save(*args, **kwargs)
```

| Advantage | Disadvantage |
|-----------|-------------|
| No extra dependencies | Slightly more code than django-constance |
| Full Django admin integration | Must implement singleton pattern |
| Rich field types (JSONField for lists) | Tied to DB persistence (same as constance) |
| Included in dumpdata/loaddata | |
| Editable from React frontend via DRF | |
| Migrations handle schema changes | |

**Evolution to multi-user:** The singleton `DashboardSettings` pattern works for a single-user dashboard. For multi-user support, this evolves into a `UserDashboard` model with a `OneToOneField` to `User` and a `widget_layout` JSONField storing each user's widget configuration (which widgets are enabled, their order, and per-widget settings like stock symbols or weather location). See FRAMEWORK_ANALYSIS.md section 6.6 for the full model design.

---

## 6. Recommended Approach: Hybrid Architecture

### The Hybrid Strategy

```
+---------------------------+     +---------------------------+
|   Environment Variables   |     |     PostgreSQL Database   |
|   (.env file)             |     |     (Docker named volume) |
|                           |     |                           |
|  - API keys (secrets)     |     |  - UserDashboard          |
|  - DATABASE_URL           |     |    (per-user widget       |
|  - Debug mode             |     |     layout & settings)    |
|  - Allowed hosts          |     |                           |
|                           |     |  - WeatherCache           |
|  Read once at startup     |     |  - StockQuote             |
|  Never change at runtime  |     |  - CalendarEvent          |
+---------------------------+     |  - APScheduler jobs       |
                                  |                           |
                                  |  Read/write at runtime    |
                                  |  Editable from admin UI   |
                                  |  & React frontend         |
                                  +---------------------------+
```

**Split the data into two categories:**

| Category | Storage | Examples | Why |
|----------|---------|----------|-----|
| **Secrets & infrastructure** | `.env` file (env vars) | API keys, DEBUG, ALLOWED_HOSTS, DB path | Should never be in a database; standard 12-factor practice |
| **User preferences & cached data** | PostgreSQL database (via Django models) | Per-user widget configs (tracked stocks, weather location, calendar URLs), cached API responses | Editable at runtime from admin/frontend; benefits from migrations; consistent across Pi and cloud |

**Why not a separate config file for user preferences?**
- Django admin already provides a free UI for editing settings
- A DRF endpoint can expose settings to the React frontend for editing
- `dumpdata`/`loaddata` backs up everything (settings + cached data) in one step
- One fewer file to manage, back up, and synchronize

### Bootstrap / First-Run Experience

On first run (empty database), Django migrations create the schema, and a data migration or management command seeds default settings:

```python
# In a migration or management command
def seed_defaults(apps, schema_editor):
    Settings = apps.get_model('dashboard', 'DashboardSettings')
    if not Settings.objects.exists():
        Settings.objects.create(
            weather_latitude=40.7128,
            weather_longitude=-74.0060,
            stock_symbols=['AAPL', 'GOOGL', 'MSFT'],
        )
```

After an update/reinstall, the database already has the user's settings (because the DB file persists outside the app directory). Only a truly fresh install triggers the seed.

---

## 7. Backup & Migration Strategies

### 7.1 Django Fixtures (dumpdata / loaddata)

```bash
# Export everything
python manage.py dumpdata --indent 2 > backup.json

# Export specific app
python manage.py dumpdata dashboard --indent 2 > dashboard_backup.json

# Restore
python manage.py loaddata backup.json
```

**Caveats:**
- Exclude `contenttypes` and `auth.Permission` to avoid conflicts: `--exclude=contenttypes --exclude=auth.Permission`
- For databases larger than ~100 MB, `dumpdata` can use excessive RAM
- This project's database will be tiny (settings + cache = a few MB at most)

### 7.2 SQLite File Copy (Simplest Backup)

```bash
# Safe backup while DB is in use (SQLite backup API)
sqlite3 /data/db.sqlite3 ".backup /data/backups/db-$(date +%Y%m%d).sqlite3"

# Or in Python
import sqlite3
src = sqlite3.connect('/data/db.sqlite3')
dst = sqlite3.connect('/data/backups/db-backup.sqlite3')
src.backup(dst)
```

This is the fastest and safest backup method for SQLite. The `.backup` command handles locking correctly even while the database is in use.

### 7.3 SQLite to PostgreSQL Migration (Cloud Deployment)

When moving from local/Pi (SQLite) to cloud (PostgreSQL):

**Option A: Django fixtures (recommended for small databases)**
```bash
# On SQLite
python manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission > data.json

# Change DATABASES to PostgreSQL in settings.py (or set DATABASE_URL)
python manage.py migrate
python manage.py loaddata data.json
```

**Option B: pgloader (for larger databases)**
```bash
pgloader sqlite:///data/db.sqlite3 postgresql://user:pass@host/dbname
```

**Django makes this easy:** Because Django's ORM abstracts the database, switching from SQLite to PostgreSQL requires only changing the `DATABASES` setting. No model or query changes needed.

### 7.4 Docker Volume Strategies

```yaml
# docker-compose.yml
volumes:
  app-data:
    driver: local
    # Data persists in /var/lib/docker/volumes/goodmorning_app-data/_data/
    # Survives: container rebuild, image update, docker compose down
    # Destroyed by: docker compose down -v, docker volume rm
```

**Backup a Docker volume:**
```bash
# Create a tarball of the volume contents
docker run --rm -v goodmorning_app-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/goodmorning-data-backup.tar.gz -C /data .
```

---

## 8. Deployment-Specific Recommendations

| Deployment | Database | Config Approach | Backup Strategy |
|------------|----------|-----------------|-----------------|
| **Windows dev** | SQLite at `~/goodmorning-data/db.sqlite3` | `.env` + DB settings model | Git-ignored data dir; `dumpdata` for portability |
| **ARM emulation** | PostgreSQL in Docker (ARM64 emulated) | `.env` in compose + DB user models | `pg_dump` or `dumpdata` |
| **Raspberry Pi** | PostgreSQL in Docker named volume | `.env` in compose + DB user models | Cron: `pg_dump` to USB/NAS; 7-day retention |
| **Cloud (Render, Railway)** | PostgreSQL (Neon free tier or platform-provided) | Environment variables (platform UI) + DB user models | Platform manages backups; `dumpdata` for export |
| **VPS (DigitalOcean, Hetzner)** | PostgreSQL in Docker named volume (same as Pi) | `.env` + DB user models | Cron: `pg_dump` to S3/object storage |

---

## 9. Decision Matrix

| Criterion | SQLite (well-configured) | PostgreSQL | MariaDB | MongoDB | Redis |
|-----------|--------------------------|------------|---------|---------|-------|
| **Persistence across updates** | Excellent (with data dir) | Excellent | Excellent | Excellent | Good (AOF) |
| **Pi RAM overhead** | 0 MB (in-process) | 100-200 MB | 80-150 MB | 200-400 MB | 30-50 MB |
| **Setup complexity** | None | Medium | Medium | High | Medium |
| **Django ORM support** | Full | Full (best) | Good | None | None |
| **Cross-platform portability** | Excellent | Good | Good | Poor (Pi 4) | Good |
| **Cloud PaaS compatibility** | Poor (ephemeral FS) | Excellent | Good | Good | Limited |
| **Concurrent multi-user** | Limited (1 writer) | Excellent | Excellent | Excellent | Excellent |
| **Backup simplicity** | File copy | pg_dump | mysqldump | mongodump | RDB snapshot |
| **Migration from SQLite** | N/A | Easy (fixtures) | Easy (fixtures) | Rewrite needed | Rewrite needed |

---

## 10. Final Recommendation

**Use PostgreSQL for all deployment targets past local Windows development. Use SQLite for local Windows dev for zero-config convenience.** The specific configuration:

1. **Local dev:** SQLite via default Django settings; optionally PostgreSQL via `DATABASE_URL` for full parity
2. **Pi / ARM emulation / VPS / cloud:** PostgreSQL 17 (Alpine Docker image), tuned for Pi: `shared_buffers=64MB`, `work_mem=2MB`, `max_connections=20`
3. **Docker:** Named volume for PostgreSQL data (`db-data:/var/lib/postgresql/data`)
4. **User settings:** Per-user `UserDashboard` model with `widget_layout` JSONField, exposed via Django admin and DRF API
5. **Secrets:** `.env` file (never in database)
6. **Cloud PaaS:** Omit the `db` Docker service; set `DATABASE_URL` to platform-managed PostgreSQL (Neon free tier recommended)
7. **Backups:** `pg_dump` on a cron schedule (Pi/VPS); platform-managed for cloud; `dumpdata` for cross-backend portability

This approach adds one Docker container (~60-80 MB RAM on Pi with tuned settings) but provides **multi-user support**, **consistency across all environments**, and **battle-tested backup/restore** via standard PostgreSQL tooling.

---

## Sources

- [Docker: Persist the DB](https://docs.docker.com/get-started/workshop/05_persisting_data/)
- [How to Run SQLite in Docker (2026)](https://oneuptime.com/blog/post/2026-02-08-how-to-run-sqlite-in-docker-when-and-how/view)
- [Enabling WAL in SQLite in Django](https://djangoandy.com/2024/07/08/enabling-wal-in-sqlite-in-django/)
- [Django SQLite Benchmark](https://blog.pecar.me/django-sqlite-benchmark/)
- [Django Ticket #24018: SQLite PRAGMA support](https://code.djangoproject.com/ticket/24018)
- [SQLite Write-Ahead Logging](https://sqlite.org/wal.html)
- [PostgreSQL Performance on Raspberry Pi](https://blog.rustprooflabs.com/2019/04/postgresql-pgbench-raspberry-pi)
- [Docker Performance on Different Raspberry Pi Models](https://dl.acm.org/doi/fullHtml/10.1145/3616480.3616485)
- [MariaDB vs PostgreSQL for Low-RAM Systems](https://lowendtalk.com/discussion/184643/which-is-better-for-low-ram-systems-mariadb-or-pg)
- [MongoDB on Raspberry Pi 5](https://andyfelong.com/2025/01/mongodb-8-x-community-edition-on-raspberry-pi-5/)
- [MongoDB ARM Architecture Requirements](https://forums.raspberrypi.com/viewtopic.php?t=348113)
- [Redis Persistence: RDB vs AOF](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
- [django-constance Documentation](https://django-constance.readthedocs.io/)
- [Neon Free Tier Pricing](https://neon.com/pricing)
- [Supabase Pricing](https://getsabo.com/blog/supabase-vs-neon)
- [Top PostgreSQL Free Tiers in 2026](https://www.koyeb.com/blog/top-postgresql-database-free-tiers-in-2026)
- [Django SQLite to PostgreSQL Migration](https://medium.com/djangotube/django-sqlite-to-postgresql-database-migration-e3c1f76711e1)
- [pgloader: SQLite to PostgreSQL](https://isaacs.pw/2018/01/migrating-django-production-database-from-sqlite3-to-postgresql-using-pgloader/)
