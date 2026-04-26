# Future Improvements

This file is the forward-looking product and technical roadmap for Wandrix.

It is intentionally practical:
- what we should improve next
- why it matters
- what depends on what

Use this as the continuity document when restarting chat sessions.

For the current target planner structure, use:
- `docs/project-materials/chat-planner-spec.md`

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
- follow the `docs/project-materials/chat-planner-spec.md` lifecycle and memory model
- make turn understanding more reliable without reverting to deterministic parsing
- improve follow-up questions, decision cards, and confirmation semantics
- strengthen provider activation discipline and summary-first board behavior
- improve how the assistant uses profile context softly in the opening phase

Why:
- this is the core product value
- better reasoning improves every surface: chat, board, modules, and brochure

Rule:
- do not introduce deterministic extraction back into the planner
- improve the structured LLM flow instead of adding regex or keyword parsing

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

## Advanced Planning Roadmap

This section captures the intended product direction for `Advanced Planning`.

Core rule:
- `Quick Plan` should stay the fast first-draft mode
- `Advanced Planning` should become the full trip-building and trip-organizing mode
- Wandrix should remain a `selection and organization` product, not a booking platform
- real checkout, payment, and reservation confirmation should happen outside Wandrix

### Make Advanced Planning a Real Planning Mode

Right now Advanced Planning still falls back to Quick Plan behavior.

That is acceptable temporarily, but it is not the intended end state.

Advanced Planning should mean:
- Wandrix helps choose real flights, hotels, activities, events, and practical trip structure
- Wandrix resolves tradeoffs more deliberately instead of jumping straight to a first draft
- Wandrix keeps a clear record of what is recommended, what is selected, and what is still undecided
- Wandrix never implies that a selected option is already booked unless the user explicitly confirms that later

Advanced Planning should proceed in stages:

1. Confirm the trip brief
- destination
- timing
- origin
- travelers
- trip style
- budget posture
- module scope
- any hard constraints

2. Choose the planning anchor
- flights-first for short or origin-sensitive trips
- stay-area-first for city breaks where neighborhood choice shapes the trip
- event-first when one date-bound activity should anchor the itinerary
- activity-style-first when the user mostly cares about trip tone and pacing

3. Build the trip skeleton before full detail
- arrival and departure shape
- likely stay strategy
- rough day themes
- pacing level
- optional day trip logic

4. Resolve major tradeoffs one by one
- central but pricier stay vs calmer but farther stay
- direct but earlier flight vs slower cheaper option
- packed highlights vs slower local pace
- one-base trip vs split-area trip

5. Enrich modules in sequence instead of all at once
- flights when flight practicality matters most
- hotels when stay choice shapes the trip
- activities and events once the structure is stable
- transport and local movement once the selected components are clearer

6. Re-plan around real selected components
- late-arrival flight should soften Day 1
- selected hotel area should influence activity ranking
- fixed event timing should shift nearby day structure
- return timing should affect the final evening and final morning

7. Present a reviewed plan before finalization
- what is selected
- what is still flexible
- what alternatives were rejected
- what tradeoffs were chosen
- what the user should confirm before locking the brochure-ready trip

Why this matters:
- this is how Wandrix becomes more than an itinerary generator
- the user should feel like the agent is helping them build the actual trip, not just sketching one

### Resolve Working Dates Before Anchor Choice

Advanced Planning should not jump straight from a rough brief into the four main anchors when timing is still vague.

If the user says things like:
- `late March`
- `around five nights`
- `long weekend in May`
- `sometime next month`

Wandrix should first run a dedicated `working date resolution` step before it asks whether flights, stay, trip style, or activities should lead the trip.

That step should mean:
- generate `3` concrete date options from the rough timing
- explain in chat why those windows are plausible interpretations
- show those options on the board as the working date-choice workspace
- let the user choose one or use `Pick for me`
- require an explicit `Proceed with this trip window` confirmation before moving on

Core rule:
- the chosen trip window is a `working date lock`, not a permanent lock

That means:
- it is concrete enough to unlock better stay, hotel, flight, budget, and activity planning
- it can still be revised later in chat if the user changes their mind
- the board should complement the reasoning, not replace it

The intended Advanced Planning flow becomes:
1. shared intake
2. resolve the working trip window if timing is still rough
3. confirm the working date window
4. only then show the four Advanced anchors

### Build Stay As The First Revisable Decision

The first real deep Advanced Planning path should be `stay`.

This should not begin as hotel inventory or a booking flow.

The first stay implementation should be:
- `area-strategy selection`
- `4` stay strategy options on the board
- each option representing a `working stay direction`, not a hotel
- each option being explained in plain traveler language

Core rule:
- Advanced Planning decisions should be treated as `working decisions`, not one-way locks

That means:
- a selected stay should mean `this is the current direction Wandrix is building around`
- it should not mean `the hotel is chosen`
- it should not mean `anything is booked`
- it should remain revisable if later planning evidence makes it weaker

Later planner evidence should be allowed to challenge the selected stay, including:
- activity anchors
- trip style decisions
- arrival and departure practicality
- one-base versus split-stay logic

When that happens, Wandrix should not silently overwrite the selection.

Instead it should:
- explain the tension in chat
- reflect the problem on the board
- mark the stay as `selected`, `strained`, or `needs review`
- suggest a better stay strategy if the old one no longer fits well

This pattern matters because it should become the reusable model for later anchors too:
- flights
- activities
- trip style

So the first stay implementation should establish the planner pattern of:
- recommend
- select
- keep as a working decision
- review later if the trip logic changes

### Turn Selected Stay Into A Hotel Shortlist

Once the user picks a stay strategy, Advanced Planning should move immediately into a hotel shortlist inside that selected stay direction.

That next step should mean:
- keep the selected stay strategy pinned and visible on the board
- use live hotel discovery first when the destination and timing are ready
- normalize those hotel results into planner-owned hotel cards
- explain each hotel in relation to the selected stay direction, not as generic hotel facts
- let the user choose a `working hotel selected` option

Core rule:
- selected hotel is still a `working decision`, not a booking and not a permanent lock

That means:
- `selected_stay_option_id` still means the current area strategy
- `selected_hotel_id` means the current working hotel inside that strategy
- neither should imply the hotel is booked
- later activities, flights, or trip structure can still strengthen or strain that hotel choice

The first hotel shortlist should:
- try live hotel discovery first
- fall back to planner-safe hotel suggestions only if live hotel results are unavailable or too weak
- keep all hotel cards clearly framed as fitting the chosen stay direction
- keep the selected stay strategy visible while the user is choosing hotels

The board should then support:
- `advanced_stay_hotel_choice`
- `advanced_stay_hotel_selected`
- later `advanced_stay_hotel_review`

This matters because:
- stay strategy without real hotel follow-through feels unfinished
- raw hotel cards without stay strategy feel shallow
- the product needs both layers to feel genuinely intelligent

So the intended planner pattern becomes:
1. choose the stay direction
2. shortlist hotels inside that direction
3. select a working hotel
4. review it later if newer trip evidence makes it weaker

### Keep Booking External

Advanced Planning should help the user decide what to choose, but not complete the booking inside Wandrix.

That means Wandrix should do:
- ranking and comparison
- recommendation rationale
- option selection
- trip organization after the user chooses an option

That means Wandrix should not do:
- checkout
- payment capture
- reservation creation
- provider-side booking confirmation
- wording that suggests a selected option is already a completed booking

The intended product flow is:
1. Wandrix recommends strong options.
2. The user selects the one they want.
3. The real booking happens outside Wandrix.
4. Wandrix remembers that choice as the selected option.
5. Later, the user may confirm that they booked it, if we add that state and UX.

Why this matters:
- it keeps the product boundary honest
- it avoids pretending Wandrix is an OTA or checkout platform
- it lets Advanced Planning stay focused on decision support and organization

### Add Selected, Booked, And Organizer Semantics

To support real Advanced Planning, the planner should stop treating all provider output as the same kind of object.

We should eventually distinguish:
- `recommended`
- `shortlisted`
- `selected`
- `booked`
- `rejected`
- `manual`

This should apply to:
- flights
- hotels
- activities
- events
- transport items later

Why:
- the trip should show what Wandrix suggested
- what the user actually chose
- and, later, what has become a real-world commitment after user confirmation

This will likely require future trip-draft structure improvements so the planner can store:
- the chosen option id or normalized payload
- selection state
- booking-confirmed-later state
- selection rationale
- fallback options
- organizer notes

State semantics should stay clear:
- `selected` means the user chose this option inside Wandrix
- `booked` should be reserved for a later user-confirmed state, not inferred automatically
- `manual` should cover user-entered outside bookings and trip items once that organizer layer exists

### Add Manual Trip Organizer Inputs

This is a later but very important improvement.

Advanced Planning should eventually support manually added trip items for things the user booked or arranged outside Wandrix after leaving Wandrix to complete those bookings.

Examples:
- a hotel booked elsewhere
- a specific flight chosen manually
- an Airbnb address
- a restaurant reservation
- a concert ticket
- a train booking
- a transfer booking
- a host contact or check-in note

The user should be able to provide details like:
- name
- address
- contact details
- confirmation number
- check-in instructions
- notes
- timing
- external link or reference

Wandrix should then:
- store the item in structured form
- place it into the trip timeline
- treat it as a real trip anchor
- plan around it instead of ignoring it
- surface it on the board and in the brochure

Why this matters:
- many users will not book everything through Wandrix
- the product gets much stronger when it can organize the whole trip, not just the parts it suggested

Longer-term product goal:
- `Advanced Planning` becomes both a planning mode and a trip organizer workspace
- the right-hand board becomes a single place where selected, booked-later, and manually added trip details live together
- the brochure can later reflect both editorial itinerary flow and practical logistics

Suggested implementation order:
1. add `recommended` vs `selected` semantics for flights, hotels, and activities
2. add selection actions and memory for chosen components
3. make the board show `recommended / selected / booked later / still deciding`
4. add manual-entry support for outside bookings
5. add organizer fields for contacts, addresses, notes, and confirmations
6. update brochure output so it can reflect both planned and externally booked trip structure

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
