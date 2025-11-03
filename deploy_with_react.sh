#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy script variant that ensures React (Vite) build is available to Django
# - Builds frontend (if present)
# - Backups and copies frontend/dist/index.html into Django templates so TemplateView can serve it
# - Runs Django migrations and collectstatic as in the original script
# - Keeps existing behavior for touching wsgi.py / reloading apache

# Defaults (same as original deploy)
APP_DIR="${APP_DIR:-/var/www/MediaWebsite}"
VENV="${VENV:-$APP_DIR/mediasite_env}"
BRANCH="${BRANCH:-main}"

MIGRATE=1
COLLECTSTATIC=1
BOOTSTRAP=0
USE_APACHE=0

# React/Vite bits
FRONTEND_BUILD=1
FRONTEND_DIR="${FRONTEND_DIR:-$APP_DIR/frontend}"
NPM_BIN="${NPM_BIN:-npm}"

# Option: copy built index.html into Django templates (safe default ON)
COPY_INDEX_TO_TEMPLATES=1

# Frontend build logging
PRIMARY_LOG="/var/log/mediawebsite-frontend.build.log"
FALLBACK_LOG="$APP_DIR/frontend.build.log"
if [[ -w "/var/log" ]]; then
  BUILD_LOG="$PRIMARY_LOG"
else
  BUILD_LOG="$FALLBACK_LOG"
fi

# Node version guards (same as original)
REQ1_MAJOR=20; REQ1_MINOR=19
REQ2_MAJOR=22; REQ2_MINOR=12

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Options:
  --no-frontend           Skip building React/Vite frontend.
  --no-copy-index         Don't copy frontend/dist/index.html into Django templates.
  Other options are same as the original deploy script (--branch, --app-dir, --venv, etc).
USAGE
}

log() { printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
trap 'log "ERROR: deploy failed at line $LINENO"; exit 1' ERR

# Arg parsing (minimal subset; extend as needed)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-frontend) FRONTEND_BUILD=0; shift;;
    --no-copy-index) COPY_INDEX_TO_TEMPLATES=0; shift;;
    --frontend-dir) FRONTEND_DIR="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --app-dir) APP_DIR="$2"; VENV="${APP_DIR}/mediasite_env"; shift 2;;
    --venv) VENV="$2"; shift 2;;
    --reload-apache) USE_APACHE=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

log "Starting deploy_with_react: APP_DIR=$APP_DIR, VENV=$VENV, BRANCH=$BRANCH"

cd "$APP_DIR" || { echo "Not found: $APP_DIR"; exit 2; }
[[ -d .git ]] || { echo "This is not a Git repo: $APP_DIR"; exit 2; }

if [[ $BOOTSTRAP -eq 1 && ! -x "$VENV/bin/python" ]]; then
  log "Bootstrapping virtualenv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Virtualenv not found at $VENV. Run with --bootstrap or set VENV."; exit 3
fi

PY="$VENV/bin/python"

# Pull latest code
log "Fetching and resetting to origin/$BRANCH"
git fetch origin "$BRANCH" --tags
git reset --hard "origin/$BRANCH"

# Install Python deps
if [[ -f requirements.txt ]]; then
  log "Installing requirements"
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r requirements.txt
else
  log "No requirements.txt found; skipping pip install"
fi

# Build frontend
if [[ $FRONTEND_BUILD -eq 1 && -d "$FRONTEND_DIR" ]]; then
  if command -v "$NPM_BIN" >/dev/null 2>&1; then
    if command -v node >/dev/null 2>&1; then
      NV_RAW="$(node -v)"
      NV="${NV_RAW#v}"
      IFS='.' read -r MAJOR MINOR PATCH <<<"$NV"

      ok=0
      if   (( MAJOR > 22 )); then ok=1
      elif (( MAJOR == 22 && MINOR >= REQ2_MINOR )); then ok=1
      elif (( MAJOR == 21 )); then ok=1
      elif (( MAJOR == 20 && MINOR >= REQ1_MINOR )); then ok=1
      fi

      if (( ok == 0 )); then
        log "Node $NV_RAW is too old for Vite; aborting frontend build."
        exit 4
      else
        log "Node version OK: $NV_RAW"
      fi
    else
      log "Node not found in PATH; cannot build frontend."; exit 4
    fi

    log "Building frontend in $FRONTEND_DIR"
    pushd "$FRONTEND_DIR" >/dev/null

    if [[ -f package-lock.json ]]; then
      $NPM_BIN ci
    else
      $NPM_BIN install
    fi

    mkdir -p "$(dirname "$BUILD_LOG")"
    log "Writing frontend build log to $BUILD_LOG"
    $NPM_BIN run build 2>&1 | tee -a "$BUILD_LOG"

    popd >/dev/null

    # Optionally copy index.html into Django templates so TemplateView can find it reliably
    if [[ $COPY_INDEX_TO_TEMPLATES -eq 1 ]]; then
      IDX_SRC="$FRONTEND_DIR/dist/index.html"
      IDX_DST="$APP_DIR/templates/index.html"
      if [[ -f "$IDX_SRC" ]]; then
        mkdir -p "$(dirname "$IDX_DST")"
        if [[ -f "$IDX_DST" ]]; then
          TIMESTAMP=$(date +%Y%m%d%H%M%S)
          log "Backing up existing $IDX_DST to ${IDX_DST}.bak.$TIMESTAMP"
          cp -p "$IDX_DST" "${IDX_DST}.bak.$TIMESTAMP"
        fi
        log "Copying $IDX_SRC -> $IDX_DST"
        cp -p "$IDX_SRC" "$IDX_DST"
      else
        log "Built index.html not found at $IDX_SRC; skipping copy-to-templates"
      fi
    else
      log "Skipping copy of index.html to templates (--no-copy-index)"
    fi

  else
    log "npm not found; skipping frontend build (install Node/npm or set NPM_BIN)"
  fi
else
  if [[ $FRONTEND_BUILD -eq 0 ]]; then
    log "Skipping frontend build (--no-frontend)"
  else
    log "No frontend directory at $FRONTEND_DIR; skipping frontend build"
  fi
fi

# Django tasks
if [[ -f manage.py ]]; then
  if [[ $MIGRATE -eq 1 ]]; then
    log "Running migrations"
    "$PY" manage.py migrate --noinput
  else
    log "Skipping migrations (--no-migrate)"
  fi

  if [[ $COLLECTSTATIC -eq 1 ]]; then
    log "Collecting static files"
    "$PY" manage.py collectstatic --noinput
  else
    log "Skipping collectstatic (--no-static)"
  fi
else
  log "manage.py not found; skipping Django steps"
fi

# Reload / touch
if [[ $USE_APACHE -eq 1 ]]; then
  log "Reloading Apache"
  sudo systemctl reload apache2
else
  log "Touching wsgi.py to trigger mod_wsgi reload"
  touch "$APP_DIR/MediaWebsite/wsgi.py"
fi

log "Deploy_with_react complete ✅"
