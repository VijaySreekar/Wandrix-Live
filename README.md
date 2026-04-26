# Wandrix

Conversation-first AI travel planner with a Next.js frontend, FastAPI backend,
Supabase Auth/Postgres persistence, and an embedded LangGraph planning runtime.

## Structure

- `frontend/` - Next.js app router project
- `backend/` - FastAPI service with a Python virtual environment
- `.env.example` - safe local environment template
- `.env` - local environment variables for both apps, never commit real secrets

## Run the frontend

```powershell
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`.

## Run the backend

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

The backend will start on `http://127.0.0.1:8000`.

## Environment

Copy `.env.example` to `.env` for local development. The root `.env` is loaded
by both the backend and frontend config locally, but production values should be
set in the hosting platform instead of committed.

Frontend production variables belong in Vercel:

- `NEXT_PUBLIC_SITE_URL` - deployed frontend URL, for example `https://app.example.com`
- `NEXT_PUBLIC_API_BASE_URL` - deployed FastAPI URL, for example `https://api.example.com`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

Backend production variables belong in Render:

- `FRONTEND_ORIGIN`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `CODEX_LB_BASE_URL`
- `CODEX_LB_API_KEY`
- `OPENAI_MODEL`
- `QUICK_PLAN_MODEL`
- `QUICK_PLAN_REASONING_EFFORT`
- `QUICK_PLAN_STAGE_ONE_ONLY`
- `LANGSMITH_TRACING`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `AMADEUS_ENV`
- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `WEATHER_PROVIDER`
- `OPEN_METEO_BASE_URL`
- `MAP_PROVIDER`
- `MAPBOX_BASE_URL`
- `MAPBOX_ACCESS_TOKEN`
- `ACTIVITIES_PROVIDER`
- `POI_PROVIDER`
- `GEOAPIFY_BASE_URL`
- `GEOAPIFY_API_KEY`
- `HOTEL_PROVIDER`
- `RAPIDAPI_KEY`
- `RAPIDAPI_XOTELO_BASE_URL`
- `RAPIDAPI_AGODA_BASE_URL`
- `RAPIDAPI_HOTELS_COM_BASE_URL`
- `RAPIDAPI_TRAVEL_ADVISOR_BASE_URL`
- `EVENTS_PROVIDER`
- `TICKETMASTER_BASE_URL`
- `TICKETMASTER_CONSUMER_KEY`
- `TICKETMASTER_CONSUMER_SECRET`
- `TRAVEL_CONTENT_PROVIDER`
- `WIKIMEDIA_TRAVEL_BASE_URL`
- `TRAVELPAYOUTS_BASE_URL`
- `TRAVELPAYOUTS_API_TOKEN`

Use separate values for testing and production. At minimum, testing and
production should have separate Supabase projects/databases, distinct
`DATABASE_URL` values, and distinct frontend/backend domains.

## API endpoints

- `GET /` - welcome payload
- `GET /health` - health check
- `GET /api/v1/ping` - API readiness route
- `GET /api/v1/auth/me` - verify Supabase bearer token and return current user
- `POST /api/v1/browser-sessions` - create a browser session container for the signed-in user
- `POST /api/v1/trips` - create a trip conversation and LangGraph thread for the signed-in user
- `GET /api/v1/trips` - list the signed-in user's recent saved trips
- `GET /api/v1/trips/{trip_id}` - load one saved trip
- `GET /api/v1/trips/{trip_id}/draft` - load the structured trip board data
- `PUT /api/v1/trips/{trip_id}/draft` - save the structured trip board data
- `GET /api/v1/trips/{trip_id}/brochures` - list saved brochure versions for a trip
- `GET /api/v1/trips/{trip_id}/brochures/latest` - load the latest saved brochure snapshot
- `GET /api/v1/trips/{trip_id}/brochures/{snapshot_id}` - load one brochure version
- `POST /api/v1/trips/{trip_id}/brochures/{snapshot_id}/pdf` - render and download a brochure PDF
- `POST /api/v1/trips/{trip_id}/conversation` - send one authenticated chat message through the backend bridge

## Frontend routes

- `/profile` - detailed account profile and travel-defaults editing
- `/chat` - conversation-first planner workspace with sidebar, assistant, and live trip board
- `/flights` - saved-trip flight reference view
- `/hotels` - saved-trip hotel reference view
- `/activities` - saved-trip activities and highlights reference view
- `/trips` - saved trip library
- `/brochure/[tripId]` - latest saved brochure snapshot with version history and PDF download

## Backend structure

- `app/api/routes/` - FastAPI route modules
- `app/core/` - app factory, config, middleware setup
- `app/schemas/` - request and response models
- `app/services/` - application orchestration and domain services
- `app/integrations/` - AI, travel provider, map, weather, and content clients
- `app/models/` - app-owned SQLAlchemy persistence models
- `app/repositories/` - persistence access layer for app-owned tables
- `tests/` - backend test files

## Coding Rules

- [Repo agent rules](AGENTS.md)
- [Backend coding rules](docs/backend-coding-rules.md)
- [Frontend coding rules](docs/frontend-coding-rules.md)
- [Architecture](docs/architecture.md)
- [Chat planner spec](docs/chat-planner-spec.md)
- [Decision log](docs/decision-log.md)
- [Future improvements](docs/future-improvements.md)
- [Planner improvement plan](docs/planner-improvement-plan.md)
- [UI rules](docs/ui-rules.md)
- [Changelog](CHANGELOG.md)
