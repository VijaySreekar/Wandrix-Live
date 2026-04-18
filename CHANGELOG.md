# Changelog

All meaningful changes must be appended here.

Each entry should include:
- Date
- Title
- Technical Summary
- Plain-English Summary
- Files / Areas Touched

## 2026-04-18 - Initial Repository Publishing Safeguards

Technical Summary:
- Expanded the root Git ignore rules to exclude repository-level environment files before the first repository initialization and push.
- Kept support for a future `.env.example` file by explicitly allowing it if one is added later.
- Prepared the workspace for safe publication to a new private GitHub repository without committing local secrets.

Plain-English Summary:
- The project is now safer to publish to GitHub because local environment secrets at the repo root will stay out of version control.
- This protects private keys and config values while still leaving room for a shareable example env file later.

Files / Areas Touched:
- `.gitignore`
- `CHANGELOG.md`

## 2026-04-18 - Future Improvements Roadmap Document

Technical Summary:
- Added a dedicated roadmap document under `docs/` that captures future product, AI, provider, brochure, quality, and production-hardening improvements for Wandrix.
- Structured the roadmap by priority and dependency so future chat sessions can resume from a clear written plan instead of relying on memory.
- Linked the roadmap from the main README alongside the rest of the project docs.

Plain-English Summary:
- The repo now has a proper markdown file listing the major next improvements we should build.
- This gives you a durable place to return to after restarting chat, so the direction is not lost.

Files / Areas Touched:
- `docs/future-improvements.md`
- `README.md`

## 2026-04-18 - LangGraph Checkpoint Table Initialization

Technical Summary:
- Updated FastAPI app startup so the LangGraph Postgres checkpointer runs its `setup()` step before the planning graph is compiled and used.
- This ensures the required LangGraph checkpoint tables are created automatically in the configured Postgres database instead of assuming they already exist.
- Fixes the runtime `psycopg.errors.UndefinedTable: relation "checkpoints" does not exist` failure when sending conversation turns.

Plain-English Summary:
- The backend now creates LangGraph's own persistence tables automatically when it starts.
- That means the chat flow should stop crashing on the missing `checkpoints` table error and can save conversation state properly.

Files / Areas Touched:
- `backend/app/core/application.py`

## 2026-04-18 - Activities Route And Richer Trip Presentation

Technical Summary:
- Added a new authenticated `/activities` planning route and extended the shared trip-module workspace so it can render saved activity and destination-highlight data, not just flights and hotels.
- Updated the top navigation to expose the activities surface directly from the app shell.
- Reworked the live trip board so it surfaces saved weather forecasts, destination highlights, module links, and clearer planning-state sections instead of relying on mostly generic summary cards.
- Upgraded the brochure to present richer trip framing, dedicated weather and highlights sections, and better date and timeline formatting using the structured saved draft.
- Documented the new frontend route surface in the README.

Plain-English Summary:
- The app now has a proper activities page alongside flights and hotels.
- The live trip board and brochure now make much better use of the real weather and places data we already connected, so the product should feel more like a travel planner and less like a rough scaffold.
- This is the UI pass that makes the recent provider work actually visible to you inside the product.

Files / Areas Touched:
- `frontend/src/app/activities/page.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/modules/trip-module-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `README.md`

## 2026-04-18 - Geoapify Activity And POI Enrichment

Technical Summary:
- Added a real Geoapify provider service for nearby activities and POIs, driven by Mapbox geocoding plus Geoapify Places API category searches.
- Mapped trip activity styles into Geoapify category groups so the destination search can respond differently for culture, food, relaxed, outdoors, and other trip tones.
- Switched the activity module generation path in the graph from template-only placeholders to provider-backed `ActivityDetail` records when destination data is available.
- Added safer fallback naming so unnamed POIs still appear as readable trip suggestions instead of raw placeholders.

Plain-English Summary:
- Activities are now the second module using real outside data in the saved trip draft.
- The planner can now pull nearby places from Geoapify and use them as actual trip suggestions, instead of only inventing generic activity blocks.
- This should make the trip board, brochure, and future activity views feel much more grounded in the destination.

Files / Areas Touched:
- `backend/app/integrations/geoapify/client.py`
- `backend/app/services/providers/activities.py`
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-18 - Open-Meteo Weather Enrichment

Technical Summary:
- Added a real backend weather provider service that geocodes trip destinations with Mapbox and fetches daily forecasts from Open-Meteo.
- Switched the weather module generation path in the graph from static placeholders to live forecast-backed `WeatherDetail` records when a destination is available.
- Aligned forecast requests to the trip's actual start and end dates instead of only returning the next few calendar days.
- Kept the previous placeholder path as a fallback if geocoding or forecast fetching fails.

Plain-English Summary:
- Weather is now the first travel module that is feeding real outside data into the saved trip draft.
- The planner can now show actual forecast-style weather details for the trip dates instead of only generic weather placeholders.
- This makes the board and brochure more useful right away, even while flights and hotels are still partially blocked or placeholder-based.

Files / Areas Touched:
- `backend/app/integrations/mapbox/client.py`
- `backend/app/integrations/open_meteo/client.py`
- `backend/app/services/providers/weather.py`
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-18 - Provider Status Diagnostics And Flight Warning Surface

Technical Summary:
- Added a new authenticated backend provider-status endpoint so the frontend can query live provider health in a normalized format.
- Added backend status checking for Amadeus auth, including a clearer error message when credentials are invalid or missing.
- Added frontend provider-status types and API helpers.
- Updated the flights and hotels module workspace to load provider statuses alongside trips, and surface the Amadeus status directly in the planning view.
- Kept the UI on the shared shell/panel token system instead of introducing one-off status colors.

Plain-English Summary:
- The app can now tell you when a live provider is unavailable instead of silently falling back behind the scenes.
- Right now the flights page will clearly show that Amadeus auth is failing, which makes debugging much easier.
- This gives the product a more honest and useful state while provider integration is still being completed.

Files / Areas Touched:
- `backend/app/schemas/provider_status.py`
- `backend/app/services/provider_status_service.py`
- `backend/app/api/routes/providers.py`
- `backend/app/api/router.py`
- `frontend/src/types/provider-status.ts`
- `frontend/src/lib/api/providers.ts`
- `frontend/src/components/modules/trip-module-workspace.tsx`

## 2026-04-18 - Amadeus Flight Enrichment Adapter

Technical Summary:
- Added a backend Amadeus adapter that performs client-credentials authentication, location resolution, and flight-offers search using the official self-service flow.
- Added a provider service that normalizes the first viable Amadeus flight offer into the app's internal `FlightDetail` model.
- Wired the graph bootstrap node to attempt live flight enrichment when the draft has enough route and date information, while preserving the fallback placeholder flow if Amadeus search fails.
- Ran a real provider smoke test with a sample route; the current Amadeus credentials or environment returned `401 Unauthorized`, so the runtime will continue to fall back safely until that auth issue is fixed.

Plain-English Summary:
- The app is now prepared to use real Amadeus flight results instead of only fake placeholder flight data.
- Right now the live Amadeus call is not succeeding because the token request is being rejected, but the planner still works because it falls back safely.
- Once the Amadeus auth issue is fixed, the same flow should start feeding real flight data into the board, brochure, and flights page.

Files / Areas Touched:
- `backend/app/integrations/shared.py`
- `backend/app/integrations/amadeus/client.py`
- `backend/app/services/providers/__init__.py`
- `backend/app/services/providers/flights.py`
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-18 - Richer Draft Module Outputs And Timeline Scaffolding

Technical Summary:
- Expanded the LangGraph bootstrap node so each conversation turn now rebuilds structured draft module outputs for flights, hotels, activities, and weather from the current trip configuration.
- Added deterministic placeholder generation for module outputs and timeline blocks so the saved draft has useful brochure and module-page data even before live provider results are wired in.
- Upgraded timeline construction to merge any model-generated preview items with derived module-driven planning blocks instead of keeping the draft mostly empty.
- Kept the existing draft contract intact, so frontend brochure, trip board, and module pages can immediately benefit from richer saved data without changing their API shape.

Plain-English Summary:
- The planner now saves much better trip structure after each chat turn.
- Even without live flight or hotel search yet, the app can build more meaningful placeholder trip details, which makes the brochure and module pages feel less empty.
- This gives the product a stronger planning flow now while we work toward real provider-backed results next.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-18 - Brochure Route From Saved Trip Drafts

Technical Summary:
- Added a new authenticated brochure route at `/brochure/[tripId]` that loads the saved trip and structured draft through the existing backend APIs.
- Built a brochure component that renders trip framing, stats, flights, stays, planning notes, and grouped day-by-day timeline sections from the persisted draft.
- Added brochure entry points from the live trip board and the saved-trips library so saved trips can now open directly into a brochure-style view.
- Kept the brochure HTML-first so it can become the basis for later PDF export without introducing PDF tooling yet.

Plain-English Summary:
- The app now has a real brochure page for each saved trip.
- You can open it from the trip board or from the saved trips page and see the trip presented in a cleaner, more editorial layout.
- This gives us the final-style destination for the planner without jumping into PDF generation too early.

Files / Areas Touched:
- `frontend/src/components/brochure/trip-brochure.tsx`
- `frontend/src/app/brochure/[tripId]/page.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/trips/trip-library.tsx`

## 2026-04-18 - Flights And Hotels Route Workspaces

Technical Summary:
- Replaced the placeholder `Flights` and `Hotels` pages with authenticated module workspaces backed by saved trip data.
- Added a shared trip-module workspace component that loads the signed-in user's trips, selects a trip from the query string or the most recent saved trip, and reads the structured trip draft for that module.
- Wired both module routes to show route context, trip window, module status, structured output items, and matching timeline blocks for the selected trip.
- Kept the chat workspace as the editing center while making the top-nav module routes useful planning surfaces instead of dead-end placeholders.

Plain-English Summary:
- The `Flights` and `Hotels` pages are no longer empty placeholder screens.
- They now open real views tied to your saved trips, so you can inspect flight-related or hotel-related planning details for each trip.
- This makes the top navigation feel more like a real product and less like unfinished navigation links.

Files / Areas Touched:
- `frontend/src/components/modules/trip-module-workspace.tsx`
- `frontend/src/app/flights/page.tsx`
- `frontend/src/app/hotels/page.tsx`

## 2026-04-18 - Searchable Trip Library And Richer Session Summaries

Technical Summary:
- Extended the trip-list backend response with route, dates, enabled modules, and timeline item count derived from the saved trip draft.
- Added frontend search support for both the chat sidebar and the saved-trips library using the richer trip summary data.
- Upgraded the recent-sessions sidebar items to show route and module context instead of only title and phase.
- Expanded the saved-trips page with filter controls, route/date summaries, module chips, and a cleaner overview of planning progress.

Plain-English Summary:
- Saved trips are easier to browse now because they show real travel context, not just internal IDs.
- You can search by trip title, city, or module, and the sidebar sessions are much more readable.
- The trips page now feels more like an actual travel library instead of a basic list of records.

Files / Areas Touched:
- `backend/app/schemas/trip.py`
- `backend/app/services/trip_service.py`
- `frontend/src/types/trip.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/trips/trip-library.tsx`

## 2026-04-18 - Real Recent Sessions And Saved Trips Library

Technical Summary:
- Added a new authenticated `GET /api/v1/trips` backend route so the frontend can list persisted trips for the current user.
- Added frontend trip-list types and API helpers for loading recent sessions and the full saved-trips library.
- Updated the chat workspace so the sidebar loads real recent trips and can reopen an existing trip through the `trip` query parameter instead of always starting a fresh conversation.
- Replaced the saved trips placeholder route with a real authenticated library page backed by the persisted trip list.
- Updated route docs so the trip-list endpoint is documented alongside the existing trip and trip-draft APIs.

Plain-English Summary:
- The sidebar is no longer pretending to have recent sessions.
- It now shows real saved trips from the database, and clicking one reopens that trip in chat.
- The saved trips page is also real now, so you can browse previous planning sessions instead of landing on a placeholder screen.

Files / Areas Touched:
- `backend/app/schemas/trip.py`
- `backend/app/repositories/trip_repository.py`
- `backend/app/services/trip_service.py`
- `backend/app/api/routes/trips.py`
- `frontend/src/types/trip.ts`
- `frontend/src/lib/api/trips.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/app/trips/page.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `README.md`

## 2026-04-18 - Full Chat Shell And Navigation Redesign

Technical Summary:
- Introduced a proper application shell for the frontend with a persistent top navigation covering Home, Flights, Hotels, Chat, and login access.
- Promoted `/chat` to the main full-height planner route, redirected `/packages` to it, and reduced leftover page padding so the workspace can use the viewport properly.
- Added a dedicated chat sidebar with a new chat action, recent sessions, and a saved trips entry point.
- Restyled the assistant panel and trip board into flatter workspace panels that match the new shell instead of stacked prototype cards.
- Simplified the global background and font fallback usage so the interface feels more product-like and less like a staged demo.

Plain-English Summary:
- The app now looks and behaves much more like a real travel product.
- The planner uses the page properly now, instead of sitting inside a cramped centered layout.
- You can see the product shape you asked for more clearly: top nav, left sidebar, chat in the middle, and the live trip board on the right.

Files / Areas Touched:
- `frontend/src/app/chat/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/auth/sign-out-button.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-18 - Richer Live Board Feedback

Technical Summary:
- Added client-side draft diffing so the workspace can summarize what changed after each conversation turn.
- Expanded the live trip board preview with a latest-changes section, module status cards, and a clearer timeline preview layout.
- Kept the board tied to the persisted draft while making progress more legible through UI summaries rather than only raw field inspection.
- Revalidated the frontend with direct ESLint and a CI-style production build.

Plain-English Summary:
- The right side is now easier to read while you test the planner.
- After each chat turn, the board can tell you what changed instead of forcing you to scan everything manually.
- The board also looks more like a real planning surface now because it has module cards and a stronger trip flow preview.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-18 - Auth UI And Route Protection

Technical Summary:
- Added a real `/auth` page with client-side sign-in and sign-up flows powered by Supabase auth.
- Added a reusable sign-out button component for authenticated screens.
- Protected `/packages` with a server-side redirect to `/auth?next=/packages` when there is no session.
- Updated the homepage so it reflects the signed-in state and routes unauthenticated users into the auth flow instead of dropping them into the planner blindly.
- Preserved the existing auth callback route for email confirmation and redirect handling.

Plain-English Summary:
- The app now actually asks you to sign in.
- If you try to open the planner without a session, it sends you to the auth screen first.
- You can now create an account, sign in, and sign out from the UI instead of needing hidden auth infrastructure only.

Files / Areas Touched:
- `frontend/src/app/auth/page.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `frontend/src/components/auth/sign-out-button.tsx`
- `frontend/src/app/packages/page.tsx`
- `frontend/src/app/page.tsx`

## 2026-04-18 - Model-Backed Graph Turn And Timeline Preview

Technical Summary:
- Replaced the regex-only trip graph turn with a hybrid planner step that combines deterministic extraction and a structured LLM update using the existing Codex-LB chat model.
- Added a structured LangGraph turn schema for travel draft updates, including title, route, budget, travelers, activity styles, modules, and timeline preview items.
- Kept a deterministic fallback path so the trip draft still updates if the model call fails.
- Expanded the live trip board preview to show dates, timeline item count, and the first timeline items generated by the graph-backed turn.
- Revalidated backend compile checks and frontend lint/build after the graph and UI update.

Plain-English Summary:
- The planning graph is now using the AI model to understand trip messages instead of relying only on simple text matching.
- The right-side board is also more useful now because it can show an early timeline preview, not just route and status fields.
- This makes the product feel more like a real AI planner and less like a setup demo.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-18 - LangGraph Turn Wiring And Live Trip Board Preview

Technical Summary:
- Replaced the placeholder graph bootstrap node with a real LangGraph turn processor that updates trip draft configuration and status from conversation input.
- Wired FastAPI app startup to compile and store the planning graph with the Postgres checkpointer context.
- Updated the conversation service to invoke LangGraph with the saved `thread_id`, persist the returned draft state, and return the graph-produced assistant reply.
- Added a visible trip board preview panel on the `/packages` workspace to show route, phase, budget, modules, activity styles, and missing fields from the saved draft.
- Updated the assistant panel so each chat message refreshes the draft after the backend conversation call, making the right-side board visibly react to conversation turns.

Plain-English Summary:
- The conversation is now going through the actual LangGraph layer instead of only a simple backend reply function.
- The chat can update the saved trip draft, and you can now see that happen on the page through the new live trip board preview.
- This is the point where the product starts becoming visibly interactive: type a trip request in chat and the board on the right should change with it.

Files / Areas Touched:
- `backend/app/graph/state.py`
- `backend/app/graph/builder.py`
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/core/application.py`
- `backend/app/services/conversation_service.py`
- `backend/app/api/routes/conversation.py`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-18 - Backend Conversation Bridge For assistant-ui

Technical Summary:
- Added a protected FastAPI conversation endpoint at `POST /api/v1/trips/{trip_id}/conversation`.
- Added typed backend conversation request/response schemas and a service that validates trip ownership before building a reply.
- Swapped the assistant-ui panel from a purely local placeholder response generator to a real authenticated backend call tied to the current `trip_id`.
- Added frontend conversation API helpers and shared conversation types for the new backend contract.
- Kept the backend response intentionally simple so the bridge is real now while leaving room to replace the response builder with LangGraph next.

Plain-English Summary:
- The chat UI is no longer talking only to itself.
- When you send a message in the assistant panel, it now goes through the backend with the signed-in user token and the current trip.
- The replies are still simple on purpose, but the important wiring is done: the conversation is now attached to the real saved trip instead of being a local-only demo.

Files / Areas Touched:
- `backend/app/schemas/conversation.py`
- `backend/app/services/conversation_service.py`
- `backend/app/api/routes/conversation.py`
- `backend/app/api/router.py`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/api/conversation.ts`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `README.md`

## 2026-04-18 - assistant-ui Conversation Shell

Technical Summary:
- Installed `@assistant-ui/react` and added a first-pass conversation shell using the official `LocalRuntime`.
- Added a dedicated assistant panel component with assistant-ui primitives for thread rendering, messages, suggestions, and composer controls.
- Reshaped the `/packages` workspace so the conversation sits on the left and the persisted trip workspace stays on the right.
- Added a shared `PlannerWorkspaceState` type so the assistant shell and workspace panels read from the same bootstrapped trip data.
- Kept the runtime adapter intentionally transparent by returning placeholder responses that confirm the shell is attached to the saved trip and thread without pretending the LangGraph agent already exists.

Plain-English Summary:
- The planner now has a real chat interface on the left instead of just preparation cards.
- The chat is powered by assistant-ui already, but it is still an honest placeholder shell while we wire the real AI orchestration next.
- The page now looks much closer to the final product shape: conversation on one side and trip workspace on the other.

Files / Areas Touched:
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/types/planner-workspace.ts`

## 2026-04-18 - Frontend Trip Workspace Boot Flow

Technical Summary:
- Added token-aware frontend API helpers so the browser can send Supabase bearer tokens to FastAPI.
- Added typed trip fetch and trip draft fetch/save API wrappers.
- Bootstrapped the `/packages` workspace to create or reuse a browser session, create a trip, and load the initial trip draft on the client.
- Removed new hardcoded error colors in the touched workspace UI and used the shared panel/background tokens instead.
- Updated the `/packages` page copy to reflect the persisted workspace boot flow.

Plain-English Summary:
- The frontend can now talk to the protected backend with the logged-in user’s token.
- Opening the planner now prepares a real saved workspace instead of just showing a static form.
- The page now shows the browser session, trip, and thread that were created for the planner, which makes the app ready for the chat layer next.

Files / Areas Touched:
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/browser-sessions.ts`
- `frontend/src/lib/api/trips.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/app/packages/page.tsx`

## 2026-04-18 - Persisted Trip APIs And Draft Storage

Technical Summary:
- Added a reusable SQLAlchemy database dependency for FastAPI route handlers.
- Added repository modules for persisted browser sessions, trips, and trip drafts.
- Replaced placeholder browser session and trip services with database-backed implementations.
- Added authenticated trip fetch, trip draft fetch, and trip draft save endpoints.
- Added `TripDraftUpsertRequest` so the right-side trip board can be saved as structured data.
- Removed the client-supplied browser session `user_id` input so ownership comes only from verified Supabase auth.
- Updated the README endpoint list to reflect the persisted trip and draft APIs.

Plain-English Summary:
- The app no longer makes up browser sessions and trips in memory when these APIs run.
- Signed-in users can now create a browser session, create a real trip record, and save or reload the trip board data from the database.
- Browser sessions also no longer trust a user id coming from the browser body; the backend now owns that from the signed-in account.
- This gives the conversation workspace a proper saved home for the live trip board before we add more AI flow on top.

Files / Areas Touched:
- `backend/app/schemas/trip_draft.py`
- `backend/app/schemas/browser_session.py`
- `backend/app/services/browser_session_service.py`
- `backend/app/services/trip_service.py`
- `backend/app/api/routes/browser_sessions.py`
- `backend/app/api/routes/trips.py`
- `frontend/src/types/browser-session.ts`
- `backend/tests/test_browser_session_service.py`
- `backend/tests/test_trip_service.py`
- `README.md`

## 2026-04-18 - Project Rules And Governance

Technical Summary:
- Added repository-level agent rules in `AGENTS.md`.
- Added architecture documentation, UI rules, and a decision log.
- Established a changelog rule requiring both technical and simple-English explanations for future changes.
- Documented the requirement to use shared global styling tokens for fonts and colors instead of hardcoded feature-level values.

Plain-English Summary:
- We added the main rules for how this project should be built going forward.
- We also created the central project changelog and made it a rule that every important change must be explained both technically and in simple terms.
- The UI rules now clearly say to use shared global color and font settings instead of sprinkling random styles across components.

Files / Areas Touched:
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture.md`
- `docs/decision-log.md`
- `docs/ui-rules.md`
- `docs/backend-coding-rules.md`
- `docs/frontend-coding-rules.md`
- `README.md`
