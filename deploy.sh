#!/usr/bin/env bash
# deploy.sh — Bootstrap all services for the Good Morning Dashboard.
#
# Usage:
#   ./deploy.sh              Full setup: Docker → backend → frontend → start all
#   ./deploy.sh --services   Start Docker services only (PostgreSQL)
#   ./deploy.sh --backend    Set up backend only (venv, migrate, seed)
#   ./deploy.sh --frontend   Set up frontend only (npm install)
#   ./deploy.sh --start      Start app (backend server + scheduler + frontend dev)
#   ./deploy.sh --test       Run backend tests (starts services first if needed)
#   ./deploy.sh --stop       Stop all running services
#
# Prerequisites: Docker Desktop, Python 3.12+, Node.js 20+

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PIDFILE_DIR="$ROOT_DIR/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
check_docker() {
    if ! command -v docker &>/dev/null; then
        fail "Docker is not installed or not in PATH."
    fi

    if ! docker info &>/dev/null; then
        info "Docker daemon is not running. Attempting to start Docker Desktop..."
        if [[ "$(uname -s)" == *MINGW* || "$(uname -s)" == *MSYS* || "$(uname -s)" == *NT* ]]; then
            # Windows — launch Docker Desktop
            local docker_path="/c/Program Files/Docker/Docker/Docker Desktop.exe"
            if [[ -f "$docker_path" ]]; then
                "$docker_path" &
            else
                fail "Cannot find Docker Desktop at $docker_path. Start it manually."
            fi
        elif [[ "$(uname -s)" == "Darwin" ]]; then
            open -a Docker
        else
            fail "Cannot auto-start Docker on this platform. Start it manually."
        fi

        info "Waiting for Docker daemon (up to 60s)..."
        local elapsed=0
        while ! docker info &>/dev/null; do
            sleep 2
            elapsed=$((elapsed + 2))
            if [[ $elapsed -ge 60 ]]; then
                fail "Docker daemon did not start within 60 seconds."
            fi
        done
        ok "Docker daemon is running."
    else
        ok "Docker daemon is running."
    fi
}

check_python() {
    local py=""
    # Prefer the venv Python if it exists
    if [[ -f "$BACKEND_DIR/.venv/Scripts/python.exe" ]]; then
        py="$BACKEND_DIR/.venv/Scripts/python.exe"
    elif [[ -f "$BACKEND_DIR/.venv/bin/python" ]]; then
        py="$BACKEND_DIR/.venv/bin/python"
    elif command -v python &>/dev/null; then
        py="python"
    elif command -v python3 &>/dev/null; then
        py="python3"
    else
        fail "Python is not installed or not in PATH."
    fi

    local ver
    ver=$($py -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 12 ]]; then
        fail "Python 3.12+ required (found $ver)."
    fi
    ok "Python $ver"
}

check_node() {
    if ! command -v node &>/dev/null; then
        fail "Node.js is not installed or not in PATH."
    fi
    local ver
    ver=$(node -v)
    ok "Node.js $ver"
}

# ---------------------------------------------------------------------------
# Docker / PostgreSQL (skipped when DATABASE_URL is unset — SQLite is default)
# ---------------------------------------------------------------------------
needs_docker() {
    # Docker is only needed when DATABASE_URL points to PostgreSQL
    [[ -n "${DATABASE_URL:-}" ]] && [[ "${DATABASE_URL:-}" == postgres* ]]
}

start_services() {
    if ! needs_docker; then
        ok "Using SQLite — skipping Docker/PostgreSQL."
        return
    fi

    info "Starting Docker services (PostgreSQL)..."
    docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

    info "Waiting for PostgreSQL to accept connections (up to 30s)..."
    local elapsed=0
    while ! docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db \
            pg_isready -U goodmorning -d goodmorning &>/dev/null; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [[ $elapsed -ge 30 ]]; then
            fail "PostgreSQL did not become ready within 30 seconds."
        fi
    done
    ok "PostgreSQL is ready."
}

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------
setup_backend() {
    info "Setting up backend..."

    # Create venv if missing
    if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
        info "Creating Python virtual environment..."
        python -m venv "$BACKEND_DIR/.venv"
    fi

    # Activate venv
    if [[ -f "$BACKEND_DIR/.venv/Scripts/activate" ]]; then
        source "$BACKEND_DIR/.venv/Scripts/activate"
    else
        source "$BACKEND_DIR/.venv/bin/activate"
    fi

    # Install dependencies
    info "Installing Python dependencies..."
    pip install -q -r "$BACKEND_DIR/requirements.txt"

    # Run migrations
    info "Running database migrations..."
    python "$BACKEND_DIR/manage.py" migrate --no-input

    # Seed data (idempotent)
    info "Seeding default data..."
    python "$BACKEND_DIR/manage.py" seed_data

    # Configure Google OAuth if credentials are set
    if [ -n "${GOOGLE_CLIENT_ID:-}" ] && [ -n "${GOOGLE_CLIENT_SECRET:-}" ]; then
        info "Configuring Google OAuth..."
        python "$BACKEND_DIR/manage.py" setup_google_oauth
    fi

    # Collect static files
    info "Collecting static files..."
    python "$BACKEND_DIR/manage.py" collectstatic --no-input --clear -v0

    ok "Backend setup complete."
}

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
setup_frontend() {
    info "Setting up frontend..."
    cd "$FRONTEND_DIR"
    npm install
    ok "Frontend setup complete."
}

# ---------------------------------------------------------------------------
# Start / stop application processes
# ---------------------------------------------------------------------------
mkdir -p "$PIDFILE_DIR"

start_app() {
    info "Starting application..."

    # Backend server
    if [[ -f "$BACKEND_DIR/.venv/Scripts/activate" ]]; then
        source "$BACKEND_DIR/.venv/Scripts/activate"
    else
        source "$BACKEND_DIR/.venv/bin/activate"
    fi

    info "Starting Django dev server on :8000..."
    python "$BACKEND_DIR/manage.py" runserver 0.0.0.0:8000 &
    echo $! > "$PIDFILE_DIR/backend.pid"

    info "Starting APScheduler..."
    python "$BACKEND_DIR/manage.py" run_scheduler &
    echo $! > "$PIDFILE_DIR/scheduler.pid"

    # Frontend dev server
    info "Starting Vite dev server on :5173..."
    cd "$FRONTEND_DIR"
    npm run dev &
    echo $! > "$PIDFILE_DIR/frontend.pid"
    cd "$ROOT_DIR"

    ok "All services started."
    echo ""
    info "Frontend:  http://localhost:5173"
    info "Backend:   http://localhost:8000/api/"
    info "Admin:     http://localhost:8000/admin/  (admin / admin)"
    echo ""
    info "Run './deploy.sh --stop' to shut everything down."
}

stop_app() {
    info "Stopping application..."

    for svc in backend scheduler frontend; do
        local pidfile="$PIDFILE_DIR/$svc.pid"
        if [[ -f "$pidfile" ]]; then
            local pid
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                ok "Stopped $svc (PID $pid)"
            else
                warn "$svc (PID $pid) was not running."
            fi
            rm -f "$pidfile"
        fi
    done

    ok "Application stopped."
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
run_tests() {
    info "Running backend tests..."

    if [[ -f "$BACKEND_DIR/.venv/Scripts/activate" ]]; then
        source "$BACKEND_DIR/.venv/Scripts/activate"
    else
        source "$BACKEND_DIR/.venv/bin/activate"
    fi

    cd "$BACKEND_DIR"
    python -m pytest -v "$@"
    ok "Tests passed."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local mode="${1:-all}"

    echo ""
    echo -e "${CYAN}=== Good Morning Dashboard — Deploy ===${NC}"
    echo ""

    case "$mode" in
        --services)
            if needs_docker; then
                check_docker
            fi
            start_services
            ;;
        --backend)
            check_python
            setup_backend
            ;;
        --frontend)
            check_node
            setup_frontend
            ;;
        --start)
            start_app
            ;;
        --stop)
            stop_app
            ;;
        --test)
            if needs_docker; then
                check_docker
            fi
            start_services
            check_python
            setup_backend
            run_tests "${@:2}"
            ;;
        all|"")
            if needs_docker; then
                check_docker
            fi
            check_python
            check_node
            start_services
            setup_backend
            setup_frontend
            start_app
            ;;
        *)
            echo "Usage: $0 [--services|--backend|--frontend|--start|--stop|--test]"
            exit 1
            ;;
    esac
}

main "$@"
