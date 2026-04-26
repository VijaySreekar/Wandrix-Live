# Wandrix

Wandrix is a conversation-first AI travel planner. The product centers on a
chat workspace for planning trips, a live structured trip board, and a polished
brochure-style output that can be saved or exported.

## Stack

- Next.js frontend
- FastAPI backend
- Supabase Auth
- Supabase Postgres for app persistence
- LangGraph embedded in the backend planning runtime
- Alembic for app-owned database migrations

## Repository Layout

- `frontend/` - Next.js app router application
- `backend/` - FastAPI application, migrations, services, integrations, and tests
- `.env.example` - safe environment template for local setup
- `docker-compose.yml` - local container orchestration for frontend and backend

## Prerequisites

- Node.js 22 or newer
- Python 3.14 or newer
- Docker Desktop, if using the Docker setup
- A Supabase project for Auth and Postgres
- API credentials for the AI runtime and any optional travel providers you enable

## Environment Setup

Copy the example file and fill in real local values:

```bash
cp .env.example .env
```

The root `.env` is used for local development only. Do not commit real secrets.

Frontend public variables:

- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

Backend variables:

- `APP_ENV`
- `FRONTEND_ORIGIN` or `FRONTEND_ORIGINS`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `CODEX_LB_BASE_URL`
- `CODEX_LB_API_KEY`

Optional provider variables for flights, hotels, maps, weather, events, and
travel content are listed in `.env.example`.

Use separate testing and production values. Testing and production should have
separate Supabase projects or databases, separate frontend/backend domains, and
separate provider keys where possible.

When `APP_ENV=production`, the backend validates the required production
configuration at startup and fails fast if core values are missing or still set
to local placeholders.

## Local Setup

Install and run the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
alembic upgrade head
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

Install and run the frontend in a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

The frontend runs at `http://localhost:3000`.

## Docker Setup

Docker is optional, but it gives reviewers a single-command way to run the app
once `.env` is configured.

```bash
cp .env.example .env
# Edit .env with real Supabase, database, and AI runtime values.

docker compose build
docker compose up
```

Run migrations from another terminal before using authenticated trip flows:

```bash
docker compose exec backend alembic upgrade head
```

Container URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`

The Docker setup uses the database configured by `DATABASE_URL`; it does not
start a local Postgres container by default because the application is designed
to use Supabase Postgres.

## Deployment Notes

Recommended environment split:

- Testing frontend on Vercel, connected to the testing backend and testing Supabase project
- Testing backend on Render, with `APP_ENV=testing`
- Production frontend on Vercel, connected to the production backend and production Supabase project
- Production backend on Render, with `APP_ENV=production`

Set frontend variables in Vercel and backend variables in Render. For custom
domains, point the app domain to Vercel and the API domain to Render, then set:

- Vercel `NEXT_PUBLIC_SITE_URL` to the frontend domain
- Vercel `NEXT_PUBLIC_API_BASE_URL` to the backend domain
- Render `FRONTEND_ORIGINS` to the allowed frontend domains

For production Docker deploys, build the frontend image with the final public
URLs because `NEXT_PUBLIC_*` values are compiled into the Next.js bundle.

## Useful Commands

Frontend:

```bash
cd frontend
npm run lint
npm run build
npm run start
```

Backend:

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app tests
python -m pytest tests/test_config.py tests/test_structure.py tests/test_llm_model_routing.py
alembic upgrade head
```

Docker:

```bash
docker compose config
docker compose build
docker compose up
docker compose exec backend alembic upgrade head
```

## Main Routes

- `/chat` - primary planning workspace
- `/trips` - saved trip library
- `/flights` - saved-trip flight reference view
- `/hotels` - saved-trip hotel reference view
- `/activities` - saved-trip activities and highlights reference view
- `/profile` - account profile and travel defaults
- `/brochure/[tripId]` - saved brochure view with version history and PDF download

## API Surface

- `GET /health` - backend health check
- `GET /api/v1/ping` - API readiness route
- `GET /api/v1/auth/me` - verify Supabase bearer token and return current user
- `POST /api/v1/browser-sessions` - create a browser session for the signed-in user
- `POST /api/v1/trips` - create a trip conversation and planning thread
- `GET /api/v1/trips` - list saved trips
- `GET /api/v1/trips/{trip_id}` - load one saved trip
- `GET /api/v1/trips/{trip_id}/draft` - load structured trip board data
- `PUT /api/v1/trips/{trip_id}/draft` - save structured trip board data
- `GET /api/v1/trips/{trip_id}/brochures` - list saved brochure versions
- `GET /api/v1/trips/{trip_id}/brochures/latest` - load latest brochure snapshot
- `GET /api/v1/trips/{trip_id}/brochures/{snapshot_id}` - load one brochure snapshot
- `POST /api/v1/trips/{trip_id}/brochures/{snapshot_id}/pdf` - render brochure PDF
- `POST /api/v1/trips/{trip_id}/conversation` - send an authenticated chat message
