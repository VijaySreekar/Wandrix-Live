# Decision Log

## 2026-04-19 - Structured Conversation Memory Inside The Trip Draft

Technical Summary:
- The chat planner now treats raw LangGraph checkpoint messages and persisted structured conversation memory as separate responsibilities.
- Raw messages stay in LangGraph checkpoint state, while the trip draft owns planner state like open questions, decision cards, field memory, mentioned options, rejected options, and turn summaries.
- The planner lifecycle is explicitly defined as `opening`, `collecting_requirements`, `shaping_trip`, `enriching_modules`, and `reviewing`.

Plain-English Summary:
- Wandrix now has a clearer memory model for planning trips.
- The app keeps the actual conversation history in the AI runtime, but it stores the planner’s structured understanding inside the saved trip draft so the board and brochure stay consistent.

## 2026-04-18 - FastAPI And Next.js Split

Technical Summary:
- The repo uses `frontend/` for Next.js and `backend/` for FastAPI.

Plain-English Summary:
- The website and the backend API are kept in separate folders so they can grow cleanly.

## 2026-04-18 - Embedded LangGraph

Technical Summary:
- LangGraph is embedded inside the backend rather than deployed as a separate graph service.

Plain-English Summary:
- The AI workflow engine lives inside the backend app so the architecture stays simpler for now.

## 2026-04-18 - Supabase For Auth And Postgres

Technical Summary:
- Supabase Auth is used for authentication and Supabase Postgres is used as the database.
- FastAPI remains the product backend layer.

Plain-English Summary:
- Supabase handles sign-in and the database, but the app still uses its own backend for the real product logic.

## 2026-04-18 - Provider Mix For Travel Discovery

Technical Summary:
- Chosen providers include Codex-LB, Amadeus, Geoapify, Mapbox, Open-Meteo, Ticketmaster, and Wikimedia/Wikivoyage.

Plain-English Summary:
- The app uses different services for flights, hotels, places, routes, weather, events, and travel content instead of relying on one provider for everything.

## 2026-04-18 - HTML-First Brochure Direction

Technical Summary:
- Brochure output should start as an HTML-first experience before PDF export tooling is introduced.

Plain-English Summary:
- We will first make the final trip plan look beautiful as a web page, and only then turn it into a PDF later.
