#!/usr/bin/env bash
# pi-health.sh — Print system and application health summary.
# Usage: ssh goodmorning.local /opt/goodmorning/pi/pi-health.sh

set -euo pipefail

APP_DIR="/opt/goodmorning"
VENV="$APP_DIR/backend/.venv/bin"
MANAGE="$VENV/python $APP_DIR/backend/manage.py"
STALE_MINUTES=20

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Load configuration
CONF_FILE="$APP_DIR/pi/pi.conf"
if [[ -f "$CONF_FILE" ]]; then
    # shellcheck source=pi.conf
    source "$CONF_FILE"
fi
GM_DATABASE="${GM_DATABASE:-postgres}"

echo ""
echo -e "${CYAN}Good Morning Dashboard — Health Check${NC}"
echo "────────────────────────────────────────"

# Uptime
echo -e "Uptime:       $(uptime -p | sed 's/^up //')"

# Configuration
echo -e "Config:        database=$GM_DATABASE workers=${GM_WORKERS:-2} desktop=${GM_DESKTOP:-full} vnc=${GM_VNC:-on}"

# Services
echo "Services:"
for svc in goodmorning-web goodmorning-scheduler; do
    short="${svc#goodmorning-}"
    state=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
    since=$(systemctl show "$svc" --property=ActiveEnterTimestamp --value 2>/dev/null || echo "unknown")
    if [[ "$state" == "active" ]]; then
        printf "  %-12s ${GREEN}%s${NC} since %s\n" "$short" "$state" "$since"
    else
        printf "  %-12s ${RED}%s${NC}\n" "$short" "$state"
    fi
done

# Database (works with both SQLite and PostgreSQL)
db_status=$($MANAGE shell -c "
from django.db import connection
from django.apps import apps

models = apps.get_app_config('dashboard').get_models()
total_rows = 0
table_count = 0
for model in models:
    try:
        total_rows += model.objects.count()
        table_count += 1
    except Exception:
        pass
print(f'OK ({table_count} tables, {total_rows} rows)')
" 2>/dev/null || echo "ERROR — cannot connect")
echo -e "Database:      $GM_DATABASE — $db_status"

# Last fetch times
echo "Last fetch:"
$MANAGE shell -c "
from django.utils import timezone
from dashboard.models import WeatherCache, StockQuote, CalendarEvent, NewsHeadline

now = timezone.now()

def ago(dt):
    if dt is None:
        return 'never'
    delta = now - dt
    mins = int(delta.total_seconds() / 60)
    if mins < 1:
        return 'just now'
    elif mins < 60:
        return f'{mins} min ago'
    else:
        return f'{mins // 60}h {mins % 60}m ago'

weather = WeatherCache.objects.order_by('-fetched_at').first()
stock = StockQuote.objects.order_by('-fetched_at').first()
cal = CalendarEvent.objects.order_by('-fetched_at').first()
news = NewsHeadline.objects.order_by('-fetched_at').first()

print(f'  weather      {ago(weather.fetched_at if weather else None)}')
print(f'  stocks       {ago(stock.fetched_at if stock else None)}')
print(f'  calendar     {ago(cal.fetched_at if cal else None)}')
print(f'  news         {ago(news.fetched_at if news else None)}')

# Stale warning
for name, obj in [('weather', weather), ('stocks', stock), ('calendar', cal), ('news', news)]:
    if obj and (now - obj.fetched_at).total_seconds() > $STALE_MINUTES * 60:
        print(f'  \033[1;33m⚠ {name} data is stale (>{$STALE_MINUTES} min)\033[0m')
" 2>/dev/null || echo "  ERROR — cannot query"

# Disk
disk_usage=$(df -h /opt/goodmorning --output=used,size,pcent | tail -1 | awk '{print $1 " / " $2 " (" $3 ")"}')
echo -e "Disk:          $disk_usage"

# Memory
mem_usage=$(free -h | awk '/^Mem:/ {print $3 " / " $2 " (" int($3/$2*100) "%)"}')
echo -e "Memory:        $mem_usage"
echo ""
