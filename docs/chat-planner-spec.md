# Chat Planner Spec

This document is the source of truth for how Wandrix `/chat` should work end to end.

The planner should feel like a warm travel agent:
- personal when profile context exists
- conservative about what is truly confirmed
- comfortable asking clarifying questions
- structured enough that the board and brochure stay honest

## Core Product Rule

- `/chat` is the main planning surface.
- Flights, hotels, activities, and similar routes are supporting inspection views, not parallel planning flows.
- The trip draft is the canonical source of truth for the board and brochure.
- Raw chat messages live in LangGraph checkpoint state.
- Structured planner memory lives inside the persisted trip draft.

## Planner Lifecycle

The planner moves through five phases:

1. `opening`
- greet warmly
- use first name when available
- mention profile defaults softly when relevant
- ask the next 1 to 2 highest-value planning questions

2. `collecting_requirements`
- collect destination, timing, origin, party, budget posture, modules, and trip style
- do not silently lock ambiguous facts
- keep uncertainty visible through inferred fields and open questions

3. `shaping_trip`
- once the destination and timing are useful enough, propose a provisional trip direction
- use decision cards to narrow choices
- corrections should override earlier facts without losing the history of what changed

4. `enriching_modules`
- call providers only when the core trip shape is strong enough for that module
- enrich the draft without pretending the itinerary is final

5. `reviewing`
- summarize what is locked
- summarize what is still open
- explain when the trip is stable enough for brochure-style review

## Trip Draft Structure

The trip draft owns:
- `title`
- `configuration`
- `timeline`
- `module_outputs`
- `status`
- `conversation`

`status` is a compact summary for surfaces that need quick readiness/progress state.

`conversation` is the deep planner memory object and should not be hidden inside `status`.

## Conversation State

`conversation` contains:
- `phase`
- `open_questions`
- `decision_cards`
- `last_turn_summary`
- `active_goals`
- `suggestion_board`
- `memory`

## Suggestion Board

`conversation.suggestion_board` is the structured board state for early planning.

It should drive the right-hand board directly instead of relying on freeform assistant copy.

The board can be in one of these modes:
- `helper`
- `destination_suggestions`
- `decision_cards`
- `idle`

### Destination Suggestions

Destination suggestion mode is only for broad destination asks.

Rules:
- use browser location first when the user allowed location assistance
- fall back to saved home-base context when browser location is unavailable
- say clearly which source is being used
- show exactly four destination cards
- keep suggestions as options, not confirmations

Each destination card should contain:
- destination name
- country or region
- image
- short reason
- one practicality signal
- selection status

The board should also offer an `Own choice` action that sends the user back to chat to type their own destination.

### Decision Cards

After the destination is confirmed, the board should move to the next useful choice set instead of returning to plain helper copy immediately.

Examples:
- timing direction
- departure point
- stay direction
- trip tone

### Open Questions

Open questions should be:
- short
- high-value
- directly actionable
- few in number

They should be tracked as structured objects, not just loose strings.

### Decision Cards

Decision cards should only appear when they help the user resolve the next concrete choice.

Good decision cards:
- compare real destinations
- compare timing windows
- compare trip tone directions
- compare comfort or budget posture

Bad decision cards:
- generic placeholders
- broad yes/no prompts with no travel context

## Conversation Memory

`conversation.memory` contains:
- `field_memory`
- `mentioned_options`
- `rejected_options`
- `decision_history`
- `turn_summaries`

### Field Memory

`field_memory` stores the best structured memory per planner field:
- `value`
- `confidence`
- `source`
- `source_turn_id`
- `first_seen_at`
- `last_seen_at`

This is how Wandrix remembers the difference between:
- explicitly confirmed facts
- provisional or inferred facts
- earlier facts that were later corrected

### Mentioned Options

These are candidate options the user mentioned but did not choose.

Examples:
- possible destinations
- possible origins
- timing windows
- trip lengths
- activity styles
- module preferences
- budget posture cues

### Rejected Options

These are things the user ruled out or corrected away from.

They should not be resurfaced casually in later turns.

### Decision History

Decision history tracks:
- what choices were presented
- what the user selected when known
- which turn introduced the choice

### Turn Summaries

Recent turns should be stored as capped structured summaries, not unlimited freeform notes.

Each turn summary should capture:
- the user message
- the assistant reply
- changed fields
- resulting phase
- timestamp

## Confirmation Rules

Conservative confirmation is the hard rule.

### Confirmed

Only explicit user statements or explicit confirmations become confirmed facts.

### Inferred

Plausible but not explicit details stay inferred.

They may guide follow-up questions, but they should not silently replace confirmed facts.

### Rejected

If the user corrects an earlier assumption:
- the new explicit fact wins
- the old option should remain traceable in memory or rejection history

### Profile Defaults

Profile defaults are:
- soft guidance
- optional context
- never stronger than explicit trip instructions

They should not be treated as confirmed trip facts unless the user effectively adopts them in the current trip.

## Configuration Rules

`trip_draft.configuration` is the current best structured trip state.

It should be derived from:
- confirmed facts
- bounded inferred facts when the slot is still blank

It should not be used as a place to hide guessy planner behavior.

Important rule:
- traveler counts can stay unknown
- the planner should not assume `1 adult` by default for planner truth

## Provider Activation

Providers should activate module-by-module, not all at once.

Before destination confirmation, the board should stay in suggestion or decision mode rather than pretending the itinerary exists already.

### Weather
Trigger only when:
- destination exists
- timing signal exists

### Activities
Trigger only when:
- destination exists
- timing signal exists

Trip style helps, but it is optional.

### Flights
Trigger only when:
- origin exists
- destination exists
- timing signal exists

### Hotels
Trigger only when:
- destination exists
- timing signal exists

### Budget
Budget is softly optional.

The planner can still move forward without it, but:
- price-sensitive choices should stay broad
- the assistant should ask for budget soon

## Board Rules

During `opening`, `collecting_requirements`, and early `shaping_trip`, the board should stay summary-first.

It should emphasize:
- route summary
- timing summary
- party summary
- unresolved questions
- decision cards
- readiness/progress state

It should not pretend to show a rich itinerary before the trip is stable enough.

The board must be driven by persisted structured state, not chat text or filler placeholders.

## Runtime Inputs Per Turn

Each planner turn should have access to:
- raw checkpointed messages
- current `trip_draft`
- current `conversation` state
- `profile_context`

## Merge Responsibilities

The planner implementation should stay split across smaller modules:
- turn understanding
- draft merge
- conversation memory merge
- provider gating and enrichment
- assistant response composition

Do not rebuild a giant monolithic planner file.

## Implementation Defaults

- no deterministic parsing for planner understanding
- no regex fallback for trip meaning
- prefer clarification over silent locking
- keep `/chat` as the main planning surface
- keep module pages secondary
- keep brochure derived from structured state
