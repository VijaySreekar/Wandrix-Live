# Architecture

## Product Model

Wandrix is a conversation-first travel planning application.

The product is organized around:
- authenticated user
- browser session
- trip
- LangGraph thread
- trip draft
- brochure output

## Ownership Model

- One authenticated user can have many browser sessions.
- One browser session can have many trips.
- One trip represents one planning conversation.
- One trip owns one LangGraph `thread_id`.
- One trip owns one live trip draft.
- The brochure is a rendered output of the trip draft.

## System Layout

### Frontend

The Next.js frontend is responsible for:
- authentication UI with Supabase Auth
- conversation workspace
- live trip board rendering
- brochure rendering

The frontend should not directly write trip domain data to the database.

### Backend

The FastAPI backend is responsible for:
- authenticated product APIs
- trip ownership and persistence
- LangGraph orchestration
- provider access
- normalization of external data
- final structured data returned to the frontend

### Supabase

Supabase is used for:
- Auth
- Postgres database

Supabase is not the direct frontend product-data API.

### LangGraph

LangGraph is embedded in the backend and is responsible for:
- conversation orchestration
- resumable planning threads
- interrupt/resume flows
- structured planning state transitions

## Source Of Truth

### Chat

The conversation is a user interaction channel.
It is not the canonical source of truth for the trip board.

### Trip Draft

The trip draft is the canonical source of truth for:
- right-side live board
- timeline items
- selected modules
- trip configuration
- conversation memory and planner questions
- brochure readiness

### Conversation Memory

Raw chat messages are owned by LangGraph checkpoint state.

Structured conversation memory is owned by the persisted trip draft and should capture:
- open questions
- decision cards
- confirmed vs inferred facts
- mentioned and rejected options
- recent turn summaries

This split keeps the agent resumable without turning raw chat text into the product source of truth.

### Brochure

The brochure should be derived from structured trip draft data, not reconstructed from freeform messages.

## Provider Roles

- Codex-LB: model generation and reasoning
- Amadeus: flight and hotel discovery
- Geoapify: landmarks, museums, POIs
- Mapbox: geocoding, routing, travel time
- Open-Meteo: weather
- Ticketmaster: events
- Wikimedia/Wikivoyage: editorial enrichment

## Persistence

Initial owned tables:
- `browser_sessions`
- `trips`
- `trip_drafts`

Alembic migrations must only manage app-owned tables.

## UI Architecture

The product should converge toward:
- left panel: conversation
- right panel: live trip board
- final route/view: brochure

The UI should feel like a premium travel-planning experience, not a generic dashboard.
