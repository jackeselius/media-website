# Media Website – Architecture and Deployment Guide

This document explains how the application works end‑to‑end and how to deploy it safely. It’s written for operators and contributors—aimed at being complete without exposing secrets.

## Overview

- UI: React + Vite single‑page app (SPA)
- Backend: Django + Django REST Framework (DRF)
- Auth: DRF token authentication (token stored in browser localStorage)
- Files: Uploaded into `MEDIA_ROOT` and served under `MEDIA_URL`
- Static: React build output (`frontend/dist`) is served as static assets by Django/web server

The project is “React‑first UI + DRF APIs.” Django serves the SPA entry, APIs, admin, and media files.

## Repository layout (key paths)

- `MediaWebsite/` – Django project (settings, URLs, WSGI/ASGI)
- `media/` – File model and REST API
  - `media/models.py` – File model (`filename`, `description`, `owner`, `icon`, `file`)
  - `media/api/` – DRF API
    - `serializers.py` – `FileSerializer`
    - `views.py` – `FileViewSet` (list/create/delete)
    - `urls.py` – router exposing `/api/media/files/`
- `accounts/api/` – Auth API (token login/logout/user)
- `frontend/` – React application (Vite)
  - `src/contexts/AuthContext.jsx` – token storage and user session state
  - `src/utils/api.js` – axios instance (baseURL, CSRF header, 401 redirect to `/login`)
  - `src/components/Auth/ProtectedRoute.jsx` – route guard for authenticated pages
  - `src/components/Layout/MainLayout.jsx` – header/sidebar and login/logout UI
  - `src/pages/` – SPA pages (Home, Files, Upload, About, Login, team pages)

Removed/retired (server‑rendered HTML): legacy Django templates and apps used before the SPA were removed or disabled.

## Request flow

1. A browser navigates to `/` → Django returns `frontend/dist/index.html`.
2. React Router controls client‑side routes (e.g., `/files`, `/upload`, `/about`).
3. When the user logs in at `/login`, the SPA calls `POST /api/auth/login/` and stores the returned token in `localStorage` and as the `Authorization: Token <token>` header for future requests.
4. File actions call the JSON API:
   - GET `/api/media/files/` → list current user’s files
   - POST `/api/media/files/` (multipart) → upload a new file (and optional icon)
   - DELETE `/api/media/files/:id/` → delete a file by id
5. Uploaded files are stored under `MEDIA_ROOT` (e.g., `data/files/…`) and served at `MEDIA_URL` (`/data/...`).

## Authentication

- Token authentication via DRF.
- Token is saved to `localStorage` by `AuthContext` and added to every axios request header.
- If the API returns 401, the axios interceptor redirects to the SPA `/login` page.
- Logout calls `POST /api/auth/logout/` then clears the token/client state.

Endpoints:
- `POST /api/auth/login/` → `{ token }`
- `POST /api/auth/logout/` → `200 OK` (token invalidated if present)
- `GET  /api/auth/user/` → `{ username, email }` (requires token)

## Files API

- Base path: `/api/media/files/`
- Requires authentication.
- Query returns only files owned by the current user (scoped by `owner == request.user.username`).
- Serializer returns absolute/relative URLs for `icon` and `file` fields suitable for `<img src>` and `<a href>`.

Operations:
- `GET    /api/media/files/` → `[{ id, filename, description, owner, icon, file }]`
- `POST   /api/media/files/` (multipart/form-data)
  - Fields: `file` (required), `description` (optional), `icon` (optional), `filename` (optional; defaults to uploaded file name)
- `DELETE /api/media/files/:id/` → `204 No Content`

## Frontend routes (SPA)

- `/` – Home (greets user if authenticated; shows login link if not)
- `/files` – File list (ProtectedRoute; shows only when logged in)
- `/upload` – Upload file (ProtectedRoute)
- `/about`, `/about/*` – Public profile pages
- `/login` – SPA login page
- `/signup` – Redirects to `/login` (signup disabled)

The left sidebar is mobile‑only; desktop shows a single header bar with navigation and auth status.

## Django settings highlights

- `DEBUG = False` (production) – Tailor ALLOWED_HOSTS accordingly.
- `STATICFILES_DIRS` includes `frontend/dist` so Django can reference built assets.
- Templates search path includes `frontend/dist` (so `/` can serve `index.html`).
- `MEDIA_ROOT = data/` and `MEDIA_URL = /data/` – Nginx should serve `/data/` directly.
- `REST_FRAMEWORK` default permissions = `IsAuthenticated`; token + session auth enabled.
- `CSRF_TRUSTED_ORIGINS` must include your HTTPS origins (e.g., `https://egmedia.org`).

Security note: never commit secrets (SECRET_KEY, DB password, etc.) to git. Use environment variables or a secrets manager in production.

## Web server (nginx) outline

A minimal nginx map (adjust to your server paths/services):

```nginx
server {
  listen 80;
  server_name egmedia.org www.egmedia.org;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name egmedia.org www.egmedia.org;

  # ssl_certificate ...;  # managed by certbot or your TLS provider
  # ssl_certificate_key ...;

  # Static build assets (React) and collected static (if any)
  location /static/ {
    alias /srv/media-website/static/; # STATIC_ROOT
    access_log off;
  }

  # Media uploads
  location /data/ {
    alias /srv/media-website/data/; # MEDIA_ROOT
    access_log off;
  }

  # Django app (gunicorn/uvicorn upstream)
  location / {
    proxy_pass http://127.0.0.1:8000; # your app server
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## Deployment guide

There are two supported patterns—pick one per environment.

### Option A: Build on the server (default)

Use this when the server has (or can install) Node 20+.

1) First-time prerequisites on the server
- Python3, pip, virtualenv/venv
- PostgreSQL access
- nginx and a process manager (systemd, supervisor) for your Django app server

2) Run the deploy script (over SSH)

```bash
# One-time or after server rebuild (install/upgrade Node to 20.x)
./deploy_with_react.sh --install-node

# Routine deploys (Node already installed)
./deploy_with_react.sh
```

What the script should do (conceptually):
- Pull latest git
- Backend: create/activate venv → `pip install -r requirements.txt` → `python manage.py migrate` → `collectstatic`
- Frontend: `npm ci` (fallback to `npm install` if lock mismatch) → `npm run build`
- Restart app service(s)

When to use `--install-node`:
- The server shows `node -v` missing or `< 20`
- You’re okay with the script installing Node via NodeSource (Ubuntu/Debian; requires sudo)
- Not needed on every deploy—usually once per server or upon major Node upgrade

If your server manages Node with `nvm/asdf`, install Node there and omit `--install-node` to avoid PATH conflicts.

3) Smoke test after deploy
- Load `/` and hard-refresh (Ctrl+F5)
- Login at `/login` and confirm the header shows “Welcome, <user>”
- Visit `/files` (should load your list or empty state)
- Upload at `/upload` and confirm a new row appears

### Option B: Build locally and ship `frontend/dist`

Use this when you prefer not to install Node on the server.

Local machine:
```bash
npm ci
npm run build
# Copy frontend/dist to the server path used by Django (STATICFILES_DIRS contains frontend/dist)
```
Server:
```bash
# Run backend steps only (migrations, collectstatic, restart). If your script
# always builds the frontend, modify it to skip when dist exists, or add a flag.
./deploy_with_react.sh
```

## Troubleshooting

- “n.map is not a function” on Files page
  - The UI tried to `.map()` over a non-array (e.g., HTML error). Check Network tab—ensure the call is to `/api/media/files/` and returns JSON array. The page now guards against bad shapes and shows an error rather than crashing.

- 401 Unauthorized
  - Token missing/expired. Log in at `/login`. The axios interceptor redirects to `/login` on 401.

- Upload 403/CSRF issues
  - Confirm `CSRF_TRUSTED_ORIGINS` includes your domain and that HTTPS is used in production. Ensure token auth is present.

- Static assets not updating
  - Clear cache (Ctrl+F5). Ensure `npm run build` ran and `frontend/dist` exists on the server. Confirm nginx serves the correct static path.

## Development notes

- Keep `package-lock.json` committed for deterministic installs.
- Use Node 20.x locally to match server builds.
- Run a local dev server (optional) with Vite for the SPA and Django for APIs; configure CORS as needed (DEBUG only).

## Roadmap / nice-to-haves

- Add pagination to the Files API and UI (DRF pagination is already enabled globally)
- Pre-sign URLs or range requests for very large files
- Add health check endpoint and a small post-deploy smoke test script
- CI pipeline to build and deploy automatically

## Security hygiene

- Don’t commit secrets (SECRET_KEY, DB creds). Inject via environment variables.
- Use HTTPS in production; set `CSRF_TRUSTED_ORIGINS` and secure cookies accordingly.
- Limit admin access; use strong passwords and 2FA where possible.

---
If anything in this README gets out of sync with the code or your deploy flow, update both together. It’s your living runbook.
