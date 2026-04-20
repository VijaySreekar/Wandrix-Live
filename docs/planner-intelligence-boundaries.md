# Planner Intelligence Boundaries

This document defines the hard boundary for improving Wandrix planner intelligence.

It exists to keep us aligned while the planner gets smarter:
- what kinds of intelligence work are safe
- what kinds of changes would quietly reintroduce brittle heuristics
- how to tell the difference during implementation and review
- what good planner behavior should look like before and after improvements

This document should be read alongside:
- `AGENTS.md`
- `docs/chat-planner-spec.md`
- `docs/planner-improvement-plan.md`
- `docs/architecture.md`

## Why This Document Exists

Wandrix is a conversation-first AI travel planner.

That means the planner should behave like a careful travel agent, not like a form parser.

We do want:
- better understanding
- better clarification
- better memory
- better judgment
- better structured outputs

We do not want:
- a pile of regexes pretending to be intelligence
- keyword maps quietly deciding user intent
- brittle fallbacks that lock wrong facts
- hidden heuristics that make the product seem smart only on narrow scripted cases

The core rule is simple:

Planner understanding must stay:
- LLM-first
- schema-validated
- ambiguity-aware
- conservative about confirmation

## Hard Boundary

### Allowed

Use deterministic logic for:
- schema validation
- normalization after the model has produced structured meaning
- merge rules between old and new state
- confidence and source bookkeeping
- persistence
- lifecycle gating
- provider readiness checks
- deduplication
- sorting and ranking after candidate data already exists
- enforcing product rules like finalized trips needing reopen before edits

### Not Allowed

Do not use deterministic logic as the main way to understand user intent.

That means we should not:
- parse user travel intent with regex
- infer planner state from keyword lists
- hardcode phrase-to-field mappings as the main understanding path
- classify confirmation with brittle string matching
- derive trip meaning from narrow rule trees
- silently fill missing fields from heuristics and pretend they are understood

## The Real Split

The clean split is:

### LLM-first responsibilities

The model should decide:
- what the user likely means
- whether a detail is explicit or inferred
- whether the user is confirming, correcting, rejecting, or brainstorming
- whether ambiguity is high enough to require clarification
- what the next best question is
- when enough signal exists to propose a draft trip direction
- how to summarize changes in a human planner voice

### Deterministic responsibilities

The application should decide:
- whether the model output matches the schema
- how structured fields merge into persisted planner state
- how confirmed facts override inferred facts
- how rejected options are stored
- when providers are allowed to run
- how the board state is derived from structured planner state
- whether a finalized plan can still be edited without reopening

## Short Rule Of Thumb

If the code is trying to answer:
- "What does the user mean?"
- "Did the user confirm this?"
- "Is this detail explicit or just implied?"
- "What should the planner ask next?"

then the answer should come from the LLM-driven structured understanding path.

If the code is trying to answer:
- "Is this output valid?"
- "How do I store this cleanly?"
- "Which value wins during merge?"
- "Is the trip ready for flight lookup?"

then deterministic logic is appropriate.

## Safe Changes

These are good planner-intelligence changes.

### 1. Make the structured turn schema richer

Safe examples:
- add stronger confidence metadata
- add explicit `explicit`, `inferred`, `corrected`, or `rejected` semantics
- add better open-question objects
- add rationale fields for why a recommendation was made
- add source metadata like `user_explicit`, `profile_default`, `board_action`, `assistant_inferred`

Why this is safe:
- it improves how the model expresses meaning
- it does not replace the model with heuristics

### 2. Improve prompts

Safe examples:
- tell the model to preserve ambiguity
- tell the model not to silently confirm inferred details
- teach the model how to treat profile defaults softly
- improve guidance for rough dates, budgets, and trip style
- improve how destination suggestions are generated

Why this is safe:
- it strengthens the intended understanding path

### 3. Improve merge rules

Safe examples:
- explicit facts override inferred facts
- corrections replace earlier guesses but preserve history
- rejected options are remembered and not resurfaced casually
- finalized trips reject edits until reopened

Why this is safe:
- this is structured state management after understanding

### 4. Improve clarification behavior

Safe examples:
- if confidence is low, ask a focused follow-up question
- if timing is broad, keep it broad instead of inventing exact dates
- if the user is comparing destinations, keep them as candidate options rather than forcing one

Why this is safe:
- ambiguity handling is part of planner quality
- the model is still doing the interpretation

### 5. Improve planner response quality

Safe examples:
- better summaries of what changed
- clearer distinction between locked facts and open questions
- more helpful next-step suggestions
- better explanation when the planner is using location assistance or profile context

Why this is safe:
- it improves the product experience without replacing the planner brain

### 6. Add evaluation datasets

Safe examples:
- golden conversations
- ambiguous-turn test sets
- correction scenarios
- rough timing scenarios
- rejection and preference-memory scenarios

Why this is safe:
- evaluation measures planner quality
- it does not change user understanding with heuristics

## Unsafe Changes

These are the kinds of changes we should reject.

### 1. Regex extraction of trip fields

Unsafe examples:
- regex for `"from (.*) to (.*)"`
- regex for `"(\d+) adults"`
- regex for `"cheap|budget|luxury"` to set budget posture
- regex for `"yes|confirm|go ahead"` to finalize plans

Why unsafe:
- these break on natural language variation
- they encode fake confidence
- they train the app to look smart only on narrow phrasing

### 2. Keyword classifiers as planner understanding

Unsafe examples:
- if text contains `"beach"` then `activity_styles = ["beach"]`
- if text contains `"summer"` then `travel_window = "June-August"`
- if text contains `"family"` then set `children = 2`
- if text contains `"romantic"` then force hotels and activities modules on

Why unsafe:
- the same word can mean different things in different contexts
- users often brainstorm, compare, negate, or correct
- keyword presence is not the same as commitment

### 3. Hardcoded phrase maps for confirmation

Unsafe examples:
- if message contains `"looks good"` then finalize
- if message contains `"nice"` then mark details confirmed
- if message contains `"okay"` then confirm trip brief

Why unsafe:
- approval is not always confirmation
- people react casually without intending to lock a plan

### 4. Heuristic date guessing disguised as intelligence

Unsafe examples:
- `"long weekend"` always becomes 3 nights
- `"around Christmas"` always becomes December 24 to December 27
- `"late summer"` always becomes August
- `"next spring"` always becomes April

Why unsafe:
- users often mean ranges, not exact dates
- this creates false precision

### 5. Heuristic fallbacks that silently write state

Unsafe examples:
- if destination missing, reuse the last mentioned city automatically
- if origin missing, force the saved home airport into `from_location`
- if budget missing, use profile preference as if it was trip-confirmed
- if party size missing, default to 2 adults and proceed as confirmed

Why unsafe:
- these make the board and brochure lie
- they collapse uncertainty that should remain visible

## Gray Zones

Some changes are not automatically good or bad. These need careful review.

### Gray Zone 1. Controlled normalization

Usually safe:
- converting `"UK"` to `"United Kingdom"` after the model already understood it
- converting activity style strings into internal enums after structured output

Unsafe version:
- mapping raw user text directly into planner meaning before the LLM has understood context

### Gray Zone 2. Intent gating

Usually safe:
- requiring a valid `planner_intent` field from structured output before finalizing

Unsafe version:
- bypassing the model and deciding intent with string matching

### Gray Zone 3. Provider readiness checks

Usually safe:
- flights require route plus timing signal
- hotels require destination plus timing signal

Unsafe version:
- using heuristics to invent the missing fields just to unblock providers

### Gray Zone 4. UI shortcuts

Usually safe:
- board actions explicitly carry structured action types like `finalize_quick_plan`

Unsafe version:
- converting board actions into fake user text and then relying on deterministic phrase matching

## Before And After Examples

These examples show the difference between brittle logic and correct planner behavior.

## Example 1. Broad destination ask

User says:

`I want somewhere warm in October, maybe Europe, not too expensive.`

### Bad deterministic approach

Code behavior:
- sees `warm`
- sees `October`
- sees `Europe`
- sees `not too expensive`
- hard-sets destination to Spain
- hard-sets budget posture to budget
- asks for exact dates immediately

Why bad:
- the user did not choose Spain
- `not too expensive` is broader than strict budget
- the planner skipped the comparison stage

### Good LLM-first approach

Planner output:
- `travel_window = October`
- `budget_posture = moderate` or inferred budget-conscious posture if the model thinks that is more accurate
- destination remains open
- suggestion board enters `destination_suggestions`
- exactly four warm, practical options are proposed
- assistant says it is using the rough brief and asks the user to choose or refine

Before:
- the board pretends a destination exists

After:
- the board honestly shows a shortlist and keeps destination unconfirmed

## Example 2. Messy route phrasing

User says:

`Thinking of doing Barcelona for a few days. I'd probably head out from London unless flights are much better from somewhere else.`

### Bad deterministic approach

Code behavior:
- regex grabs `Barcelona`
- regex grabs `London`
- writes both as confirmed fields

Why bad:
- origin is tentative
- trip length is vague
- the planner missed the user's flexibility

### Good LLM-first approach

Planner output:
- `to_location = Barcelona` with high confidence
- `from_location = London` as inferred or provisional, depending on prompt/schema semantics
- `trip_length = a few days`
- open question might ask whether London should be treated as the actual departure point
- flight enrichment does not run until route and timing are strong enough

Before:
- the app falsely shows London as locked

After:
- the planner keeps London soft and asks only if it matters

## Example 3. Casual approval versus real confirmation

Assistant says:

`I can shape this into a quick four-day Lisbon plan with food, neighborhoods, and a flexible budget.`

User replies:

`That sounds nice.`

### Bad deterministic approach

Code behavior:
- keyword map sees positive language
- sets `confirmed_trip_brief = true`
- advances to planning mode choice or even generates the itinerary

Why bad:
- polite approval is not explicit confirmation

### Good LLM-first approach

Planner output:
- keeps trip brief unconfirmed
- assistant responds with a concise restatement and one concrete confirmation ask

Example good response:

`Lovely. I have Lisbon, a four-day food-led city break, and a flexible budget direction. If that brief feels right, I can turn it into a quick first itinerary next.`

Before:
- planner over-commits

After:
- planner stays conservative and asks for a clear go-ahead

## Example 4. Rough timing

User says:

`Maybe late September or early October for around a week.`

### Bad deterministic approach

Code behavior:
- converts this into exact dates immediately
- stores September 24 to October 1

Why bad:
- false precision

### Good LLM-first approach

Planner output:
- `travel_window = late September or early October`
- `trip_length = around a week`
- exact dates remain unset
- assistant can still propose a direction using rough timing

Before:
- fake exact dates distort flights, weather, and brochure timing

After:
- the trip remains usable while still honest about uncertainty

## Example 5. Profile defaults

Saved profile:
- home airport: `LGW`
- preferred currency: `GBP`

User says:

`I want to plan a Tokyo trip next year.`

### Bad deterministic approach

Code behavior:
- sets `from_location = LGW`
- sets `preferred_currency = GBP`
- treats both as confirmed trip facts

Why bad:
- the user never said they are leaving from Gatwick for this trip

### Good LLM-first approach

Planner output:
- may mention that it can plan from the saved London-area context if useful
- keeps origin unset unless adopted by the user
- uses currency/profile context softly in recommendations or follow-up prompts

Before:
- the board falsely shows the route starting from LGW

After:
- the planner uses profile context as a helpful nudge, not as a committed fact

## Example 6. Correction

Earlier user message:

`Let's do Rome in May.`

Later user message:

`Actually make it Florence, still in May.`

### Bad deterministic approach

Code behavior:
- leaves both Rome and Florence floating around the draft
- or overwrites Rome without tracking the correction

Why bad:
- the planner loses decision history
- rejected options may resurface later

### Good LLM-first approach

Planner output:
- `to_location = Florence`
- Rome is moved into rejected or corrected history
- assistant acknowledges the change cleanly
- downstream modules update around Florence

Before:
- activities and brochure may still contain Rome artifacts

After:
- the planner reflects the correction cleanly and traceably

## Example 7. Negative preference

User says:

`I want Paris, but not museums all day. More food, neighborhoods, and people-watching.`

### Bad deterministic approach

Code behavior:
- sees `museums`
- boosts museum activities

Why bad:
- the user mentioned museums negatively

### Good LLM-first approach

Planner output:
- activity preferences emphasize food, neighborhoods, cafes, strolling
- museum-heavy pacing is avoided
- rejected or de-emphasized option memory can capture the museum aversion

Before:
- the planner responds to nouns, not meaning

After:
- the planner responds to intent and polarity

## Example 8. Provider triggering

User says:

`Somewhere in Italy for a spring trip.`

### Bad deterministic approach

Code behavior:
- picks Rome
- invents dates
- runs flights, weather, and hotels immediately

Why bad:
- this is provider eagerness hiding planner weakness

### Good LLM-first approach

Planner output:
- destination remains broad
- may show destination suggestions
- providers stay quiet until route and timing are strong enough

Before:
- low-quality provider noise pollutes the board

After:
- the planner earns enrichment by first shaping the brief

## Example 9. Board action versus fake chat parsing

User clicks:

`Confirm plan`

### Bad deterministic approach

Implementation:
- frontend sends a fake text message like `confirm this trip`
- backend detects that phrase with keyword matching

Why bad:
- behavior depends on magic text
- planner intent becomes fragile

### Good approach

Implementation:
- frontend sends a real board action like `finalize_quick_plan`
- backend merges it as structured action context
- planner lifecycle rules stay explicit

Before:
- action logic is hidden and brittle

After:
- product intent is explicit and reliable

## Example 10. Multiple candidates

User says:

`We're debating between Vienna and Prague in December.`

### Bad deterministic approach

Code behavior:
- picks whichever city appears first

Why bad:
- the user explicitly has not chosen

### Good LLM-first approach

Planner output:
- both destinations are stored as candidate options
- a decision card can compare them
- destination stays unconfirmed until the user picks

Before:
- the planner collapses a comparison into a false decision

After:
- the board helps the user decide

## Good Deterministic Support Examples

These are examples of deterministic logic that we do want.

### Example A. Schema validation

Good:
- the model returns `adults = -2`
- schema rejects it
- planner falls back safely or asks again

Why good:
- validation protects product state

### Example B. Merge precedence

Good:
- old state has inferred `from_location = London`
- new state has explicit `from_location = Manchester`
- merge logic promotes Manchester and preserves the previous inference trail

Why good:
- state merge is deterministic and should be

### Example C. Provider readiness

Good:
- flights only run when route and usable timing exist
- hotels only run when destination and timing exist

Why good:
- provider gating is operational logic, not planner understanding

### Example D. Enum normalization

Good:
- the model returns an activity style that maps to internal enum values already defined by the schema or post-validation normalization

Why good:
- we are cleaning structured output, not guessing meaning from raw text

## Review Checklist

Use this checklist for any planner-intelligence PR.

### Safe review questions

Ask:
- Is the model still doing the semantic understanding?
- Does this change preserve ambiguity when ambiguity exists?
- Does it improve structured outputs rather than bypass them?
- Does it keep profile defaults soft?
- Does it avoid silently promoting guesses into confirmed facts?
- Does it improve clarification quality?
- Does it strengthen merge, memory, or evaluation behavior?

### Red-flag review questions

Reject or pause if:
- Are we matching raw user text with regex or keyword lists to set planner facts?
- Are we deciding confirmation from hand-built phrase maps?
- Are we inventing exact values from rough language?
- Are we silently writing default values into user trip state?
- Are we unblocking providers by guessing missing fields?
- Are we making the board look more certain than the planner really is?

## Implementation Guidance

If we want Wandrix to feel smarter, prefer work in this order:

1. Improve the structured turn schema.
2. Improve the prompt and examples in the understanding layer.
3. Improve merge semantics and memory bookkeeping.
4. Improve clarification responses and question prioritization.
5. Improve evaluation scenarios and regression coverage.

Avoid this order:

1. add regex fallback
2. add keyword classifiers
3. add phrase maps for confirmation
4. add hidden defaults to unblock providers

That sequence would make the planner appear better briefly while making it much harder to trust.

## Granular Change Tracker

This section is the implementation tracker for planner-intelligence work.

The goal is to make every change small enough to review safely.

How to use this:
- each row should become one PR, one tightly related PR series, or one clearly scoped task
- do not combine unrelated rows just because they touch the same files
- update status as work progresses
- use the detailed notes below before implementing any row

Suggested status values:
- `not started`
- `drafting`
- `in progress`
- `reviewing`
- `done`
- `paused`

Suggested priority values:
- `P0` means core planner correctness
- `P1` means important quality improvement
- `P2` means useful follow-on improvement

| ID | Priority | Status | Change | Main Files | Why It Matters | Safe Shape |
| --- | --- | --- | --- | --- | --- | --- |
| PI-01 | P0 | not started | Add per-field confidence semantics | `backend/app/graph/planner/turn_models.py`, `backend/app/schemas/trip_conversation.py` | The planner needs to say how sure it is, not just what it thinks | Let the model return structured confidence signals and store them in memory |
| PI-02 | P0 | not started | Add per-field source semantics | `backend/app/graph/planner/turn_models.py`, `backend/app/schemas/trip_conversation.py` | We need to know whether a fact came from the user, the board, profile context, or inference | Extend structured output and state bookkeeping, not raw-text heuristics |
| PI-03 | P0 | not started | Tighten explicit vs inferred merge rules | `backend/app/graph/planner/conversation_state.py` | Prevent inferred details from silently behaving like confirmed facts | Deterministic merge precedence after structured output is produced |
| PI-04 | P0 | not started | Improve correction handling | `backend/app/graph/planner/conversation_state.py`, `backend/app/schemas/trip_conversation.py` | Users change their minds often; the planner must update cleanly | Track corrections and rejected history explicitly |
| PI-05 | P0 | not started | Improve confirmation detection through schema output | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/turn_models.py` | Casual approval should not finalize a trip | Keep confirmation as structured LLM output, not phrase matching |
| PI-06 | P0 | not started | Improve open-question structure and priority | `backend/app/schemas/trip_conversation.py`, `backend/app/graph/planner/conversation_state.py` | The planner should ask the most valuable next question, not a random one | Use structured question objects with field, priority, and status |
| PI-07 | P0 | not started | Improve ambiguity preservation in understanding prompt | `backend/app/graph/planner/understanding.py` | The planner must stop inventing certainty when the user is broad or mixed | Add prompt guidance and examples that preserve uncertainty |
| PI-08 | P1 | not started | Improve rough timing handling | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/conversation_state.py` | Rough timing should stay rough until the user chooses exact dates | Keep windows and lengths broad unless the user gave exact dates |
| PI-09 | P1 | not started | Improve origin handling for tentative phrasing | `backend/app/graph/planner/understanding.py` | Users often mention an origin softly or conditionally | Let the model mark route fields as tentative or inferred |
| PI-10 | P1 | not started | Improve budget posture handling | `backend/app/graph/planner/understanding.py` | Budget language is subtle and often qualitative | Capture posture conservatively instead of hardcoding labels from keywords |
| PI-11 | P1 | not started | Improve traveler understanding | `backend/app/graph/planner/understanding.py` | Party size affects nearly every recommendation | Handle explicit counts, soft phrasing, and uncertainty separately |
| PI-12 | P1 | not started | Improve module-scope understanding | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/provider_enrichment.py` | The planner should respect “just activities” or “skip flights” clearly | Keep selection module-aware through structured outputs |
| PI-13 | P1 | not started | Improve destination suggestion discipline | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/suggestion_board.py` | Broad asks should lead to strong options, not false decisions | Generate suggestions only when destination is still unresolved |
| PI-14 | P1 | not started | Improve decision-card generation quality | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/response_builder.py` | Decision cards should help resolve a real choice | Ask the model for cards only when a concrete choice exists |
| PI-15 | P1 | not started | Improve early draft proposal timing | `backend/app/graph/planner/runner.py`, `backend/app/graph/planner/response_builder.py` | The planner should propose a usable draft earlier | Move from questioning to shaping once enough signal exists |
| PI-16 | P1 | not started | Improve planner response framing | `backend/app/graph/planner/response_builder.py` | Users need to understand what is locked, assumed, or missing | Structure replies around changes, assumptions, and next move |
| PI-17 | P1 | not started | Improve profile-context usage | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/response_builder.py` | Profile defaults should help the opening, not override the trip | Use profile context softly and visibly |
| PI-18 | P1 | not started | Improve planning-mode selection semantics | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/runner.py` | Quick vs advanced should be intentional, not accidental | Keep mode choice explicit in structured state |
| PI-19 | P1 | not started | Improve timeline preview quality | `backend/app/graph/planner/understanding.py`, `backend/app/graph/planner/provider_enrichment.py` | A quick plan should feel like a believable trip, not a loose sketch | Ask for fuller previews and merge them carefully with modules |
| PI-20 | P1 | not started | Improve rejected and mentioned option memory | `backend/app/schemas/trip_conversation.py`, `backend/app/graph/planner/conversation_state.py` | The planner should remember comparisons and rejections cleanly | Preserve candidate and rejected options without overcommitting |
| PI-21 | P2 | not started | Improve turn summaries for resume quality | `backend/app/schemas/trip_conversation.py`, `backend/app/graph/planner/conversation_state.py` | Better summaries make later sessions feel coherent | Store structured summaries of what changed and why |
| PI-22 | P2 | not started | Improve provider activation discipline | `backend/app/graph/planner/runner.py`, `backend/app/graph/planner/provider_enrichment.py` | Weak trip briefs should not trigger noisy enrichment | Gate providers on structured readiness, not guessed values |
| PI-23 | P2 | not started | Build planner evaluation conversation set | `backend/tests/`, new evaluation docs/files as needed | We need a repeatable way to tell whether intelligence actually improved | Add representative conversations and expected state outcomes |
| PI-24 | P2 | not started | Add planner-specific regression tests | `backend/tests/` | We need protection for merge rules and phase transitions | Test structured state behavior instead of string-only outputs |
| PI-25 | P2 | not started | Add planner-quality observability | `backend/app/graph/planner/runner.py`, logging surfaces as needed | We need to see weak turns and unexpected planner behavior | Log structured planner outcomes, confidence, and fallbacks |

## Detailed Change Notes

This section explains each change one by one so implementation stays precise.

## PI-01. Add Per-Field Confidence Semantics

### What this change is

Right now the planner can say a field is confirmed or inferred, but it still needs finer-grained confidence semantics.

This change adds a clearer structure for how sure the planner is about each field.

### Why we need it

Without field confidence:
- the board can feel too certain
- rough guesses can look similar to solid understanding
- clarification behavior becomes inconsistent

### What the implementation should do

Add confidence semantics that the model can produce and the planner can store for each field.

Examples:
- high confidence explicit destination
- medium confidence inferred departure city
- low confidence rough budget posture

### What the implementation should not do

Do not create a hand-built rule table like:
- if user says `maybe`, confidence is `0.3`
- if user says `definitely`, confidence is `1.0`

That would be fake precision from heuristics.

### Before

User:

`Probably Barcelona, leaving from London I think.`

Planner behavior:
- destination and origin may both appear similarly solid

### After

Planner behavior:
- `to_location = Barcelona` with stronger confidence
- `from_location = London` with weaker confidence or inferred source
- response can ask only about the origin if that is the weak spot

## PI-02. Add Per-Field Source Semantics

### What this change is

Every planner fact should say where it came from.

### Why we need it

Without source tracking:
- profile defaults can quietly look like user-stated facts
- board actions can become hard to distinguish from typed user intent
- later corrections are harder to reason about

### What the implementation should do

Make source tracking explicit for each field.

Good source types:
- `user_explicit`
- `user_inferred`
- `profile_default`
- `assistant_derived`
- `board_action`

### What the implementation should not do

Do not fake source by reverse-engineering raw text after the fact with rules.

### Before

Profile has `LGW`.
User says:

`Plan me something in Tokyo next year.`

Planner state:
- route may show `LGW -> Tokyo` with unclear provenance

### After

Planner state:
- destination may be user-driven
- origin remains unset or soft
- if profile context is used, it is stored visibly as profile-derived context

## PI-03. Tighten Explicit Vs Inferred Merge Rules

### What this change is

Once the model returns structured output, merge rules should clearly decide what wins.

### Why we need it

Without clean merge precedence:
- old guesses can linger after clearer user statements
- inferred values can behave like confirmed values
- the planner becomes hard to trust over time

### What the implementation should do

Make merge behavior deterministic after understanding.

Rules should cover:
- explicit beats inferred
- newer explicit beats older explicit when it is clearly a correction
- rejected options should not casually return

### What the implementation should not do

Do not use raw text string matching during merge to detect what changed.

### Before

Earlier:

`Maybe Rome.`

Later:

`Actually Florence.`

Bad result:
- both cities keep leaking into later planning

### After

Good result:
- Florence becomes the active destination
- Rome stays in history as a rejected or corrected option

## PI-04. Improve Correction Handling

### What this change is

Users will revise destination, dates, budget, and module scope constantly.

This change makes correction behavior explicit.

### Why we need it

Correction handling is one of the fastest ways to make the planner feel intelligent or unintelligent.

### What the implementation should do

When the user corrects something:
- promote the new fact
- keep the old fact traceable in history
- make sure downstream modules realign around the new fact

### What the implementation should not do

Do not:
- silently overwrite without trace
- keep both options half-active
- rely on hardcoded phrases like `actually` to detect every correction case

### Before

User:

`Let's do Lisbon.`

Later:

`No, make it Porto instead.`

Bad result:
- Lisbon hotels still remain in the board summary

### After

Good result:
- Porto becomes active
- Lisbon is remembered as rejected
- follow-up questions and enrichment now target Porto

## PI-05. Improve Confirmation Detection Through Schema Output

### What this change is

The planner needs a better way to distinguish:
- interest
- approval
- brief confirmation
- actual plan finalization

### Why we need it

This is one of the easiest places to accidentally reintroduce brittle keyword logic.

### What the implementation should do

Let the model classify confirmation through structured output:
- not confirmed
- brief confirmed
- plan finalize intent
- reopen intent

### What the implementation should not do

Do not implement:
- `if text contains "looks good" then confirm`
- `if text contains "yes" then finalize`

### Before

User:

`That sounds nice.`

Bad result:
- planner advances as if the trip was confirmed

### After

Good result:
- planner treats it as positive engagement
- still asks for a clear go-ahead before locking anything

## PI-06. Improve Open-Question Structure And Priority

### What this change is

Open questions should be first-class objects, not just loose strings.

### Why we need it

Without good question structure:
- the planner asks low-value questions too early
- the board can drift away from the real missing information
- later resume behavior gets muddy

### What the implementation should do

Each question should carry:
- a field or planning area
- a priority
- a status
- possibly why it matters

### What the implementation should not do

Do not store only a list of plain-text questions with no structure behind them.

### Before

The planner asks:

`What dates are you thinking?`

even though destination is still broad and unchosen.

### After

The planner asks:

`Which of these destinations feels closest to what you want?`

because that is the actual highest-value next question.

## PI-07. Improve Ambiguity Preservation In The Understanding Prompt

### What this change is

The prompt should explicitly teach the model to preserve ambiguity.

### Why we need it

Models often try to be helpful by overcommitting.

### What the implementation should do

Push the prompt harder on:
- keeping broad timing broad
- preserving candidate destinations
- not hard-setting uncertain traveler counts
- treating soft route language as provisional

### What the implementation should not do

Do not counter overcommitment by adding heuristic post-processing that guesses what the model meant.

### Before

User:

`Somewhere warm in Europe this autumn.`

Bad result:
- planner chooses one country immediately

### After

Good result:
- planner stays broad and offers a shortlist

## PI-08. Improve Rough Timing Handling

### What this change is

This change improves the planner's handling of fuzzy time language.

### Why we need it

Travel planning often starts with:
- `late September`
- `around Easter`
- `a long weekend`
- `sometime in spring`

### What the implementation should do

Keep rough timing as:
- `travel_window`
- `trip_length`

until the user actually chooses exact dates.

### What the implementation should not do

Do not auto-convert broad phrases into fixed dates unless the user really gave fixed dates.

### Before

User:

`Maybe early October for five-ish days.`

Bad result:
- planner writes exact dates immediately

### After

Good result:
- planner keeps a broad window plus a rough duration and still moves planning forward

## PI-09. Improve Origin Handling For Tentative Phrasing

### What this change is

This change helps the planner handle soft route language like:
- `probably from London`
- `maybe Manchester`
- `wherever is easiest from the south`

### Why we need it

Origin often arrives as a planning hint, not a locked fact.

### What the implementation should do

Allow origin to remain tentative and ask only when route certainty matters.

### What the implementation should not do

Do not treat every mentioned origin as confirmed.

### Before

User:

`I'd probably leave from London unless something else makes more sense.`

Bad result:
- London is stored as a solid committed origin

### After

Good result:
- London is provisional
- planner can still shape the trip while keeping the route flexible

## PI-10. Improve Budget Posture Handling

### What this change is

Budget language needs better nuance.

### Why we need it

Users rarely say:
- `my budget posture is moderate`

They say:
- `not too expensive`
- `happy to splurge on food`
- `keep hotels sensible`

### What the implementation should do

Let the model interpret posture carefully and keep it soft when needed.

### What the implementation should not do

Do not map simple keywords directly into final budget labels.

### Before

User:

`I don't need luxury but I don't want it to feel cheap either.`

Bad result:
- planner hard-sets `budget`

### After

Good result:
- planner stores a more balanced budget posture and may clarify if needed

## PI-11. Improve Traveler Understanding

### What this change is

This change improves how the planner understands who is travelling.

### Why we need it

Traveler composition changes itinerary, hotel needs, pace, and budget.

### What the implementation should do

Handle:
- explicit counts
- couples
- families
- children mentioned indirectly
- uncertainty when only partial information is available

### What the implementation should not do

Do not infer exact child counts from vague words like `family`.

### Before

User:

`Thinking of a family trip to Portugal.`

Bad result:
- planner sets `2 adults, 2 children`

### After

Good result:
- planner understands family context but asks for the actual group makeup later

## PI-12. Improve Module-Scope Understanding

### What this change is

The planner should understand whether the user wants:
- full planning
- just activities
- no flights
- hotels later

### Why we need it

Module scope affects both assistant behavior and provider triggering.

### What the implementation should do

Keep module scope as structured planner meaning.

### What the implementation should not do

Do not force all modules on by default just because the app supports them.

### Before

User:

`I already booked flights. Just help me with what to do in Kyoto.`

Bad result:
- planner keeps generating flight content

### After

Good result:
- planner narrows focus to activities and possibly hotels only if the user asks

## PI-13. Improve Destination Suggestion Discipline

### What this change is

Destination suggestions should appear only when the user is still broad enough to need them.

### Why we need it

Suggestion cards are helpful for exploration, but annoying once the user already chose.

### What the implementation should do

Use the suggestion board for unresolved destination asks.

### What the implementation should not do

Do not show destination shortlist cards after the user already said:
- `Let's do Lisbon`

### Before

User:

`Let's do Amsterdam in December.`

Bad result:
- planner still offers four unrelated city cards

### After

Good result:
- planner moves to the next real decision instead

## PI-14. Improve Decision-Card Generation Quality

### What this change is

Decision cards should represent real decisions, not filler.

### Why we need it

Weak cards make the planner feel templated.

### What the implementation should do

Generate decision cards only when they help resolve a concrete uncertainty:
- destination choice
- timing window
- planning mode
- trip tone

### What the implementation should not do

Do not generate generic cards just because the UI can display them.

### Before

Planner asks:

`What kind of trip do you want?`

with generic cards that are not tied to the actual conversation.

### After

Planner offers:

`Food-led neighborhood weekend` versus `museum-heavy classic city break`

because those are the real competing directions in context.

## PI-15. Improve Early Draft Proposal Timing

### What this change is

The planner should know when it has enough to propose a useful first draft.

### Why we need it

If Wandrix keeps questioning too long, it feels hesitant.

### What the implementation should do

Once destination plus usable timing plus broad trip direction exist, the planner should move into shaping.

### What the implementation should not do

Do not wait for every field to be perfect before offering a provisional draft.

### Before

The planner keeps asking about budget, exact dates, and traveler details before proposing anything.

### After

The planner says:

`I can already sketch a strong first direction for this Barcelona long weekend and refine the rest with you after.`

## PI-16. Improve Planner Response Framing

### What this change is

Responses should explain planner state clearly.

### Why we need it

Users need to know:
- what changed
- what is still open
- what the next move is

### What the implementation should do

Shape replies around:
- confirmed facts
- inferred assumptions
- unresolved questions
- next recommended action

### What the implementation should not do

Do not make the assistant sound like an extraction bot or a generic chatbot.

### Before

`Updated your trip draft. What else would you like to add?`

### After

`I now have Lisbon in early October with a roughly five-day window and a food-first city-break direction. Your departure point still feels flexible, so that is the main thing I would confirm next before I tighten flights.`

## PI-17. Improve Profile-Context Usage

### What this change is

This change improves how saved defaults help the planner opening.

### Why we need it

Profile context should make Wandrix feel personal, not presumptuous.

### What the implementation should do

Use profile context to:
- personalize tone
- optionally ground suggestions
- offer a soft starting point

### What the implementation should not do

Do not promote profile defaults into trip facts unless the user adopts them in the trip.

### Before

Saved home airport becomes a committed origin automatically.

### After

The planner says, in effect:

`I can use your London-area default as a starting point if that is still right for this trip.`

## PI-18. Improve Planning-Mode Selection Semantics

### What this change is

The planner should be clear about what `quick` and `advanced` mean.

### Why we need it

Mode choice affects pacing and expectation.

### What the implementation should do

Treat planning mode as an explicit lifecycle decision once the brief is strong enough.

### What the implementation should not do

Do not infer advanced or quick mode from weak signals alone.

### Before

Planner jumps into quick mode because the user said `go ahead`.

### After

Planner distinguishes:
- brief confirmation
- quick-plan request
- deeper refinement request

## PI-19. Improve Timeline Preview Quality

### What this change is

Quick-plan previews should feel like believable travel plans.

### Why we need it

Weak previews reduce trust in the whole product.

### What the implementation should do

Ask for stronger:
- pacing
- day shape
- thematic coherence
- connection to trip style

### What the implementation should not do

Do not overfill the timeline with repetitive filler activities.

### Before

The timeline looks like:
- arrive
- explore city
- dinner
- sightseeing

### After

The timeline feels like an actual trip direction with meaningful pacing and rationale.

## PI-20. Improve Rejected And Mentioned Option Memory

### What this change is

The planner should remember what was considered, not just what won.

### Why we need it

Comparisons and rejections are a major part of travel planning.

### What the implementation should do

Track:
- mentioned candidates
- rejected candidates
- earlier preferences that lost

### What the implementation should not do

Do not keep resurfacing things the user already ruled out.

### Before

User rejects Prague, but it keeps returning in later suggestions.

### After

Prague stays visible only as prior history, not as a fresh recommendation.

## PI-21. Improve Turn Summaries For Resume Quality

### What this change is

Turn summaries should help the planner pick up where it left off.

### Why we need it

Trip planning is naturally multi-session.

### What the implementation should do

Store concise structured summaries of:
- what changed
- what remains open
- what the planner was trying to resolve

### What the implementation should not do

Do not store endless low-signal transcript-like summaries.

### Before

A resumed trip feels like the planner barely remembers the last meaningful decision.

### After

A resumed trip feels like the planner knows the current state and the next unresolved choice.

## PI-22. Improve Provider Activation Discipline

### What this change is

Providers should activate only when the trip brief is strong enough.

### Why we need it

Premature provider calls create noisy board state and waste quota.

### What the implementation should do

Use structured readiness:
- route certainty
- timing usefulness
- module scope

### What the implementation should not do

Do not guess missing fields simply to trigger enrichment.

### Before

Broad Italy trip prompts flight and hotel output too early.

### After

The planner first shapes the brief, then enriches intentionally.

## PI-23. Build Planner Evaluation Conversation Set

### What this change is

We need a fixed set of conversation scenarios to evaluate planner quality.

### Why we need it

Without evaluation, it is too easy to mistake a nice demo for a real improvement.

### What the implementation should do

Build scenarios for:
- broad asks
- rough dates
- corrections
- rejections
- soft approvals
- explicit confirmation
- profile-context handling
- module-scope narrowing

### What the implementation should not do

Do not rely on memory or ad hoc manual checking only.

### Before

We judge planner quality by vibe.

### After

We can compare planner behavior against expected structured outcomes.

## PI-24. Add Planner-Specific Regression Tests

### What this change is

Planner state rules need tests around merge and lifecycle behavior.

### Why we need it

Prompt improvements alone are not enough if state handling regresses.

### What the implementation should do

Add tests around:
- explicit beats inferred
- corrections replace old active facts
- finalized state blocks edits until reopen
- open question status updates
- provider gating based on readiness

### What the implementation should not do

Do not make tests depend only on a single assistant string response.

### Before

State regressions can slip through because the UI still renders something.

### After

Core planner contracts are protected.

## PI-25. Add Planner-Quality Observability

### What this change is

We should be able to inspect planner behavior when a turn feels weak.

### Why we need it

Without observability, planner debugging becomes guesswork.

### What the implementation should do

Capture structured signals like:
- resulting phase
- changed fields
- confidence patterns
- clarification counts
- provider trigger decisions

### What the implementation should not do

Do not log raw user data carelessly or create noisy unreadable logs.

### Before

When the planner makes a weak decision, it is hard to tell whether the issue was:
- prompt quality
- merge behavior
- provider gating
- missing context

### After

We can inspect the structured planner path and fix the real failure point.

## Anti-Regression Rule

If a future change makes the planner seem more accurate, but it works by:
- matching phrases
- forcing defaults
- collapsing ambiguity
- writing guessed details as facts

then it is not a real planner-intelligence improvement.

It is a regression hidden behind a more convenient demo.

## Final Standard

The Wandrix planner should be able to say, in effect:

- `Here is what I know.`
- `Here is what I think is likely.`
- `Here is what you have ruled out.`
- `Here is what still needs a decision.`
- `Here is the most useful next move.`

That is the standard.

Not:

- `I saw a keyword, so I filled a field.`
- `I guessed a date and moved on.`
- `I treated a profile default as a confirmed plan detail.`
- `I assumed the user meant yes.`

If we keep that distinction clear, Wandrix will get smarter in a way that actually scales.
