# Planner Improvement Plan

This document is the practical planning roadmap for improving Wandrix before we turn on recurring Codex automation.

It answers three questions:
- what we want to improve first
- what order makes sense
- what work is safe for automation vs what still needs human review

## Product Direction

Wandrix should feel like a real conversational travel agent.

That means:
- chat is the main planning surface
- the agent should understand messy, natural user language
- the right-side trip board should update with structured, trustworthy state
- the brochure should feel like the polished payoff of the conversation

Profile defaults should help the planner start intelligently, but they must remain soft defaults rather than hard rules.

## Main Goals

### 1. Make the agent genuinely smarter

This is the top priority.

The planner should:
- understand indirect or messy phrasing
- distinguish confirmed details from inferred details
- ask better follow-up questions
- avoid silently locking weak guesses
- use profile defaults as context, not as instructions

### 2. Improve trip planning quality inside chat

The chat should move from:
- extracting fields

to:
- proposing a useful draft plan quickly
- refining that plan through conversation
- coordinating flights, hotels, weather, activities, and timing coherently

### 3. Make the board and brochure feel trustworthy

The board and brochure should reflect structured trip state that feels:
- clear
- complete
- well organized
- visually intentional

### 4. Finish live module coverage carefully

The planner should gradually replace placeholders with real provider-backed data where it is worth the complexity.

## What We Should Improve First

## Phase 1. Planner Intelligence

This is the first automation phase.

Target outcomes:
- stronger LLM-first trip understanding
- better clarification behavior
- better use of profile context
- richer assistant responses
- better distinction between missing, inferred, and confirmed details

Concrete work:
- redesign the structured trip-turn schema
- add explicit field confidence or confirmation metadata
- improve the prompt for trip understanding
- improve fallback behavior so the planner asks clarifying questions instead of becoming vague
- improve title generation and trip summary generation
- improve timeline preview generation from the model

This is the highest-value area because it improves:
- chat
- trip board
- brochure
- future provider orchestration

## Phase 2. Chat Experience And Personalization

After planner intelligence improves, the next step is making the conversation feel more human.

Target outcomes:
- better first message
- profile-aware greeting
- better use of home airport and currency defaults
- more natural pacing
- clearer assistant response structure

Concrete work:
- generate a dynamic greeting from user profile context
- introduce better chat response templates or sections
- improve suggestion chips and follow-up actions
- surface “what changed” more clearly after each turn

## Phase 3. Live Planning Modules

Once the agent is smarter, module quality becomes more valuable.

Target outcomes:
- better flight planning
- real hotel discovery when available
- real event discovery
- stronger activity ranking
- better weather-aware suggestions

Concrete work:
- stabilize or replace flight provider path
- add hotel discovery source when feasible
- wire Ticketmaster events into the planner flow
- improve activity ranking with weather, distance, and trip style
- improve travel-time and logistics reasoning

## Phase 4. Board And Brochure Quality

After the planner can produce better structured trip state, we should upgrade how that state is shown.

Target outcomes:
- a more editorial trip board
- stronger module sections
- clearer timeline hierarchy
- brochure that feels shareable and premium

Concrete work:
- improve trip board hierarchy and density
- improve confirmed vs draft state display
- improve brochure sections, pacing, and typography
- add better outbound links and summary framing

## Phase 5. Export And Reliability

This comes after the brochure shape is stable.

Target outcomes:
- HTML-to-PDF export
- stronger observability
- better provider resilience
- better test coverage

Concrete work:
- add print-ready brochure styles
- add PDF export route or action
- add logging/tracing improvements
- add more backend tests and frontend integration coverage

## Best Order For Automation

If Codex automation is going to run regularly, this should be the working order:

1. planner intelligence
2. chat personalization and response quality
3. live module improvements
4. board and brochure polish
5. export and reliability

That order matters because:
- smarter planning improves everything downstream
- prettier UI without better planner behavior will still feel weak
- export should wait until the trip output stabilizes

## Safe Work For Automation

These are good recurring automation tasks:
- planner prompt improvements
- schema refinements
- clarification-flow improvements
- response quality improvements
- board polish tied to existing state
- brochure layout improvements
- provider adapter cleanup
- docs and changelog maintenance
- lint/build/compile verification

## Unsafe Or Human-Review Work

These should not be left fully autonomous:
- destructive database changes
- major auth changes
- secret handling
- branch or git cleanup decisions that may discard work
- major architecture pivots
- anything ambiguous enough that product intent is not obvious

## Suggested First Automation Backlog

These are the first good automation-safe improvement items.

### Batch A. Planner Intelligence Core

- improve `TripTurnUpdate` so it can represent inferred vs confirmed values
- improve the trip-understanding prompt
- improve clarification replies when the draft is incomplete
- improve assistant response quality so the planner proposes useful draft plans earlier
- improve timeline preview generation

### Batch B. Profile-Aware Conversation

- use saved profile defaults in the first message more intelligently
- make the greeting feel personalized without sounding robotic
- make home airport and currency appear as soft assumptions in the planner
- improve the transition from account setup into chat

### Batch C. Better Structured Planning

- improve module output synthesis into the trip board
- improve timeline grouping and naming
- improve rationale text for activities and weather pacing
- improve brochure summaries using stronger structured state

## Acceptance Criteria For Phase 1

Before moving heavily into later phases, we should be able to say:

- the planner no longer depends on deterministic parsing for trip understanding
- ambiguous user messages lead to clarification, not bad guesses
- profile context helps the opening turns without overriding explicit instructions
- the agent can produce a useful early draft plan with incomplete information
- the trip board feels more aligned with what the assistant actually said

## Recommendation

Before enabling recurring Codex automation, we should treat this as the active target:

### Immediate focus

- Phase 1: Planner Intelligence

### Immediate automation-safe scope

- Batch A

### After that

- Batch B
- then Batch C

That gives the automation a clear mission:
- make Wandrix smarter first
- then make it more personal
- then make the surfaces more polished

