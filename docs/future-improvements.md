# Future Improvements

This file is the forward-looking product and technical roadmap for Wandrix.

It is intentionally practical:
- what we should improve next
- why it matters
- what depends on what

Use this as the continuity document when restarting chat sessions.

## Current Baseline

As of `2026-04-18`, Wandrix already has:
- Next.js frontend and FastAPI backend
- Supabase Auth integration
- Supabase Postgres persistence
- browser sessions, trips, and trip drafts
- assistant-style chat workspace
- live trip board
- saved trips library
- brochure route
- live weather from Open-Meteo
- live POI and activity enrichment from Geoapify
- Mapbox geocoding support
- partial Amadeus flight integration

Core product rule:
- `/chat` is the main planning workspace
- module pages like flights, hotels, and activities are supporting reference views, not parallel planning centers

## Highest Priority

These are the most valuable next improvements.

### 1. Make the Planner Smarter Per Turn

The chat loop works, but the planner still needs deeper travel intelligence.

Improve:
- remove or shrink deterministic extraction over time
- move trip understanding toward LLM-first structured parsing
- better extraction of dates, traveler counts, budgets, and styles
- better follow-up questions when information is missing
- stronger structured timeline generation per day
- better use of weather and activity data inside the assistant response
- clearer distinction between "collected", "suggested", and "confirmed" trip details

Why:
- this is the core product value
- better reasoning improves every surface: chat, board, modules, and brochure

Rule:
- do not expand heuristic parsing as the long-term solution
- treat current deterministic extraction as temporary fallback logic that should be reduced

### 2. Finish Live Flights

Flights are only partially live right now.

Improve:
- stabilize Amadeus flow if the test environment becomes usable
- add a second flight provider behind the adapter layer if needed
- handle auth errors, empty results, and server failures gracefully
- enrich flight summaries with layovers, total travel time, and outbound resource links

Why:
- flights are a top-nav surface already
- placeholder flight data will feel weak as the product gets more polished

### 3. Add Real Hotel Discovery

Hotels are still mostly structured placeholders.

Improve:
- add a real hotel discovery source when one is available
- normalize hotel results into internal models
- store neighborhood, stay style, and link-out fields
- use location and travel-time logic so hotels support itinerary planning

Why:
- hotels are one of the main planning modules
- the right board and brochure will feel much stronger with real stays

### 4. Add Real Events

Ticketmaster is configured, but not yet part of the planner flow.

Improve:
- add event discovery tied to trip dates and destination
- surface live events in chat and on the board
- use events as optional itinerary anchors
- show outbound event links in the brochure

Why:
- events can make itineraries feel time-aware and current
- they are a strong differentiator from generic AI trip planning

## Product UX Improvements

### 5. Make the Chat Feel More Premium

Improve:
- better message styling and spacing
- richer planner responses with structured sections
- loading and streaming states that feel calm and intentional
- clearer assistant status such as planning, refining, or waiting for input
- quick actions for follow-up prompts

Why:
- this is a conversation-first product
- the chat must feel like the main workspace, not just a debug surface

### 6. Upgrade the Trip Board

Improve:
- more editorial timeline design
- clearer module sections for flights, hotels, weather, and activities
- stronger hierarchy between confirmed items and draft suggestions
- better desktop and mobile resizing behavior
- route map or movement summaries later

Why:
- the right board is the main visual counterpart to the chat
- it should look alive and trustworthy

### 7. Improve Saved Trips and Re-entry

Improve:
- trip thumbnails or richer trip cards
- better recent trip sorting and grouping
- archived trips and favorites
- draft vs completed trip badges
- search by destination, month, and trip style

Why:
- this becomes more important as users accumulate trips

### 8. Make the Brochure Exceptional

Improve:
- better cover section
- destination imagery strategy
- richer highlights and daily sections
- outbound links for flights, hotels, activities, and events
- better print layout
- export-ready typography and spacing

Why:
- the brochure is the product payoff
- it should feel polished enough to share

## Brochure and Export Roadmap

### 9. Add HTML-to-PDF Export

Do this only after the brochure content and layout feel stable.

Improve:
- print-specific CSS
- PDF generation using a browser-based renderer
- export action from brochure and trip views
- shareable file naming and trip metadata

Why:
- PDF is important, but only after the HTML brochure is strong

### 10. Add Brochure Variants

Possible variants:
- concise summary brochure
- detailed day-by-day brochure
- client-facing luxury brochure
- practical logistics version

Why:
- different travelers want different levels of detail

## AI and LangGraph Improvements

### 11. Expand the Graph Beyond Bootstrap Logic

Right now the graph is useful, but still early-stage.

Improve:
- requirement collection node
- clarification node
- itinerary-building node
- module enrichment node
- review and finalization node
- interruption and resume points

Why:
- this is the long-term brain of the product
- better graph structure will reduce brittle prompt behavior

### 12. Add Better State Semantics

Improve:
- separate inferred values from user-confirmed values
- track confidence per field
- track unresolved planning questions
- track why a recommendation was made

Why:
- this will make both the chat and board more transparent

This is important because:
- it gives us a better replacement for brittle regex-style extraction
- it lets the planner admit uncertainty instead of committing the wrong detail

### 13. Add Better Memory and Resume Behavior

Improve:
- stronger per-trip conversation continuity
- resume exactly where a trip was left off
- support future multi-session planning cleanly

Why:
- the product is inherently multi-turn and iterative

## Provider and Data Improvements

### 14. Add Wikimedia and Editorial Travel Context

Improve:
- city and neighborhood context
- destination overviews
- context-aware highlights
- better explanation of why a place is worth seeing

Why:
- live POI data is useful, but editorial context makes the planner feel more informed

### 15. Add Better Activity Ranking

Improve:
- ranking based on weather
- ranking based on activity style
- ranking based on travel distance from stay area
- morning / afternoon / evening suitability

Why:
- good activities are not just "places nearby"
- they need ordering and relevance

### 16. Add Transport and Local Movement Logic

Improve:
- airport transfer suggestions
- between-stop travel time
- neighborhood clustering
- walking vs transit hints

Why:
- this makes the timeline more realistic

### 17. Add Car Rental as an Optional Module

Possible later module:
- car rental discovery and outbound links
- only for trips where it makes sense

Why:
- useful for road trips and regional travel
- not a first-wave priority

## Quality, Reliability, and Operations

### 18. Add Better Provider Resilience

Improve:
- retries
- fallback messaging
- timeout handling
- provider-level diagnostics
- cached recent results where appropriate

Why:
- external travel APIs will fail sometimes
- the product should degrade gracefully

### 19. Add Better Observability

Improve:
- request correlation by `user_id`, `trip_id`, and `thread_id`
- graph step logging
- provider latency logging
- optional LangSmith or Langfuse tracing

Why:
- debugging AI travel flows gets hard quickly without good tracing

### 20. Add More Real Tests

Improve:
- backend API tests
- repository tests
- trip-draft persistence tests
- graph-state tests
- frontend integration tests for auth and chat boot flow

Why:
- the product is starting to move beyond scaffolding
- stability will matter more with each new provider

## Security and Production Readiness

### 21. Clean Up Secret Handling Before Production

Improve:
- rotate any credentials that were pasted during local setup
- move secrets to a proper deployment secret manager
- tighten backend-only key usage
- review Supabase secret usage carefully

Why:
- current local setup was optimized for speed, not production safety

### 22. Harden Auth and Ownership Rules

Improve:
- protect all trip routes consistently
- verify trip ownership everywhere
- add clearer auth failure UX on the frontend

Why:
- this is necessary before broader usage

### 23. Add Rate Limiting and Abuse Protection

Improve:
- backend rate limiting
- conversation throttling if needed
- provider cost controls

Why:
- AI and travel APIs both have cost and abuse risk

## Nice-to-Have Product Ideas

These are good later, but not immediate.

### 24. Collaboration

Possible improvements:
- share trip with another user
- collaborative editing
- read-only brochure sharing

### 25. Multi-Brochure Themes

Possible improvements:
- family travel theme
- luxury theme
- minimalist itinerary theme

### 26. Maps and Visual Geography

Possible improvements:
- destination map on board
- hotel and activity geography view
- travel path overlay

### 27. Personalization

Possible improvements:
- remembered traveler preferences
- budget sensitivity
- repeat-user style memory

## Recommended Build Order

If resuming work later, this is the recommended sequence:

1. strengthen chat planning intelligence
2. finish one more live provider module
3. improve timeline quality on the trip board
4. improve brochure quality
5. add events
6. add PDF export
7. improve reliability and observability
8. harden production safety

## Short Version

If we want the most impactful next steps, do these first:

1. make the planner smarter per turn
2. finish live flights or add a backup flight source
3. add real hotels
4. wire Ticketmaster events
5. make the board timeline and brochure feel premium
6. add PDF export after the brochure stabilizes
