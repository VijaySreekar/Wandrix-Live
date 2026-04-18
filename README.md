# Wandrix

Starter workspace with a Next.js frontend and a FastAPI backend in separate folders.

## Structure

- `frontend/` - Next.js app router project
- `backend/` - FastAPI service with a Python virtual environment
- `.env` - shared local environment variables for both apps

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

This repo uses a single root `.env` file for local setup.

Set these before wiring real AI logic:

- `NEXT_PUBLIC_API_BASE_URL`
- `FRONTEND_ORIGIN`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `CODEX_LB_BASE_URL`
- `CODEX_LB_API_KEY`
- `OPENAI_MODEL`
- `LANGSMITH_TRACING`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `DATABASE_URL`
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
- `EVENTS_PROVIDER`
- `TICKETMASTER_BASE_URL`
- `TICKETMASTER_CONSUMER_KEY`
- `TICKETMASTER_CONSUMER_SECRET`
- `TRAVEL_CONTENT_PROVIDER`
- `WIKIMEDIA_TRAVEL_BASE_URL`

## API starter endpoints

- `GET /` - welcome payload
- `GET /health` - health check
- `GET /api/v1/ping` - sample API route
- `GET /api/v1/auth/me` - verify Supabase bearer token and return current user
- `POST /api/v1/browser-sessions` - create a browser session container for the signed-in user
- `POST /api/v1/trips` - create a trip conversation and LangGraph thread for the signed-in user
- `GET /api/v1/trips` - list the signed-in user's recent saved trips
- `GET /api/v1/trips/{trip_id}` - load one saved trip
- `GET /api/v1/trips/{trip_id}/draft` - load the structured trip board data
- `PUT /api/v1/trips/{trip_id}/draft` - save the structured trip board data
- `POST /api/v1/trips/{trip_id}/conversation` - send one authenticated chat message through the backend bridge
- `POST /api/v1/packages/generate` - starter AI travel package generator payload

## Frontend routes

- `/chat` - conversation-first planner workspace with sidebar, assistant, and live trip board
- `/flights` - saved-trip flight planning surface
- `/hotels` - saved-trip hotel planning surface
- `/activities` - saved-trip activities and highlights planning surface
- `/trips` - saved trip library
- `/brochure/[tripId]` - brochure-style trip presentation

## Backend structure

- `app/api/routes/` - FastAPI route modules
- `app/core/` - app factory, config, middleware setup
- `app/schemas/` - request and response models
- `app/services/` - package generation business logic
- `app/integrations/` - future AI and third-party clients
- `app/models/` - future database models
- `app/repositories/` - future persistence layer
- `tests/` - backend test files

## Coding Rules

- [Repo agent rules](AGENTS.md)
- [Backend coding rules](docs/backend-coding-rules.md)
- [Frontend coding rules](docs/frontend-coding-rules.md)
- [Architecture](docs/architecture.md)
- [Decision log](docs/decision-log.md)
- [Future improvements](docs/future-improvements.md)
- [UI rules](docs/ui-rules.md)
- [Changelog](CHANGELOG.md)
