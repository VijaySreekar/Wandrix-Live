# Changelog

All meaningful changes must be appended here.

Each entry should include:
- Date
- Title
- Technical Summary
- Plain-English Summary
- Files / Areas Touched

## 2026-04-24 - Smoothed Chat Sidebar Collapse

Technical Summary:
- Moved chat workspace column sizing from conditional Tailwind grid classes into a CSS grid transition driven by a `data-sidebar-collapsed` attribute.
- Added short reduced-motion-aware entrance animation hooks to sidebar sections as the expanded and collapsed content swaps.

Plain-English Summary:
- Collapsing or expanding the chat sidebar should now feel smoother instead of snapping abruptly between widths and content states.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Persisted Greeting-Only New Chats

Technical Summary:
- Updated the new-chat opening-turn path so lightweight first messages that do not start full trip planning still create and activate a persisted trip workspace.
- Cached the greeting-style user and assistant turn against the new persisted trip id so refreshes reopen the same chat instead of falling back to another recent session.
- Guarded persisted-trip activation and draft updates by source trip id so late first-message responses cannot overwrite a newer chat workspace.
- Preserved optimistic local greeting history when the backend conversation checkpoint is still empty, so a refresh does not wipe the visible first turn.
- Replaced generated trip-id fallback titles with a stable `New chat` label for lightweight conversations.
- Changed recent-trip cache writes to merge with existing cached rows instead of replacing the sidebar cache with a temporary one-trip list.

Plain-English Summary:
- A new chat that starts with “hi” or another short opener now gets its own sidebar record.
- Refreshing after that first message should reopen the same chat rather than making it look like a different recent chat took over.
- Older in-flight responses from another chat should no longer jump the user into the wrong recent conversation.
- The first short message should remain visible after refresh even before the fuller planning conversation begins.
- Lightweight chats now show as “New chat” instead of exposing a raw trip id in the sidebar.
- The recent-chat list should stop briefly collapsing to one item and then reshuffling after a refresh.

Files / Areas Touched:
- `backend/app/services/trip_service.py`
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Added Immediate Sidebar Entry For New Chats

Technical Summary:
- Preserved the active newly persisted trip during sidebar refreshes so a just-created chat cannot be dropped while the trip-list API catches up.
- Passed fresh trip ids into the chat sidebar and added a short reduced-motion-aware highlight animation for newly inserted recent sessions.

Plain-English Summary:
- After the first message in a new chat, the saved chat should appear in the left sidebar immediately instead of waiting for a refresh or another chat click.
- New sidebar entries now get a subtle arrival animation so the save feels intentional.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Matched Chat Stop Button To Send Style

Technical Summary:
- Restyled the running-state chat stop button to use the same accent button treatment as the send control.
- Replaced the black stop glyph with a smaller white square using the shared composer contrast token.

Plain-English Summary:
- The stop button now looks like part of the Wandrix chat bar instead of a separate white control with a black square.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Moved Send Motion To Composer Bar

Technical Summary:
- Moved the send-click motion from the send button to the composer surface so it remains visible after the button swaps into the stop-generating state.
- Strengthened the message bubble entrance distance for a clearer sent-message animation.

Plain-English Summary:
- The chat should now visibly respond when a message is sent, even while the send control quickly changes into the stop button.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Made Chat Send Animation Visible

Technical Summary:
- Strengthened the chat message entrance animation with clearer slide, fade, and bubble-scale motion for user and assistant rows.
- Added a short send-button pop animation that runs immediately when a message is submitted.

Plain-English Summary:
- Sending a message should now visibly animate instead of feeling like the chat silently jumps into place.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Smoothed Chat Message Flow

Technical Summary:
- Reduced the chat message stack bottom padding from a large artificial spacer to normal composer-adjacent spacing.
- Added viewport auto-scroll behavior that keeps new and running messages pinned near the bottom when the user is already in the active conversation flow.
- Added a short reduced-motion-aware entrance animation for user and assistant message rows.

Plain-English Summary:
- New chat messages should now appear from the bottom in a more natural way, without leaving a strange empty gap under the conversation.
- Sent and received messages now have a subtle animation instead of popping awkwardly into place.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Increased Chat Send Arrow Contrast

Technical Summary:
- Kept the chat send button solid accent-colored even when disabled instead of muting the background.
- Increased the send arrow size and set its SVG stroke directly to white for stronger contrast.

Plain-English Summary:
- The send arrow should now be clearly visible inside the green button at all times.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Kept Disabled Send Arrow Visible

Technical Summary:
- Replaced whole-button opacity dimming on the disabled chat send button with a muted accent background.
- Applied the composer contrast token directly through the send arrow SVG style so the stroke remains white in both enabled and disabled states.

Plain-English Summary:
- The send button still looks inactive when the message box is empty, but the arrow should remain clearly visible.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Forced White Chat Send Arrow

Technical Summary:
- Applied the composer contrast token directly to the send arrow SVG text and stroke classes so it no longer depends on inherited button color.

Plain-English Summary:
- The send arrow should now render white inside the green button.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Restored Solid Chat Send Button

Technical Summary:
- Restored the chat composer send button to a solid accent background while keeping the arrow white through the shared composer contrast token.

Plain-English Summary:
- The send button is green again, and the arrow inside it is white.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Greened Chat Composer Send Icon

Technical Summary:
- Updated the chat composer send button to use a soft accent surface with a green accent icon and border instead of a dark-looking arrow treatment.

Plain-English Summary:
- The send arrow now reads as green and matches the Wandrix travel-planning style more clearly.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Simplified Returning Chat Placeholder

Technical Summary:
- Replaced the returning-thread composer placeholder with a simpler chat-style prompt.

Plain-English Summary:
- The chat input now says “Message Wandrix...” instead of the more awkward “Continue shaping your trip...” copy.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Removed Chat Composer Search Icon

Technical Summary:
- Removed the search icon from the production chat composer and adjusted the bar padding so the input text starts cleanly without a misleading leading control.

Plain-English Summary:
- The chat bar no longer suggests search; it now reads plainly as a message composer for planning.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Centered Slim Chat Composer Controls

Technical Summary:
- Updated the Slim Split composer alignment from bottom-aligned controls to centered controls.
- Removed per-control vertical offsets and tuned the composer height, gap, padding, and input text size for a more balanced single-line layout.

Plain-English Summary:
- The chat bar icon, placeholder text, and send button should now sit on the same visual centerline instead of feeling slightly dropped or uneven.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Removed Chat Composer Divider

Technical Summary:
- Removed the standalone top border from the chat composer root so the Slim Split input bar is the only visible composer boundary.

Plain-English Summary:
- The chat input area now looks less like a line plus a separate box and more like one clean control.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Flattened Slim Chat Composer

Technical Summary:
- Removed the nested visual shell from the Slim Split production composer so the input renders as one compact bar.
- Kept the existing send and stop behavior while simplifying the composer markup and border treatment.

Plain-English Summary:
- The chat bar no longer looks like one container sitting inside another; it is now a single cleaner input surface.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Integrated Slim Split Chat Composer

Technical Summary:
- Applied the selected Slim Split preview treatment to the production chat composer.
- Reworked the composer into a compact token-based bar with an embedded planning icon, smaller textarea, and a single right-side send or stop action slot.

Plain-English Summary:
- The real chat input now uses the slimmer style from the preview page, so it fits the chat workspace more neatly and avoids the oversized boxy look.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Added Chat Bar Preview Samples

Technical Summary:
- Added a standalone `/chat-bar-previews` page with 15 code-native chat composer treatments for review before changing the production composer.
- Built the samples with existing Wandrix theme tokens and lucide icons so the selected direction can be integrated without introducing throwaway styling.

Plain-English Summary:
- There is now a separate page where different chat input styles can be compared side by side.
- The real chat bar has not been changed yet, so a preferred sample can be chosen before integration.

Files / Areas Touched:
- `frontend/src/app/chat-bar-previews/page.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-24 - Stabilized First Message Chat Layout

Technical Summary:
- Switched the chat message stack spacing decision from cached initial messages to the live assistant thread message count.
- Prevented the first new-chat message from changing vertical layout again when the temporary chat becomes a persisted trip.
- Preserved the active assistant-ui thread during the `draft_trip` to persisted-trip handoff so the first response is not reset mid-run.
- Removed the client-storage workspace read from initial render so server and client chat markup stay aligned during hydration.

Plain-English Summary:
- The first message in a new chat should now stay in a steadier position while Wandrix saves the trip behind the scenes.
- The chat should feel less like it jumps, gets stuck generating, or repositions after the first send.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Smoothed New Chat Persistence Handoff

Technical Summary:
- Updated the first-message new-chat persistence handoff to replace the browser URL in-place after the ephemeral workspace becomes a persisted trip.
- Avoided a transient Next route replacement from `/chat/new` to `/chat?trip=...` so the chat shell does not visibly remount after the first message.

Plain-English Summary:
- Sending the first message in a new chat should no longer look like the page refreshes when Wandrix creates the saved trip behind the scenes.
- The address bar still updates to the real trip URL, but the active chat remains steady.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Added Flight UI Preview Pages

Technical Summary:
- Added a sample-only `/flight-previews` preview area with separate pages for the live board flight card, saved-trip flight reference view, Advanced flight selection, and missing-details flight state.
- Created reusable flight preview fixtures and shells that render existing flight board components without writing trip data or calling provider APIs.
- Verified the frontend with lint and production build checks.

Plain-English Summary:
- There are now standalone sample pages where the flight UI can be reviewed without needing to create or load a real trip.
- These pages make it easier to compare the current visible flight boards and spot UI improvements before changing the live planning flow.

Files / Areas Touched:
- `frontend/src/app/flight-previews/`
- `frontend/src/components/flights/flight-preview-pages.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Smoothed Chat Trip Switching

Technical Summary:
- Moved recent-trip navigation ownership from the sidebar into the chat workspace so route changes happen after the destination workspace is hydrated.
- Added a session-scoped workspace cache for recently opened trips and reused prefetched trip state on selection.
- Switched recent-trip selection to an in-page browser history update so changing the `trip` query does not trigger a transient Next route refresh.
- Cleared pending trip state once the displayed workspace and URL are aligned to avoid unnecessary bootstrap reload states.

Plain-English Summary:
- Clicking a recent chat now stays inside the current app shell while Wandrix swaps in the selected trip, instead of briefly refreshing before the chat loads.
- The top-level Chat navigation still opens a fresh chat, while recent-session clicks now switch smoothly without a route refresh.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Stabilized Recent Trip Activity Times

Technical Summary:
- Updated trip-list responses to use the latest effective activity timestamp across the trip row, draft row, and draft status `last_updated_at`.
- Hardened sidebar refresh merging so a refreshed API row cannot replace a newer visible `updated_at` with an older cached or trip-table timestamp.
- Added backend coverage for effective trip activity timestamp selection.

Plain-English Summary:
- The recent chat list now keeps stable “last updated” times when moving between Home, Chat, and individual trips.
- A trip that showed as updated 9 hours ago should no longer jump backward to 21 hours ago just because the sidebar refreshed.

Files / Areas Touched:
- `backend/app/services/trip_service.py`
- `backend/tests/test_trip_service.py`
- `frontend/src/lib/recent-trips-cache.ts`
- `CHANGELOG.md`

## 2026-04-24 - Fixed Advanced Review, Sidebar, Flights, and Brochure Display

Technical Summary:
- Added `advanced_review_workspace` to the chat board preview render allowlist so Advanced Review renders in the right-side board instead of falling back to the generic live board.
- Made the chat sidebar recover from sparse one-trip recent-session state by retrying trip-list refreshes when the sidebar only has the active trip.
- Filtered provider-backed flight options by the trip's selected outbound and return dates before they become Advanced Flight cards.
- Anchored selected Advanced flight timeline labels to the configured trip dates so stale provider dates cannot create incorrect `Day 24`-style labels.
- Made explicit activity day moves honor the requested day first, using another open daypart on that day before falling back elsewhere.
- Filtered Advanced brochure snapshots and legacy brochure rendering around selected flights/stays instead of raw provider inventory.
- Stabilized board-action chat insertion so manually appended assistant responses do not start an extra assistant-ui run.

Plain-English Summary:
- The review board now appears where travelers expect it, the left sidebar keeps showing recent sessions, and old cached flight inventory no longer leaks misleading dates into the plan.
- Activity schedule edits better respect the user's chosen day.
- Brochures now focus on the selected planning choices instead of showing every hotel or stale flight option returned by providers.
- Board button responses no longer trigger an extra chat runtime pass after the backend action has already completed.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/services/brochure_service.py`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `CHANGELOG.md`

## 2026-04-24 - Added Conflict Repair Follow-Through Memory

Technical Summary:
- Added `conflict_resolution` to planner decision memory so resolved, deferred, and safely edited planning tensions become durable planning context.
- Stored conflict resolution outcomes as confirmed or working memory with source, rationale, related anchor, and updated timestamp.
- Carried follow-through wording into repeated same-evidence conflicts so Wandrix respects accepted tradeoffs, deferred cautions, and safe-edit preferences until evidence materially changes.
- Updated conflict resolution responses and Advanced Review cards to distinguish resolved-by-edit, accepted tradeoff, and deferred caution outcomes.
- Added targeted backend coverage for conflict resolution memory creation and same-evidence follow-through behavior.

Plain-English Summary:
- Wandrix now remembers how a traveler chose to handle a planning tension instead of raising the same repair suggestion over and over.
- If the user accepts a tradeoff, defers a caution, or applies a safe edit, the planner carries that preference forward unless the plan changes enough to make it a new issue.
- Review cards now make it clearer whether a tension was fixed, intentionally accepted, or saved as a caution.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Proactive Conflict Repair Guidance

Technical Summary:
- Extended planner conflicts with priority score, priority label, recommended repair, why-it-matters text, and proactive summary metadata.
- Added deterministic conflict ranking so open, higher-impact tensions surface before deferred or resolved items.
- Updated assistant responses to mention the top open conflict after meaningful planning changes, including Quick Plan provider-confidence cases.
- Upgraded Advanced Review and live board conflict cards to show recommended repairs and short reasoning instead of only passive warning text.
- Updated brochure caution notes to use recommended repair language for open conflicts while preserving deferred and resolved behavior.
- Added backend coverage for guidance metadata and proactive conflict response copy.

Plain-English Summary:
- Wandrix now does a better job of saying which planning tension matters most, why it matters, and what the cleanest repair path is.
- After a user makes a change that creates a meaningful tension, the assistant can call it out right away instead of waiting until the final review.
- The review board and brochure notes now read more like guided travel planning advice and less like raw diagnostics.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/brochure_service.py`
- `backend/tests/test_brochure_service.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Guided Conflict Resolution

Technical Summary:
- Extended planner conflict records with open/resolved/deferred status, resolution summaries, resolution actions, timestamps, and board-rendered resolution options.
- Added Advanced Review board actions for resolving, deferring, and applying conservative safe edits to planner conflicts.
- Preserved conflict resolution memory across recomputation by conflict id and evidence signature, reopening conflicts only when the underlying evidence materially changes.
- Added safe reducer edits for activity density/logistics/weather/stay/provider-confidence conflicts while preserving essentials, manual activity edits, fixed-time events, selected flights, selected stays, and finalization state.
- Updated Advanced Review cards, live board filtering, assistant responses, and brochure caution-note generation for resolved and deferred conflict states.
- Added targeted backend tests for conflict status persistence, safe activity edits, and brochure treatment of deferred versus resolved conflicts.

Plain-English Summary:
- Wandrix can now help travelers do something about review tensions instead of only listing them.
- In Advanced Review, each tension can be reviewed, safely softened, deferred as an intentional caution, or accepted as resolved.
- Deferred cautions still carry into the brochure, while resolved tensions stay out of the warning notes unless the facts change.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/brochure_service.py`
- `backend/tests/test_brochure_service.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Planner Conflict Detection

Technical Summary:
- Added planner-owned conflict records with severity, category, affected areas, evidence, source decision ids, suggested repair text, and optional revision target.
- Built advisory conflict detection from existing Trip Style, Pace, Flights, Stay, Weather, Activities, and provider-confidence signals without automatically mutating the plan.
- Surfaced planning tensions in Advanced Review and the live board, with repair buttons routing to existing Advanced revision workspaces where possible.
- Preserved conflicts in brochure worth-reviewing notes and finalized warning output.
- Added targeted backend coverage for schedule-density, style mismatch, review propagation, provider-confidence conflict, and brochure preservation.

Plain-English Summary:
- Wandrix can now notice when parts of the plan pull against each other, such as a slow-paced trip becoming too full or a food-led trip missing food anchors.
- These tensions are advisory: the app explains them and suggests where to review, but it does not silently change the trip.
- Finalized brochures now keep those caution notes so the saved proposal remains honest.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/brochure_service.py`
- `backend/tests/test_brochure_service.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Confidence-Aware Provider Clarification

Technical Summary:
- Added structured provider reliability blockers to planner observability so blocked module activation records the unreliable field, source, confidence, and traveler-facing reason.
- Converted the highest-priority reliability blocker into an open question for the conversation state, including cases where a value exists but came from profile memory or another weak source.
- Updated Quick Plan waiting copy to name the next reliability question instead of only saying live planning is blocked.
- Threaded provider activation context through conversation-state building so confidence questions stay visible only while the relevant field remains unreliable.
- Added runtime coverage for profile-derived origin blocking live flight search and producing a route clarification.

Plain-English Summary:
- Wandrix now distinguishes “we do not know this yet” from “we have a guess, but it is not reliable enough for live provider checks.”
- If a flight search would use a profile-default origin or another soft assumption, the chat and board now ask the exact confirmation needed before spending provider calls.
- This makes the planner more careful without making the user repeat details that are already genuinely confirmed.

Files / Areas Touched:
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-24 - Surfaced Decision Confidence In Advanced Review

Technical Summary:
- Added Advanced Review decision-signal contracts that expose current decision value, source, confidence, status, related anchor, and traveler-facing caution note.
- Reordered planner memory merge timing so current-turn decision memory can inform the review workspace instead of appearing one turn late.
- Updated Advanced Review readiness and section notes to account for low-confidence, inferred, profile-default, working, or needs-review decision memory without overriding stronger explicit choices.
- Rendered a Decision Sources panel in the Advanced Review board and added frontend type/default parity.
- Added merge semantics coverage for low-confidence decision memory influencing review readiness and source notes.

Plain-English Summary:
- The review board now shows why Wandrix trusts each major planning choice, whether it was chosen directly, inferred, pulled from profile defaults, or based on provider data.
- Weaker signals now become gentle “worth checking” notes instead of being hidden behind a polished summary.
- This makes the final review more transparent and helps users catch assumptions before saving a brochure-ready plan.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Planner Decision Memory Foundation

Technical Summary:
- Added planner-owned decision memory records for core trip facts and Advanced Planning decisions with source, confidence, status, rationale, related anchor, and update time.
- Extended conversation memory so intake fields, profile defaults, board actions, chat decisions, provider-backed weather, Trip Style, Flights, Stay, Activities, and Advanced Review can be summarized as current decision state.
- Added reducer helpers that preserve stronger explicit/board sources over weaker inferred/profile/system updates and keep profile defaults as working memory rather than confirmed facts.
- Added frontend type/default parity for the new decision memory contract.
- Added merge semantics coverage for profile-default softness, source-priority preservation, completed Trip Style memory, and board-confirmed flight memory.

Plain-English Summary:
- Wandrix now remembers not just what the current plan says, but where important decisions came from and how strongly it should trust them.
- Profile defaults remain helpful suggestions instead of being treated like user-confirmed facts.
- This gives future planner intelligence a cleaner base for better clarification, provider readiness, review explanations, and resume behavior.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Upgraded Advanced Brochures Into Proposal Outputs

Technical Summary:
- Extended brochure snapshot payloads with optional Advanced Review, trip character, section summary, flexible-item, planned-experience, and worth-reviewing fields while preserving legacy payload validation.
- Built the new Advanced brochure fields from finalized conversation state across review, trip style, flights, stay, activities, and weather planning.
- Redesigned the web brochure as a luxury proposal with an immersive hero, proposal status cards, trip character section, flexible/review notes, refined itinerary treatment, and logistics side panels.
- Added Advanced proposal sections to print HTML and added a system Chrome fallback for PDF rendering when bundled Playwright Chromium is unavailable.
- Added targeted brochure service tests for Advanced payloads, needs-review notes, legacy payload compatibility, and Quick Plan compatibility.

Plain-English Summary:
- Finalized Advanced trips now open as polished proposal-style brochures instead of plain trip summaries.
- The brochure shows what is selected, what is still flexible, what is worth reviewing, and how trip character, flights, stay, activities, and weather shaped the saved plan.
- Older and Quick Plan brochures still load cleanly without requiring Advanced-only data.

Files / Areas Touched:
- `backend/app/schemas/brochure.py`
- `backend/app/services/brochure_service.py`
- `backend/tests/test_brochure_service.py`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `frontend/src/types/brochure.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Advanced Review Finalization

Technical Summary:
- Added a dedicated `finalize_advanced_plan` board action and structured `requested_advanced_finalization` planner update.
- Routed Advanced Review finalization into the existing finalized status and immutable brochure snapshot flow without changing Quick Plan finalization.
- Added an Advanced Review finalization panel with readiness-specific advisory copy for ready, flexible, and needs-review states.
- Updated assistant responses, audit messages, and decision history so Advanced finalization is distinct from Quick Plan locking.
- Added backend coverage for board/chat Advanced finalization, advisory warnings, Quick Plan separation, finalized-lock behavior, and brochure snapshot triggering.

Plain-English Summary:
- Users can now save a reviewed Advanced Planning trip as a brochure-ready version from the review board.
- Flexible choices and warning notes are allowed, but Wandrix explains what will be captured before saving.
- Quick Plan finalization remains separate, so the two planning modes stay clear.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/conversation.py`
- `backend/tests/test_conversation_service.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Advanced Planning Review Board

Technical Summary:
- Added planner-owned Advanced Review state with readiness status, completed/open summaries, section cards, and review notes.
- Added the `advanced_review_workspace` board mode plus review-specific backend/frontend contracts and board action support for revising flights, stay, trip style, or activities.
- Routed Advanced Planning into review when enabled planning areas are complete or when the user asks to review the plan, while preserving Quick Plan finalization behavior.
- Updated chat understanding instructions so review language requests review rather than finalization, and review revision language routes back to existing workspaces.
- Added targeted backend coverage for review summaries, automatic review entry, chat-requested review, revision routing, and understanding prompt behavior.

Plain-English Summary:
- Wandrix can now show a clean “what we have so far” review inside chat before finalizing anything.
- The review board summarizes working flights, current stay, trip character, planned experiences, flexible items, and weather notes using traveler-friendly language.
- Users can jump back into a specific planning area from review without treating the plan as booked or brochure-ready.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Forecast-Aware Weather Nudges

Technical Summary:
- Extended normalized weather contracts with forecast dates, weather codes, condition tags, temperature bands, and risk levels.
- Added planner-owned weather context with ready/unavailable/not-requested status, day impact summaries, and activity influence notes.
- Fed live forecast signals into Advanced Activities as soft ranking and scheduling nudges while preserving manual edits, fixed events, trip style, stay, and flight constraints.
- Updated the live board and activities workspace summaries so weather influence is visible without pretending long-range forecasts exist.
- Added targeted provider and planner coverage for weather code mapping, unavailable forecast handling, and rainy-day indoor activity nudging.

Plain-English Summary:
- Weather now helps shape the plan when real forecast data is available.
- Rain, storms, heat, cold, snow, and clear weather can gently influence which activities are emphasized and how days are explained.
- If forecast data is not available yet, Wandrix says so plainly and only uses the traveler’s weather preference lightly.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/trip_planning.py`
- `backend/app/services/providers/weather.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_weather_provider.py`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `CHANGELOG.md`

## 2026-04-24 - Enriched Advanced Flight Inventory

Technical Summary:
- Extended normalized flight contracts with fare text, stop counts, layover summaries, leg details, timing quality, and inventory notices.
- Updated Amadeus and Travelpayouts flight adapters to preserve richer segment, duration, transfer, fare, and partial-inventory detail behind internal provider normalization.
- Added strategy-aware flight option ranking so smoothest route favors fewer stops, best timing favors humane travel windows, and best value favors lower fare snapshots when available.
- Upgraded the Advanced flights workspace and selected-flight live board treatment to show richer flight details without becoming a raw inventory table.
- Added targeted backend coverage for multi-segment live inventory mapping, cached fallback detail, and richer strategy recommendation behavior.

Plain-English Summary:
- Flight choices now feel much more useful inside chat.
- The user can see whether an option is direct or has stops, how long it takes, what fare snapshot is available, and whether the inventory is live, cached, or planning-grade.
- Wandrix still frames flights as working planning choices, not final schedules.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/trip_planning.py`
- `backend/app/services/providers/flights.py`
- `backend/tests/test_flights_provider.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Flight Timing Impact For Advanced Planning

Technical Summary:
- Extended planner-owned `flight_planning` with confirmed selected-flight snapshots, arrival/departure impact summaries, and timing review notes.
- Updated Advanced timeline derivation so only confirmed selected outbound/return flights become flight timeline anchors; raw provider options remain workspace candidates only.
- Fed confirmed flight timing into the activities scheduler as soft arrival/departure constraints, lightening Day 1 for late arrivals and the final day for early returns while preserving fixed events, manual placements, and reserve decisions.
- Updated assistant response copy and live board rendering so selected working flights and flight timing impacts are visible without implying booking or ticketing.
- Added targeted coverage for selected-flight timeline anchors, late-arrival/early-return activity softening, keep-flexible behavior, and fixed-event preservation under flight pressure.

Plain-English Summary:
- Confirmed flights now matter to the trip plan.
- If the selected outbound arrives late, Wandrix keeps the first day lighter; if the return leaves early, it avoids overfilling the final day.
- The plan still respects user-picked activities and fixed events first, and keeps flight choices clearly framed as working planning inputs, not bookings.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Advanced Flights Working Options

Technical Summary:
- Added planner-owned `flight_planning` state with strategy cards, outbound/return option cards, route-readiness blocking, placeholder handling, selection status, summaries, and downstream notes.
- Added Advanced flight board/chat actions for selecting a strategy, selecting outbound and return options, confirming flights, and keeping flights open, all merged through the same reducer path.
- Added the dedicated `advanced_flights_workspace` board mode and frontend workspace controls, plus a live-board summary for completed or in-progress flight planning.
- Reordered flight provider enrichment to prefer Travelpayouts results first, with Amadeus retained as fallback.
- Added targeted backend coverage for provider ordering, blocked flight readiness, provider-backed options, placeholders, board/chat convergence, runtime completion, and understanding prompt semantics.

Plain-English Summary:
- Flights now work as a real Advanced Planning branch inside chat.
- The user can choose what kind of flight shape Wandrix should plan around, pick outbound and return options separately, or intentionally keep flights flexible.
- If live inventory is weak, Wandrix still gives useful planning placeholders without pretending anything is booked.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/providers/flights.py`
- `backend/tests/test_flights_provider.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Closed Trip Style Verification Gaps

Technical Summary:
- Updated the Trip Style runtime expectation so selecting the `trip_style` Advanced anchor now verifies the dedicated Direction workspace instead of the old generic placeholder board.
- Preserved the stay-review response wording that reassures users Activities remain the active planning driver while a strained stay choice is reviewed.
- Shortened the completed Trip Style board subtitle so live persisted conversations stay inside the typed board contract after Direction, Pace, and Tradeoffs are all summarized.

Plain-English Summary:
- The Trip Style branch verification now matches the real Direction, Pace, and Tradeoffs flow.
- When Activities create tension with a saved stay choice, Wandrix now clearly says Activities are still leading while it asks the user to review the stay.
- The live board handoff after Trip Style completion no longer risks failing because the summary text is too long.

Files / Areas Touched:
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`

## 2026-04-24 - Added Trip Style Tradeoffs Before Activities

Technical Summary:
- Extended Advanced Trip Style from `Direction -> Pace -> completed` to `Direction -> Pace -> Tradeoffs -> completed`, with the new `advanced_trip_style_tradeoffs` board mode and planner-owned tradeoff cards, decisions, status, rationale, and downstream summaries.
- Added board/chat actions for setting and confirming tradeoffs, using the same reducer path for board clicks and structured chat updates.
- Implemented adaptive v1 tradeoff card selection across must-sees vs wandering, convenience vs atmosphere, early starts vs evening energy, and polished vs hidden gems, informed by Direction, Pace, accent, stay/hotel context, and trip style signals.
- Fed confirmed Tradeoffs into activity ranking and rationale as soft tie-breakers while preserving existing activity dispositions, reserves, manual schedule preferences, and fixed-time event locks.
- Added focused backend coverage for Tradeoff action merging, adaptive card selection, Tradeoff completion, activity ranking influence, runtime handoff, and understanding prompt semantics.

Plain-English Summary:
- Trip Style now has a final refinement step before Activities opens.
- After choosing the trip character and day pace, the user can decide how Wandrix should break close calls, like must-sees vs wandering or convenience vs atmosphere.
- Activities now inherit those choices as soft preferences, not rigid rules, so the plan feels more intentional without overwriting user edits.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Trip Style Pace Before Activities

Technical Summary:
- Extended the Advanced Trip Style branch from `Direction -> completed` to `Direction -> Pace -> completed`, with `slow`, `balanced`, and `full` pace choices carried through board actions, chat-side structured updates, suggestion-board state, assistant copy, and frontend contracts.
- Added the dedicated `advanced_trip_style_pace` workspace so confirmed Direction now opens a Pace decision instead of immediately returning to anchor choice, and Pace confirmation completes Trip Style with Activities recommended next.
- Fed confirmed Pace into the activities scheduler as a density default: slow places fewer flexible candidates, balanced targets two main moments, and full can use more dayparts while fixed-time events and manual placements remain stronger.
- Added targeted backend coverage for Pace board/chat merging, Direction-to-Pace runtime flow, activity schedule density, fixed/manual preservation, and understanding prompt semantics; verified backend compile checks plus frontend type/lint checks.

Plain-English Summary:
- Trip Style now asks one more useful question before Activities: how full should the days feel?
- The user can keep the same trip character, then choose Slow, Balanced, or Full pacing so Activities knows whether to leave more open time or build denser days.
- Existing event locks and manual activity edits stay safe when pacing changes.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/understanding.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-24 - Added Trip Style Direction As A Real Advanced Planning Workspace

Technical Summary:
- Added planner-owned `trip_style_planning` state, Direction vocabularies (`primary` plus optional `accent`), board actions, and chat-side `requested_trip_style_direction_updates` so `trip_style` now behaves like a real Advanced Planning branch instead of generic placeholder flow.
- Extended the suggestion board and assistant response layers with a dedicated Direction workspace, explicit confirmation flow, completed-anchor return behavior, and activities-first handoff once the trip character is confirmed.
- Updated activity ranking so a confirmed Direction now shapes candidate ordering and rationale ahead of raw intake style signals, while preserving existing activity selections and schedule edits when Direction changes later.
- Added focused backend coverage for board-action merging, Direction prompt semantics, trip-style workspace completion flow, and activity reranking behavior, and verified the new contracts through planner compile checks plus frontend lint/build.

Plain-English Summary:
- Trip Style now works as a real step in Advanced Planning instead of just a label.
- You can choose the trip’s main character first, like food-led or culture-led, optionally soften it with an accent like local or relaxed, and then let Activities inherit that direction.
- Once Direction is confirmed, Wandrix sends you back to the remaining anchors and pushes Activities next, already biased toward the kind of trip you chose.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-23 - Closed The Activities Workspace With Direct Schedule Editing

Technical Summary:
- Extended the Advanced activities planner contracts with explicit schedule-editing actions, chat-side `requested_activity_schedule_edits`, planner-owned placement preferences, reserve tracking, daypart metadata, and schedule rebalance notes.
- Updated the activities reducer to preserve manual day and daypart choices across rebuilds, allow reserve/restore actions, keep fixed-time events locked, and regenerate draft day plans around those explicit edits instead of wiping them away.
- Expanded the activities workspace and live board UI to expose direct schedule controls for placing picks on specific days, pinning them to morning/afternoon/evening, moving scheduled blocks earlier or later, and sending or restoring items from reserve, while surfacing rebalance notes and richer highlight context.
- Added focused backend coverage for board/chat scheduling parity, reserve/restore behavior, fixed-time event protection, and the new understanding prompt semantics for activity schedule edits.

Plain-English Summary:
- You can now shape the activities branch more directly instead of only marking picks as strong or weak.
- Activities and events can be moved between days, nudged earlier or later, pinned to a part of the day, or saved for later without losing the planner’s surrounding draft.
- Fixed-time events stay locked to their real time, and the board now explains when the planner had to rebalance nearby stops to keep the plan workable.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-23 - Softened Timeline Copy And Activities Handoff Language

Technical Summary:
- Reworked activities schedule summaries and completion summaries so they describe draft days and trip shape more naturally, instead of sounding like internal planner state.
- Updated transfer blocks and per-stop timing notes to read like a travel draft (`Travel between plans`, `Set aside about ... minutes`) instead of generated system output.
- Renamed frontend timeline badges from raw block types to more human labels like `Planned stop`, `Timed moment`, and `Travel`, and softened `Fixed time` to `Set time`.

Plain-English Summary:
- The activities timeline should now read more like a real itinerary draft and less like a backend-generated schedule dump.
- Moving from the activities workspace back to the next planning choice should feel calmer and more natural.
- The day-by-day blocks should be easier for a traveler to scan at a glance.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Polished Activity Card Copy And Shortened Raw Location Text

Technical Summary:
- Tightened Geoapify activity shaping so location labels now prefer shorter English-forward area text over raw full-address strings when possible.
- Reworked planner-side activity candidate summaries and ranking reasons into more editorial travel copy, replacing raw category phrases like `Commercial Marketplace` and generic boilerplate with cleaner experience-led language.
- Added provider assertions to keep shorter location labels stable for English-first and local-script Kyoto activity cases, and updated the runtime expectation for the renamed event-led copy.

Plain-English Summary:
- Activity cards should now read more like real travel suggestions and less like raw map data.
- The location lines are shorter and cleaner, and the supporting reasons sound more natural.
- Kyoto activities should feel less like a scraped POI list and more like a curated planning workspace.

Files / Areas Touched:
- `backend/app/services/providers/activities.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_activities_provider.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Tightened Activities Completion And Aligned The Next-Step Recommendation

Technical Summary:
- Tightened `_finalize_activity_completion_state(...)` so multi-day activities planning no longer completes after a single `Shape trip` choice unless there is a stronger short-trip or fixed-time-event signal.
- Added a dedicated post-activities recommendation helper on the board side so the completed activities handoff now uses the same next-step logic as the assistant response, instead of producing conflicting recommendations.
- Updated the runtime expectation for hotel-review resolution on a longer trip so resolving review can return to the activities workspace without prematurely marking the branch complete.

Plain-English Summary:
- Wandrix should no longer act like one chosen activity is enough to finish planning a whole 5-day activities flow.
- The board and the assistant should now agree on what the next planning move is after experiences are in place.
- This makes the activities handoff feel less jumpy and less contradictory.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Reframed The Activities Experience In More Human Language

Technical Summary:
- Rewrote the Advanced activities board copy, completion copy, and review copy so the experience talks about moments, trip shape, and draft days instead of leaning on planner-internal terms like anchors, branches, essentials, and passes.
- Renamed the main activities workspace labels in the frontend from internal planning semantics to more user-facing language such as `Shape trip`, `Keep option`, `Skip`, `Leading picks`, `In the mix`, and `Refresh draft days`.
- Softened chat-side board action echoes so clicking through the activities workspace now produces more natural transcript language that matches the board labels.
- Updated related anchor-choice and stay-review surface text so the activities flow hands off more smoothly without snapping back into technical planning language.

Plain-English Summary:
- The activities flow should now feel more like a travel planner helping shape a trip, and less like a state machine showing its internal wiring.
- The board now uses friendlier labels for what belongs at the heart of the trip, what should stay as an option, and what should be left out.
- Moving through activities, review, and handoff should read more naturally for a normal traveler, even though the same planning logic is still underneath.

Files / Areas Touched:
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Stabilized Board Actions And Softened Activities Language

Technical Summary:
- Routed planner board actions through the direct backend update path instead of relying on the assistant thread run loop, so board-triggered planner changes can update the trip draft and chat history more reliably.
- Softened Advanced activities wording across the backend board/response builders so the UI talks about what should shape the trip rather than surfacing planner-internal terms like branches and anchors as heavily.
- Updated activities completion copy so selected essentials now describe shaping the activities plan instead of using awkward anchor phrasing.
- Counted chat-side stay-review resolution turns as real activities-branch interaction, so chat and board now agree about when a resolved review can return to a completed activities handoff.
- Replaced the composer send/cancel primitives with thread-state-driven controls because the local assistant runtime always advertised cancel capability, which kept surfacing a fake idle `Stop generating` state in chat.
- Guarded the chat-history cache against server rendering so `/chat/new` no longer throws when the app shell renders before `window` exists, and pointed the top-nav `Chat` entry plus login handoff at `/chat/new` so it always starts a fresh planner.

Plain-English Summary:
- Board actions should now feel less brittle, because they update the real trip state more directly instead of waiting on the chat runtime to catch up.
- The activities flow now sounds more like a travel planner and less like an internal planning system.
- The overall experience should feel a little more natural, even though there is still more polish left to do.
- Resolving a stay review in chat now behaves the same way as resolving it on the board, instead of one path feeling like it "counted" and the other one did not.
- The chat composer now behaves more honestly: the stop button only shows up while Wandrix is actually responding, and idle chat goes back to a normal send state.
- Opening Chat from the navbar now starts cleanly in a new planner instead of yanking you back into an older trip, and the `/chat/new` page no longer trips over browser-only storage during the first render.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/lib/chat-history-cache.ts`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `CHANGELOG.md`

## 2026-04-23 - Improved Activity Candidate Filtering And English-First Titles

Technical Summary:
- Expanded the Geoapify activities provider to query multiple categories per style, prioritize richer marketplace/culture categories over low-signal top-level labels, and return up to six activity candidates instead of a thin four-item list.
- Added English-first activity title shaping so local-script place names can fall back to readable English anchor labels while preserving the original venue name in structured detail and notes.
- Tightened filtering so generic chain restaurants, weak catering-only results, and street-name fragments no longer dominate the Advanced activities workspace, and added provider tests for chain filtering, English fallback, and marketplace/category prioritization.

Plain-English Summary:
- Kyoto activity suggestions now read much more like real trip anchors and much less like random nearby lunch spots.
- Wandrix now prefers English-facing activity titles, while still keeping the local name around in the details when it is useful.
- The activities branch now has a broader and more believable mix of food-and-culture ideas instead of collapsing into generic restaurant clutter.

Files / Areas Touched:
- `backend/app/services/providers/activities.py`
- `backend/tests/test_activities_provider.py`
- `backend/tests/test_provider_enrichment.py`
- `CHANGELOG.md`

## 2026-04-23 - Prevented Premature Activities Auto-Completion

Technical Summary:
- Extended `AdvancedActivityPlanningState` with a persisted `workspace_touched` flag so the planner can distinguish between auto-seeded activity state and a branch the user has actually shaped.
- Updated `merge_activity_planning_state(...)` to mark the activities workspace as touched only after meaningful interaction such as disposition changes, rebuilds, review-resolution turns, or chat-side activity decisions, instead of treating the initial anchor selection as sufficient engagement.
- Tightened `_finalize_activity_completion_state(...)` so activities can only complete when the schedule is ready, the branch has a real anchor, there is no unresolved review, and the workspace has genuinely been touched by the user.
- Updated starter/frontend types and planner tests so first entry to the activities anchor stays in `advanced_activities_workspace`, while explicit shaping actions can still complete the branch and hand it back to remaining anchors.

Plain-English Summary:
- Choosing activities first no longer causes Wandrix to skip past the activities workspace and mark it done immediately.
- The planner now waits until the user has actually shaped the activities branch before it is allowed to count as completed.
- This makes the activities flow feel more honest: you now get the workspace first, and completion happens only after real interaction.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/schemas/trip_conversation.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Added Activities Completion And Anchor Handoff

Technical Summary:
- Extended `AdvancedActivityPlanningState` with derived completion fields so the activities branch can mark itself `completed` once it has a ready timed plan, a real anchor, and no unresolved stay or hotel review still blocking it.
- Added completion evaluation to the planner flow after activities-driven stay and hotel review, so accepted keep-current review decisions count as resolved while thin all-`maybe` plans stay in progress.
- Updated Advanced Planning board routing so a completed activities branch returns to the existing anchor-choice surface with activities marked completed, while unresolved review still wins and weak plans stay inside the activities workspace.
- Updated assistant copy and runtime tests so activities can hand off to the remaining anchors without losing branch context, and so later review or weaker activity evidence can naturally pull the planner back into the workspace.

Plain-English Summary:
- The activities branch can now actually finish instead of staying open forever.
- Once Wandrix has enough real activity structure, it marks activities as completed and brings back the remaining planning anchors so the trip can move forward.
- If the activity plan is still too thin, or if stay or hotel review is still unresolved, Wandrix keeps the user inside the activities flow until it is genuinely ready.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `frontend/src/types/trip-conversation.ts`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Added Review Resolution Flow For Activities-Driven Stay And Hotel Conflicts

Technical Summary:
- Extended the Advanced Planning stay state so activities-driven stay and hotel review can store accepted-review signatures and summaries without adding new public review enums.
- Added explicit `keep_current_stay_choice` and `keep_current_hotel_choice` board actions, plus chat-side `requested_stay_option_title` and `requested_review_resolutions`, so both the board and chat can resolve review by either switching or explicitly keeping the current choice.
- Updated the activities review reducer, assistant responses, and workspace UI so resolved review returns to `advanced_activities_workspace`, accepted review stays suppressed until the activity evidence changes materially, and the activity plan plus hidden timeline remain intact.
- Added targeted backend tests for keep-current suppression, chat-driven stay switching, review reopening semantics, and the new understanding-prompt fields.

Plain-English Summary:
- When activities or events put the current stay or hotel under review, the planner can now handle that cleanly instead of leaving the user stuck in warning mode.
- You can now either switch to a better-fit base or hotel, or keep the current one anyway, and the planner will remember that choice until the trip plan changes enough to make the warning meaningfully different.
- The activities plan stays in place through all of this, so resolving review no longer knocks the trip off course.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Made Sidebar Chat Count Auto-Fit The Available Height

Technical Summary:
- Updated `frontend/src/components/chat/chat-sidebar.tsx` so the sidebar no longer starts from a hardcoded visible-chat count and instead uses a `ResizeObserver` on the list viewport to derive how many chat rows fit in the available height.
- Kept `Show more` behavior intact by layering manual expansion on top of the auto-fit baseline, so the list grows naturally with the sidebar but can still be extended beyond the default fit when needed.

Plain-English Summary:
- The sidebar now shows as many chats as fit in the space it actually has.
- If the sidebar gets taller or shorter, the default visible list adjusts with it instead of staying stuck at five rows.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Refined The Wandrix Wordmark Typography

Technical Summary:
- Updated `frontend/src/components/app/brand-wordmark.tsx` so the live brand text now uses the existing display font stack instead of the heavier `Sora`-style treatment.
- Simplified the wordmark styling to a single `Wandrix` text run with calmer sizing and no split-color letter treatment, while keeping the current briefcase icon mark in place.

Plain-English Summary:
- The header wordmark should look more polished now.
- I moved it away from the chunkier font treatment and made it feel cleaner, more premium, and less shouty.

Files / Areas Touched:
- `frontend/src/components/app/brand-wordmark.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Reverted The Experimental Chat Sidebar Redesign

Technical Summary:
- Restored `frontend/src/components/chat/chat-sidebar.tsx` to the earlier lightweight sidebar structure with the original recent-trip list, compact search, and existing rename/delete affordances after the redesign pass proved wrong in the real app.
- Removed the sidebar-only destination thumbnail helper from `frontend/src/lib/destination-images.ts` so the revert does not leave behind unused support code from the abandoned sidebar iteration.

Plain-English Summary:
- I rolled the sidebar back to the version you preferred before the redesign experiment.
- The extra sidebar styling and image treatment are gone, and the left rail is back to its original simpler behavior.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/lib/destination-images.ts`
- `CHANGELOG.md`

## 2026-04-23 - Reverted The Custom Logo And Swapped In A Briefcase Brand Mark

Technical Summary:
- Removed the user-supplied raster lockup from the live navbar brand treatment and restored `frontend/src/components/app/brand-wordmark.tsx` to a simple code-native icon-plus-wordmark component.
- Replaced the previous custom image approach with Lucide's `BriefcaseBusiness` icon so the Wandrix brand stays lightweight, legible, and easy to tune directly in the frontend without depending on generated logo assets.

Plain-English Summary:
- The app is back to a cleaner built-in logo treatment instead of the uploaded logo you hated.
- The brand now uses a briefcase icon with the live Wandrix wordmark, which should feel simpler and less awkward in the header.

Files / Areas Touched:
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/public/images/branding/wandrix-navbar-lockup-v2.png`
- `CHANGELOG.md`

## 2026-04-23 - Flattened The Chat Sidebar Into A Cleaner Thumbnail List

Technical Summary:
- Reworked `frontend/src/components/chat/chat-sidebar.tsx` to remove the separate `Planning now` block, keep the active conversation highlighted inside the main chat list, and render destination thumbnails for recent chats instead of letter-only placeholders.
- Added a synchronous `getDestinationImageForPlace` helper to `frontend/src/lib/destination-images.ts` so lightweight surfaces like the sidebar can reuse Wandrix's curated destination imagery without async lookup flow.
- Replaced the earlier bulky `New Trip` glyph with a thinner mountain-line mark and widened row content so long trip names can wrap more naturally instead of getting chopped too early.

Plain-English Summary:
- The sidebar now wastes less space and reads more cleanly.
- Your current trip sits naturally inside the same chat list, recent conversations feel more visual, and the `New Trip` button is closer to the style you asked for.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/lib/destination-images.ts`
- `CHANGELOG.md`

## 2026-04-23 - Adopted The New User-Supplied Wandrix Logo In The App Shell

Technical Summary:
- Added the user-provided brand lockup as `frontend/public/images/branding/wandrix-navbar-lockup-v2.png` and updated `frontend/src/components/app/brand-wordmark.tsx` to use the new asset with its correct dimensions.
- Extended the shared brand component with a compact `BrandMonogram`, then replaced the chat sidebar's old compass-led header treatment so the app shell now uses one consistent Wandrix identity across wide and narrow brand surfaces.

Plain-English Summary:
- The app now uses your chosen Wandrix logo instead of mixing the new lockup with the older generic icon treatment.
- The top navigation and chat sidebar should feel like the same brand system now, not two different identities stitched together.

Files / Areas Touched:
- `frontend/public/images/branding/wandrix-navbar-lockup-v2.png`
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Stay Review Workspaces Now Re-rank Alternatives Around Activities

Technical Summary:
- Extended the activities-to-stay review pass so strained stay directions are re-ranked around current activity and event signals instead of showing only the original brief-led stay ordering.
- Re-ranked hotel recommendations inside hotel review mode using the same activity gravity, including stronger neighbourhood-vs-hub scoring and replacement-ready hotel copy when the selected hotel has drifted out of fit.
- Updated stay and hotel review board copy plus assistant responses so review mode now points at the leading replacement option instead of only restating the conflict.

Plain-English Summary:
- When activities or events make the current stay choice feel wrong, Wandrix now surfaces better replacement options instead of only warning you.
- The stay and hotel review boards now actively lean toward the alternatives that match the trip you are actually building.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Refocused The Chat Sidebar Around Active Planning

Technical Summary:
- Reworked `frontend/src/components/chat/chat-sidebar.tsx` so the left rail now behaves like a planning-first workspace instead of a mixed saved-trips shelf, with a branded header, stronger `New Trip` entry point, dedicated `Planning now` card, and a cleaner `Recent chats` list that excludes the active thread.
- Added richer trip summary helpers for route, timing, and phase labels so the sidebar can surface real trip context from persisted trip data and the live workspace draft without introducing new API calls or changing the underlying chat-switching behavior.
- Kept rename and delete flows intact while restyling their surrounding rows to match the calmer, more editorial travel-product direction requested for the chat experience.

Plain-English Summary:
- The chat sidebar now feels like it belongs to the live planning experience instead of acting like a second saved-trips page.
- Your current trip gets a clearer home, recent conversations are easier to scan, and the whole left rail should read as more premium and more aligned with Wandrix's conversation-first product shape.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Activities Can Now Put Stay And Hotel Choices Under Review

Technical Summary:
- Routed the Advanced `activities` branch through the existing stay and hotel review workspaces whenever the activity or event plan puts a previously selected stay direction or hotel under visible strain.
- Reused the planner's activity-driven compatibility overlay so review status now comes from scheduled activity blocks, essential picks, and strong event anchors, then surfaced that state through the suggestion board and assistant response layer instead of leaving it hidden inside planner state.
- Added targeted planner merge and runtime tests covering stay review triggers, hotel-only review triggers, conservative no-review cases, and activities-driven board switching.

Plain-English Summary:
- Wandrix will now call out when the activities plan no longer fits the stay or hotel you chose earlier.
- Instead of quietly swapping those choices, it keeps them visible, explains the conflict, and moves the board into the right review workspace so you can decide what should change.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-23 - Replaced The Navbar Brand With A Custom Compass Lockup

Technical Summary:
- Generated several custom transparent brand-lockup concepts with the built-in `image_gen` workflow, chose the cleanest compass-and-wordmark direction, and saved it as `frontend/public/images/branding/wandrix-navbar-lockup-v1.png`.
- Reworked `frontend/src/components/app/brand-wordmark.tsx` to render the custom lockup image in the navbar instead of composing the symbol and text separately, and added `--nav-brand-chip-*` theme tokens in `frontend/src/app/globals.css` so the logo sits on a stable branded surface in both light and dark themes.

Plain-English Summary:
- The navbar now uses a more custom Wandrix logo instead of the generic icon treatment.
- The compass and the `Wandrix` text now feel like one designed mark, and the new logo should read more cleanly across both light and dark nav themes.

Files / Areas Touched:
- `frontend/public/images/branding/wandrix-navbar-lockup-v1.png`
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-23 - Deepened Event Planning Inside The Advanced Activities Branch

Technical Summary:
- Extended the shared activity and timeline contracts so event candidates and hidden activity timeline items can carry brochure-ready event metadata, including venue name, outbound source URL, image URL, availability text, price text, and status text.
- Upgraded Ticketmaster normalization and Advanced activities ranking so strong fixed-time events can lead the branch more deliberately, produce event-led planner summaries, and persist richer event data through `activity_planning` into the hidden `trip_draft.timeline`.
- Refined the activities workspace, live board, brochure route, and brochure HTML renderer to show richer event treatment with venue hierarchy, metadata chips, outbound event links, and optional event thumbnails without creating a separate events module.

Plain-English Summary:
- Events inside Advanced Planning now feel like real trip anchors instead of just extra items mixed into the activity list.
- Wandrix can now carry event links and richer event detail from the planner all the way through to the final trip surfaces, so the finished trip can actually point back to the live event that shaped it.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/providers/events.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/services/brochure_service.py`
- `backend/tests/test_events_provider.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Replaced The Custom Navbar Mark With A Lucide Compass Icon

Technical Summary:
- Reworked `frontend/src/components/app/brand-wordmark.tsx` to replace the previous custom inline SVG mark with Lucide's `Compass` icon from the `lucide-react` package already used in the frontend.
- Wrapped the icon in a small token-driven circular shell using the existing navbar theme variables so the mark feels cleaner and more intentional on both light and dark surfaces, and removed the negative tracking from the live text wordmark.

Plain-English Summary:
- The navbar logo now uses a cleaner, established icon instead of the old custom mark that felt off.
- I kept the `Wandrix` text live and just swapped the symbol, so it should feel sharper and easier to live with in the actual product.

Files / Areas Touched:
- `frontend/src/components/app/brand-wordmark.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Added W-Based Navbar Logo Concepts

Technical Summary:
- Generated four additional transparent PNG navbar logo-mark concepts using the built-in `image_gen` workflow, this time centered on a legible `W` monogram rather than abstract non-letter marks.
- Saved the new `W` variants under `frontend/public/images/logo-concepts/` as ribbon, editorial-arc, soft, and geometric-star directions for review without changing the live navbar component.

Plain-English Summary:
- I tested whether a `W`-led logo could work for Wandrix, and yes, it can.
- There is now a new batch of `W` concepts in the project so you can react to that direction before we replace the real navbar logo.

Files / Areas Touched:
- `frontend/public/images/logo-concepts/wandrix-logo-concept-8-ribbon-w.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-9-editorial-w-arc.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-10-soft-w.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-11-geometric-w-star.png`
- `CHANGELOG.md`

## 2026-04-23 - Reworked The Homepage Around Real Product Storytelling

Technical Summary:
- Replaced the earlier homepage pass in `frontend/src/app/page.tsx` with a more product-explicit layout built around real Wandrix planning screenshots instead of process-oriented placeholder messaging.
- Reworked the hero to show the actual chat-and-board experience, removed the internal-facing homepage concept section, added a stronger step-by-step usage story, expanded the live-board proof section, upgraded supporting-view cards with richer visual previews, and changed the final CTA into concrete starter briefs.
- Copied product reference screenshots into `frontend/public/images/homepage/` so the homepage can use stable project-local assets for the new visual storytelling.

Plain-English Summary:
- The homepage now feels much more like Wandrix itself instead of a generic landing page with nice copy.
- It shows the real planning experience more clearly, explains the product flow with actual visuals, and ends with examples of what someone could really type to start planning.

Files / Areas Touched:
- `frontend/src/app/page.tsx`
- `frontend/public/images/homepage/chat-suggestion-board-live.png`
- `frontend/public/images/homepage/chat-suggestion-board-stitch-pass.png`
- `frontend/public/images/homepage/improved-travel-planner-reference.png`
- `CHANGELOG.md`

## 2026-04-23 - Added Non-Pin Logo Concept Directions

Technical Summary:
- Generated four additional transparent PNG navbar logo-mark concepts using the built-in `image_gen` workflow after dropping the earlier pin-led direction.
- Saved the new options under `frontend/public/images/logo-concepts/` as route-wave, horizon-road, folded-loop, and star-route variants for review without changing the live navbar implementation.

Plain-English Summary:
- I created a new batch of logo options that move away from the map-pin look and feel more like a broader travel brand.
- These are now in the project so you can compare cleaner directions before we swap the real navbar logo.

Files / Areas Touched:
- `frontend/public/images/logo-concepts/wandrix-logo-concept-4-route-wave.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-5-horizon-road.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-6-folded-loop.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-7-star-route.png`
- `CHANGELOG.md`

## 2026-04-23 - Added Timed Activities Scheduling With A Hidden Advanced Timeline

Technical Summary:
- Extended the Advanced Planning activities branch so ranked activity and event candidates can now be scheduled into planner-owned day plans with timed blocks, unscheduled overflow, and transfer estimates.
- Added richer activity and event normalization fields for coordinates, location labels, source metadata, dwell estimates, and fixed event timing; introduced a Mapbox-backed movement estimator with heuristic fallback; and used that data to rebuild schedules automatically inside `activity_planning`.
- Persisted the activity schedule into the hidden `trip_draft.timeline` by replacing only activity-owned timeline blocks during Advanced Planning, kept the right side in workspace mode, expanded the activities board UI to show scheduled day sections and reserve items, and added targeted backend tests for scheduling, event geocoding, movement fallback, and hidden timeline persistence.

Plain-English Summary:
- Advanced Planning can now do more than rank activity ideas: it builds an actual draft day plan with timed stops, live events, and travel gaps between them.
- That itinerary is being saved quietly in the trip draft for later final review, while the right side still stays in guided planning mode instead of jumping early into the final live board.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/services/providers/activities.py`
- `backend/app/services/providers/events.py`
- `backend/app/services/providers/movement.py`
- `backend/tests/test_events_provider.py`
- `backend/tests/test_movement_provider.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Added Alternate Navbar Logo Concepts

Technical Summary:
- Generated three new transparent PNG logo-mark concepts for the Wandrix navbar using the built-in `image_gen` workflow, each aimed at a cleaner and more integration-friendly brand direction than the current inline mark.
- Saved the concept assets under `frontend/public/images/logo-concepts/` without wiring them into the navbar yet, so the direction can be chosen before changing the live brand component.

Plain-English Summary:
- I created three cleaner logo options for the navbar so you can pick a better brand direction instead of settling for the current weird one.
- These are saved in the project and ready to drop into the site once you choose one.

Files / Areas Touched:
- `frontend/public/images/logo-concepts/wandrix-logo-concept-1-route-mark.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-2-ribbon-pin.png`
- `frontend/public/images/logo-concepts/wandrix-logo-concept-3-horizon-star-pin.png`
- `CHANGELOG.md`

## 2026-04-23 - Made The Green Palette The Main Wandrix Accent Theme

Technical Summary:
- Removed the old blue/gold `wandr` and `blue` accent options from `frontend/src/components/ui/accent-picker.tsx` and made the green palette the primary `Wandrix` option.
- Updated `frontend/src/components/app/appearance-initializer.tsx` so fresh page loads now default to the green accent family and gracefully ignore the removed blue/gold theme keys.
- Changed the default accent tokens in `frontend/src/app/globals.css` to green-based values so the product’s base appearance now matches the intended Wandrix palette even before any user preference is applied.

Plain-English Summary:
- Wandrix now defaults to the green theme instead of the old blue-and-gold one.
- I also removed the old blue/gold Wandrix theme option so the branding stops feeling split between two identities.

Files / Areas Touched:
- `frontend/src/components/ui/accent-picker.tsx`
- `frontend/src/components/app/appearance-initializer.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-23 - Added The Advanced Activities Workspace With Essential Maybe Pass State

Technical Summary:
- Added planner-owned `activity_planning` state, activity candidate card models, and a dedicated `advanced_activities_workspace` board mode across backend and frontend conversation contracts.
- Implemented an Advanced Planning activities reducer that mixes Geoapify activity enrichment with normalized Ticketmaster event candidates, preserves candidate dispositions across turns, applies board/chat activity decisions, and keeps those choices confined to conversation state instead of writing them into the shared itinerary.
- Added a dedicated activities board UI with mixed activity and event cards plus `Essential`, `Maybe`, and `Pass` controls, updated assistant copy for the activities anchor, and introduced targeted backend tests for the new reducer, runtime branch, understanding prompt guidance, and Ticketmaster normalization.

Plain-English Summary:
- Advanced Planning can now open a real activities workspace instead of falling back to generic placeholder copy.
- The board now shows ranked things to do and live events together, and you can mark each one as essential, maybe, or pass while Wandrix keeps that shortlist organized for the next itinerary step.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/integrations/ticketmaster/client.py`
- `backend/app/services/providers/events.py`
- `backend/tests/test_events_provider.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Stopped Recent Trip Cache From Causing Chat Hydration Drift

Technical Summary:
- Updated `frontend/src/components/package/travel-package-workspace.tsx` so recent trips no longer hydrate from browser cache during the initial client render.
- The workspace now starts from the same empty recent-trip state as the server render, letting the later bootstrap path fill cached trips without creating a server/client mismatch.

Plain-English Summary:
- The chat page should no longer disagree with itself on first load just because browser-cached trips were injected too early.
- This removes the kind of hydration drift that was surfacing as a live browser warning in the sidebar.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Removed The Chat Sidebar Hydration Mismatch

Technical Summary:
- Updated `frontend/src/components/chat/chat-sidebar.tsx` to replace the immediate `useSyncExternalStore` hydration flag with a mount-driven `useEffect` flag so the server render and the first client render agree.
- This removes the live browser hydration mismatch that was causing the Next.js issue badge to appear while the chat workspace loaded.

Plain-English Summary:
- The chat sidebar should no longer trigger that browser-side hydration warning on load.
- I changed it so the first client render matches the server output before the sidebar switches into its fully interactive state.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Fixed Theme And Accent Preferences On Fresh Page Load

Technical Summary:
- Added an appearance bootstrap script in `frontend/src/app/layout.tsx` that reads saved `theme` and `accent` values from `localStorage` before the app renders.
- The bootstrap now applies the `dark` class, `color-scheme`, accent variables, and accent foreground color on initial page load, which fixes the mismatch where toggles worked after interaction but fresh pages reopened in the wrong appearance.

Plain-English Summary:
- Dark mode and accent preferences now come back correctly when a new page opens.
- Before this, the toggle worked only after you clicked it in the current tab, which made the saved theme feel broken.

Files / Areas Touched:
- `frontend/src/app/layout.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Brought The Wandrix Logo Closer To The Chosen Navbar Concept

Technical Summary:
- Refined the SVG mark in `frontend/src/components/app/brand-wordmark.tsx` so the icon now uses a cleaner circular travel motif, softer sweep lines, and a warm star accent that better matches the selected concept direction.
- Tightened the wordmark sizing and tracking so the brand lockup sits more naturally in the flatter header without feeling oversized or improvised.

Plain-English Summary:
- The logo in the app now looks much closer to the concept you actually liked.
- I pulled it away from the more experimental mark and made it feel cleaner, rounder, and more elegant.

Files / Areas Touched:
- `frontend/src/components/app/brand-wordmark.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Flattened The Navbar Shell And Removed Nested Utility Framing

Technical Summary:
- Updated `frontend/src/components/app/app-top-nav.tsx` to remove the floating rounded shell treatment and convert the header into a full-width top band with a simpler inner layout.
- Removed the extra grouped utility capsule around accent and theme controls, and simplified the unauthenticated `Log in` treatment so the right side now reads as one continuous header row instead of multiple nested containers.
- Adjusted `frontend/src/components/auth/user-account-popover.tsx`, `frontend/src/components/ui/theme-toggle.tsx`, and `frontend/src/components/ui/accent-picker.tsx` so account and utility controls use lighter hover framing that matches the flatter navbar direction.

Plain-English Summary:
- I flattened the navbar so it no longer looks like a card sitting on top of the page.
- The theme, accent, and login controls now sit more naturally in the header instead of being wrapped in extra little containers.
- Overall the header should feel cleaner, less boxed-in, and more like part of the product.

Files / Areas Touched:
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/ui/theme-toggle.tsx`
- `frontend/src/components/ui/accent-picker.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Implemented The New Premium Navbar Direction In The App

Technical Summary:
- Reworked the shared navigation tokens in `frontend/src/app/globals.css` so the header now uses a warmer editorial shell, softer utility controls, refined active states, and dedicated brand colors instead of leaning on the generic accent-driven nav surface.
- Redesigned `frontend/src/components/app/brand-wordmark.tsx`, `frontend/src/components/app/app-top-nav.tsx`, and `frontend/src/components/app/app-nav-links.tsx` to match the selected concept direction: serif Wandrix wordmark, travel-inspired mark, structured cream header shell, calmer pills, and a more premium utility cluster while preserving the current route model and auth-aware behavior.
- Updated `frontend/src/components/auth/user-account-popover.tsx`, `frontend/src/components/ui/theme-toggle.tsx`, and `frontend/src/components/ui/accent-picker.tsx` so the account and utility controls visually belong to the new navbar treatment, and aligned the chat shell height calculation in `frontend/src/components/chat/chat-page-shell.tsx` with the shared nav-height token.

Plain-English Summary:
- The navbar in the actual app now follows the more premium direction you picked instead of the older plain app-shell look.
- It keeps the same functionality, but the brand, active tab, and right-side controls should now feel much closer to a polished travel concierge product.
- I also made the chat page respect the shared navbar height token so the layout stays in sync with the redesigned header.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/ui/theme-toggle.tsx`
- `frontend/src/components/ui/accent-picker.tsx`
- `frontend/src/components/chat/chat-page-shell.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Added Navbar Concept Directions For Wandrix

Technical Summary:
- Reviewed the shared app shell and chat-first workspace structure in `frontend/src/components/app/app-top-nav.tsx`, `frontend/src/components/app/app-nav-links.tsx`, `frontend/src/components/chat/chat-page-shell.tsx`, and related UI snapshots to assess whether the current navbar matches the documented conversation-first travel-product direction.
- Generated three new desktop navbar concept mockups using the built-in `image_gen` workflow, each preserving the current information architecture while pushing the visual direction toward a more premium, travel-native, concierge-style header.
- Saved the generated concept assets into the project for direct review and future implementation reference under `frontend/public/images/navbar-concepts/`.

Plain-English Summary:
- I reviewed the current navigation and decided it is clean but still too plain for the kind of premium travel planner Wandrix wants to be.
- To give you stronger options, I created three navbar design concepts that feel more branded, more editorial, and more in tune with the chat-plus-live-board product shape.
- The images are now saved in the repo so you can compare them and use one as the visual reference for the real implementation.

Files / Areas Touched:
- `frontend/public/images/navbar-concepts/wandrix-navbar-concept-1-editorial-concierge.png`
- `frontend/public/images/navbar-concepts/wandrix-navbar-concept-2-modern-concierge-luxury.png`
- `frontend/public/images/navbar-concepts/wandrix-navbar-concept-3-product-forward.png`
- `CHANGELOG.md`

## 2026-04-23 - Added Wandrix Homepage Hero Concept Image

Technical Summary:
- Generated a new homepage hero concept image shaped around the actual Wandrix product direction rather than a generic travel scene.
- Used the repo's homepage implementation, shared visual tokens, and current chat-plus-board screenshots as the art direction source so the image reflects the conversation-first planner layout and premium travel tone.
- Saved the selected asset into the frontend public image path for later homepage integration as `frontend/public/images/homepage-hero-wandrix-v1.png`.

Plain-English Summary:
- We now have a homepage image concept that actually looks like it belongs to Wandrix.
- The image shows the product as a travel-planning experience, with the chat workspace and live board feeling baked into the scene instead of looking like a random travel ad.
- It is saved in the project so we can review it and wire it into the site when ready.

Files / Areas Touched:
- `frontend/public/images/homepage-hero-wandrix-v1.png`
- `CHANGELOG.md`

## 2026-04-23 - Recorded The Next Advanced Planning Priority After Hotels

Technical Summary:
- Added `docs/advanced-planning-next-steps.md` to capture the current post-hotel roadmap for Advanced Planning based on the implemented flow without disturbing the broader `future-improvements` roadmap.
- Documented that the next priority is no longer basic date resolution or initial stay selection, because those are already in place.
- Added the new product direction that Advanced Planning must continue after stay and hotel selection by:
  - marking `stay` as completed
  - returning to the remaining anchors
  - using the selected hotel as real downstream planning context
  - building `activities` as the next deep anchor
  - adding cross-anchor review and conflict behavior later

Plain-English Summary:
- We wrote down the real next step for Advanced Planning now that the hotel-selection flow exists.
- The product should no longer stop after the user chooses a hotel.
- Instead, Wandrix should keep going like a connected planner: use the selected stay and hotel as context, move to the next anchor, and later let newer decisions challenge older ones when needed.

Files / Areas Touched:
- `docs/advanced-planning-next-steps.md`
- `CHANGELOG.md`

## 2026-04-23 - Fixed Hotel Selection Runtime And Returned Advanced Planning To Next-Step Anchors

Technical Summary:
- Hardened the LangGraph checkpoint connection path in `backend/app/graph/checkpointer.py` and `backend/app/services/conversation_service.py` by validating pooled psycopg connections before use and retrying checkpoint-backed graph calls once after `OperationalError`.
- Extended the structured planner update model in `backend/app/graph/planner/turn_models.py` and `backend/app/graph/planner/understanding.py` so hotel selection can also be made in chat via `requested_stay_hotel_name`, then merged that into stay-planning state in `backend/app/graph/planner/conversation_state.py`.
- Updated `backend/app/graph/planner/suggestion_board.py` and `backend/app/graph/planner/response_builder.py` so selecting a hotel now hands Advanced Planning back to the next-anchor choice, with `stay` marked completed and moved to the bottom instead of trapping the user inside the hotel board.
- Refined frontend board-action and anchor-card UI in `frontend/src/components/assistant/travel-planner-board-actions.tsx`, `frontend/src/components/package/trip-suggestion-board.tsx`, and `frontend/src/types/trip-conversation.ts` so hotel-selection prompts include the chosen hotel name and completed anchors render as disabled, greyed cards.
- Added coverage in `backend/tests/test_conversation_service.py` and `backend/tests/test_planner_runtime_quality.py` for retry behavior, chat-based hotel selection, and the post-hotel next-anchor board state.

Plain-English Summary:
- Clicking `Select this hotel` should no longer blow up the backend just because a stale checkpoint DB connection was reused.
- Wandrix can now understand hotel selection from chat as well, not only from the board.
- After you pick a hotel, the assistant responds more naturally, then the board returns to the remaining planning options with `Stay` clearly marked as completed instead of keeping you stuck inside the hotel step.

Files / Areas Touched:
- `backend/app/graph/checkpointer.py`
- `backend/app/services/conversation_service.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_conversation_service.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-23 - Switched Hotel Card Copy To Validated LLM Writing

Technical Summary:
- Updated `backend/app/graph/planner/suggestion_board.py` so hotel card `summary`, `why_it_fits`, and `tradeoffs` can now be generated through a structured LLM pass instead of only using rigid template strings.
- Kept the hotel-copy path schema-validated with deterministic fallback behavior, so planner state still stays safe if the model call fails or returns something incomplete.
- Separated stay-level tradeoffs from hotel-level tradeoffs, which stops hotel cards from inheriting the same generic stay warning across the whole shortlist.
- Refined the board fit-line fallback in `frontend/src/components/package/trip-suggestion-board.tsx` so thinner metadata cases still read more naturally on the live board.

Plain-English Summary:
- Hotel cards should now sound more specific to the actual hotel instead of repeating the same planner sentence again and again.
- I moved that copy onto the LLM, but kept it structured and validated so the product remains reliable.
- The repeated “daily travel can need more planning” line should no longer be stamped onto every hotel row.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Removed The Extra Hotel-State Framing From The Live Board

Technical Summary:
- Updated `backend/app/graph/planner/suggestion_board.py` so the Advanced hotel board title and subtitle no longer announce that a hotel is already selected or that Wandrix is “building around” a chosen base at the top of the board.
- Refined `frontend/src/components/package/trip-suggestion-board.tsx` so hotel cards use shorter fit-line copy, cleaner visible area labels, and a slimmer four-card shortlist without the old duplicated selected-hotel framing.

Plain-English Summary:
- The hotel board now reads more like a clean shortlist and less like a system status page.
- I removed the extra “hotel selected / building around” framing at the top and made the recommendation copy much less repetitive.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Flattened The Hotel Board And Made Cards Expandable

Technical Summary:
- Reworked `frontend/src/components/package/trip-suggestion-board.tsx` so the Advanced hotel recommendations no longer sit inside a boxed workspace shell with a sticky header, and instead render as a flatter board section with a single intro line and cleaner spacing between hotel rows.
- Added expandable hotel cards with a compact default state and an inline details section for fuller rationale and tradeoffs, keeping the initial scan lighter while still allowing deeper hotel information on demand.
- Updated `backend/app/graph/planner/response_builder.py` so the assistant now explicitly invites the user to use chat to reshape the hotel shortlist, instead of relying on the board alone to carry the interaction.

Plain-English Summary:
- The hotel step should now feel less boxed-in and less like a separate mini app.
- Each hotel starts cleaner, and you can open a card when you want more detail instead of being forced to read everything at once.
- The assistant also speaks more naturally about the shortlist now, so the conversation stays central.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `backend/app/graph/planner/response_builder.py`
- `CHANGELOG.md`

## 2026-04-23 - Simplified The Live Hotel Board And Removed Repetitive Card Copy

Technical Summary:
- Tightened `frontend/src/components/package/trip-suggestion-board.tsx` so the Advanced hotel board now renders only the first four hotel recommendations, removes the pinned selected-hotel slab, removes the extra stay-context strip, and reduces the vertical bulk of each hotel row.
- Shortened hotel card copy by replacing repeated planner-style rationale paragraphs with a compact fit line derived from hotel tags and cleaner fallback wording, while also normalizing visible area labels before rendering them in the card body.
- Slimmed the hotel image, price, and action layout so the shortlist reads more like the other clean board states in Wandrix and less like a stacked workspace prototype.

Plain-English Summary:
- The hotel board is now much less repetitive and less bulky.
- I removed the extra top blocks you called out, kept the shortlist to four recommendations, and made each hotel card read more like a clear recommendation instead of repeating the same planning sentence over and over.
- The visible area names should also look cleaner and more consistent now.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Polished The Hotel Workspace Hierarchy And Deepened Hotel Metadata

Technical Summary:
- Expanded hotel metadata and workspace contracts in `backend/app/schemas/trip_conversation.py`, `frontend/src/types/trip-conversation.ts`, and `backend/app/services/providers/hotels.py` by increasing the hotel search pool, allowing richer hotel style tags, and carrying more hotel options into the planner instead of compressing the workspace too early.
- Improved hotel normalization and ranking in `backend/app/graph/planner/suggestion_board.py` by adding fallback stay-area labels, district extraction for Kyoto-style addresses, broader derived hotel style tags (`traditional`, `nightlife`, `walkable`, `value`), more useful area/style aggregation, and cleaner hotel tradeoff messaging.
- Reworked the hotel workspace UI in `frontend/src/components/package/trip-suggestion-board.tsx` into a flatter sticky toolbelt with a compact stay context strip, cleaner filter header, numbered pagination, larger hotel imagery, slimmer selected-hotel treatment, and less awkward `current base` language.
- Added validation-compatible schema updates and re-ran planner regression coverage so the deeper style vocabulary and hotel-card payloads remain stable across Advanced stay selection and hotel filtering flows.

Plain-English Summary:
- The hotel side of Advanced Planning now feels more like one polished workspace instead of a stack of unrelated panels.
- There are more hotel options to browse, the area and style filters are richer and more consistent, and the stay direction no longer shows up with that awkward “current base” feel.
- The hotel cards are also calmer and easier to scan, with larger images, cleaner pagination, and stronger area labels.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/providers/hotels.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_provider_enrichment.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Reframed The Hotel Workspace As A Calmer Search Surface

Technical Summary:
- Redesigned the hotel workspace in `frontend/src/components/package/trip-suggestion-board.tsx` from a stack of bordered sub-panels into a single search surface with one sticky header, a lighter stay-direction context line, a simpler control row, and divider-based hotel result rows.
- Flattened the visual hierarchy of the selected-hotel treatment and hotel result cards by reducing shadows, removing the heavier boxed `current base` feel, simplifying badges, tightening copy blocks, and moving price/selection controls into a clearer right-hand action column.
- Kept the richer hotel metadata and pagination behavior from the earlier workspace work, but presented it through calmer pagination, simpler context summaries, and larger but less ornamental hotel imagery.

Plain-English Summary:
- The hotel step on the right board should now feel less like a pile of UI cards and more like one focused hotel-selection workspace.
- I removed a lot of the heavy framing and made the results denser, calmer, and easier to scan, while keeping the filters and hotel selection logic intact.
- The awkward “current base” feel is gone, and the overall page should read more like a polished search flow than a feature demo.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Simplified Advanced Hotels Back To A Curated Four-Hotel Flow

Technical Summary:
- Simplified `backend/app/graph/planner/suggestion_board.py` so the stay-led hotel step now returns a curated top four hotel recommendations inside the selected stay direction instead of shaping a larger filterable workspace with paging.
- Updated `backend/app/graph/planner/response_builder.py` so Advanced stay responses now talk about hotel recommendations rather than a hotel workspace with filters and pagination.
- Reworked `frontend/src/components/package/trip-suggestion-board.tsx` to remove the hotel search controls, filter toolbar, and pagination UI, leaving a simpler recommendation surface with stay context, selected hotel state, and four denser hotel rows.
- Adjusted `backend/tests/test_planner_runtime_quality.py` to validate the simplified curated shortlist behavior instead of the removed filter-and-pagination workflow.

Plain-English Summary:
- The hotel step is now intentionally simpler and more honest.
- Instead of pretending Wandrix is already a full hotel search engine, the board now shows four strong hotel recommendations inside the chosen stay direction and lets the user pick one as the working hotel choice.
- This should feel cleaner, more focused, and less fake than the earlier filter-heavy version.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-23 - Cleared Stale Hotel Filter State And Backfilled Thin Shortlists

Technical Summary:
- Updated `backend/app/graph/planner/conversation_state.py` so the Advanced stay -> hotel path now forcibly clears old hotel filter, sort, and paging state when using the curated recommendation flow instead of carrying stale workspace values forward in conversation state.
- Updated `backend/app/services/providers/hotels.py` so thin provider hotel sets are supplemented with fallback hotel suggestions when needed, helping the planner reach a four-item shortlist more reliably.
- Adjusted `backend/tests/test_planner_runtime_quality.py` to assert that the curated hotel flow ignores stale filter actions and keeps the hotel recommendation state clean.

Plain-English Summary:
- Old hotel filters should no longer linger in the trip state after we simplified the hotel step.
- If live provider results are too thin, Wandrix can now fill the shortlist back up so the hotel step is much more likely to show the expected four options.
- This makes the simplified hotel flow more consistent and less confusing.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/services/providers/hotels.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-22 - Turned The Advanced Stay Shortlist Into A Real Hotel Workspace

Technical Summary:
- Extended the planner conversation contracts in `backend/app/schemas/trip_conversation.py`, `backend/app/schemas/conversation.py`, `frontend/src/types/trip-conversation.ts`, and `frontend/src/types/conversation.ts` with hotel-workspace filters, sort state, available areas/styles, result status, and richer hotel-card metadata like derived style tags and outside-filter visibility.
- Added hotel-workspace shaping in `backend/app/graph/planner/suggestion_board.py` and `backend/app/graph/planner/conversation_state.py`, including exact-date gating, price/area/style filtering, sort modes, result summaries, selected-hotel persistence outside active filters, and derived hotel style tags for the board.
- Updated `backend/app/graph/planner/response_builder.py` so Advanced stay replies now acknowledge hotel workspace refreshes, blocked exact-date comparison, and empty filtered states instead of treating every hotel turn like a generic shortlist.
- Reworked `frontend/src/components/package/trip-suggestion-board.tsx` into a proper hotel workspace with a sticky compact stay summary, sticky controls for nightly cap / area / style / sort, a vertical result list, smaller selected-hotel treatment, and clearer blocked or empty states.
- Updated sandbox/mock shape coverage in `frontend/src/components/package/trip-board-sandbox.tsx` and expanded `backend/tests/test_planner_runtime_quality.py` with regressions for hotel filtering, selected-hotel persistence outside filters, and exact-date blocking behavior.

Plain-English Summary:
- The right-side hotel step now behaves much more like a real hotel search workspace.
- Instead of just showing a static shortlist, the board can now narrow hotels by nightly cap, area, and style, and sort them in different ways while keeping the current hotel choice visible.
- The planner also now treats exact dates as the gate for true hotel comparison, so the hotel board is more honest about when it is ready for real selection.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Cleaned Up The Selected Hotel Panel Labeling

Technical Summary:
- Removed the duplicate `Current hotel` kicker text from the selected-hotel panel in `frontend/src/components/package/trip-suggestion-board.tsx` so the selected state is communicated once through the image badge instead of being repeated in the content column.

Plain-English Summary:
- The selected hotel panel on the right board now reads more cleanly and feels less cluttered.
- It still shows the hotel as the current working choice, but without repeating the same label twice.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Deepened The Hotel Workspace With Pagination And Richer Stay Metadata

Technical Summary:
- Expanded hotel discovery in `backend/app/services/providers/hotels.py` from the old 4-result shortlist to a deeper provider-backed pool, and improved area labels by deriving ward-level location names from provider address data when available.
- Extended the hotel workspace contracts in `backend/app/schemas/trip_conversation.py`, `backend/app/schemas/conversation.py`, `frontend/src/types/trip-conversation.ts`, and `frontend/src/types/conversation.ts` with hotel page state, total result counts, and a persisted `selected_hotel_card` so the working hotel can stay visible even when it falls outside the current page.
- Reworked hotel workspace shaping in `backend/app/graph/planner/suggestion_board.py` and `backend/app/graph/planner/conversation_state.py` to page through a deeper ranked hotel pool, clamp page changes safely, preserve the selected hotel outside the current slice, and expose richer area/style filter values.
- Updated `backend/app/graph/planner/provider_enrichment.py` so older shallow hotel caches refresh instead of freezing the workspace on the original thin shortlist, and added regression coverage in `backend/tests/test_provider_enrichment.py` and `backend/tests/test_planner_runtime_quality.py`.
- Refined the frontend hotel workspace in `frontend/src/components/package/trip-suggestion-board.tsx` with a lighter stay-direction context strip, pager controls, cleaner sticky toolbar behavior, and a safer date fallback for older saved trips.

Plain-English Summary:
- The hotel workspace can now work with a deeper hotel pool instead of feeling capped at a tiny shortlist.
- The board is now set up to page through results properly, keep the current hotel choice visible while you browse, and show more useful area/style context.
- The top of the workspace is also lighter and less awkward, so it reads more like a real hotel-selection tool and less like a stack of unrelated cards.

Files / Areas Touched:
- `backend/app/services/providers/hotels.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/tests/test_provider_enrichment.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-22 - Tightened The Hotel Workspace Hierarchy And Older-Cache Area Labels

Technical Summary:
- Updated `backend/app/graph/planner/suggestion_board.py` so hotel cards normalize area labels from address data when provider areas are still generic, and feed that richer area context back into style-tag derivation for the hotel workspace.
- Slimmed the selected-hotel treatment in `frontend/src/components/package/trip-suggestion-board.tsx` from a large featured panel into a smaller inline summary strip, and improved the compact stay-direction context strip so older saved trips can still show a useful stay window from the visible hotel cards.
- Refreshed fixture expectations in `backend/tests/test_planner_runtime_quality.py` so the tests reflect the more useful Kyoto ward labels now shown by the planner.

Plain-English Summary:
- The hotel workspace now looks less top-heavy, because the selected hotel no longer takes over so much of the right board.
- Older hotel caches also look less generic now, since Wandrix can often pull a more useful area label from the hotel address instead of showing the same broad city text everywhere.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Refined Advanced Hotel Cards Into A Cleaner Selection Layout

Technical Summary:
- Updated `frontend/src/components/package/trip-suggestion-board.tsx` to give hotel cards larger visuals, a cleaner hierarchy, and denser result layouts inside the Advanced stay flow.
- Increased hotel image prominence for both selected and shortlist cards while reducing the bulk of the pinned stay summary and simplifying badge treatment.
- Reworked hotel result cards to use a more minimal structure: stronger hotel name and price hierarchy, leaner metadata, concise fit explanation, and compact tradeoff chips instead of heavier stacked blocks.
- Removed the unused `DetailBody` helper left over from the previous hotel-card version and revalidated the frontend with fresh lint and build checks.
- Live-tested the updated Kyoto hotel shortlist in Chrome DevTools after refreshing live nightly rates.

Plain-English Summary:
- The hotel cards on the right-side board now feel less bulky and more intentional.
- Hotel photos take up more space, the current stay summary is less oversized, and each result is easier to scan quickly.
- The whole hotel step now reads more like a real selection surface and less like a long stack of generic info blocks.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Restored Exact Hotel Pricing And Tightened The Advanced Hotel Workspace

Technical Summary:
- Fixed `backend/app/services/providers/hotels.py` so Xotelo rate parsing reads the real nested `result.rates` payload shape instead of incorrectly looking for top-level `rates`, which was causing exact-date hotel searches to lose valid nightly prices.
- Updated `backend/tests/test_hotels_provider.py` so provider coverage matches the real Xotelo rate-response structure.
- Refined `frontend/src/components/package/trip-suggestion-board.tsx` so Advanced hotel cards now prioritize exact nightly pricing, taxes, and provider notes instead of vague `mid-range fit` style fallback language.
- Tightened the selected-stay and hotel card layouts by shrinking the oversized pinned stay panel, reducing hotel image heights, and compacting the pricing panel so the shortlist feels more like a usable selection workspace.
- Live-tested the Kyoto Advanced stay flow in Chrome DevTools after a refresh turn and confirmed exact nightly pricing now renders on the hotel shortlist for fixed dates.

Plain-English Summary:
- The hotel cards now show real nightly prices again when the dates are fixed.
- The vague budget-fit wording is gone, and the stay header no longer takes over so much space above the results.
- The right-side board feels more like a real hotel-picking workspace now, with the hotels themselves taking priority.

Files / Areas Touched:
- `backend/app/services/providers/hotels.py`
- `backend/tests/test_hotels_provider.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Made Advanced Stay And Hotel Choices Revisable From Real Trip Signals

Technical Summary:
- Updated `backend/app/graph/planner/conversation_state.py` so the Advanced `stay` branch now evaluates selected stay strategies against real downstream trip signals instead of only storing static review fields.
- Added compatibility heuristics for stay strategies based on activity style, custom trip style, day-trip/outdoors bias, nightlife bias, and overall activity density.
- Added hotel compatibility evaluation so a selected working hotel inherits tension from a stay direction that is now under strain, and can also be flagged directly when its fit conflicts with the selected stay strategy.
- Preserved existing review states when no new turn evidence resolves them yet, so previously flagged stay/hotel review states do not silently disappear on the next turn.
- Expanded `backend/tests/test_planner_runtime_quality.py` with regressions proving a quieter stay can move into review when the trip turns nightlife-heavy, and that a selected hotel can move into review when its stay direction no longer fits the evolving trip.

Plain-English Summary:
- Wandrix can now actually notice when a stay or hotel choice stops fitting the shape of the trip.
- For example, if the user picked a calm local base and later turns the trip into a nightlife-heavy plan, the planner can now flag that stay as needing review instead of blindly continuing.
- The same is true for the hotel inside that stay strategy, so Advanced Planning is starting to behave more like a real connected planning system and less like a one-way checklist.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-22 - Refreshed Supabase Auth Snapshots In The Chat Workspace

## 2026-04-22 - Fixed Advanced Date Resolution Board Rendering And Confirmation Gating

Technical Summary:
- Updated `frontend/src/components/package/trip-board-preview.tsx` so the right-side board recognizes `advanced_date_resolution` as a first-class suggestion-board mode instead of falling back to the old placeholder shell.
- Updated `frontend/src/components/package/trip-suggestion-board.tsx` so selecting a date option no longer sends exact `start_date` / `end_date` during the provisional selection step.
- Hardened `backend/app/graph/planner/board_action_merge.py` so provisional date actions (`select_date_option`, `pick_dates_for_me`) strip any leaked exact dates and confirmed-field markers before trip configuration is merged.
- Added a regression in `backend/tests/test_planner_runtime_quality.py` proving provisional date selection keeps the planner in `resolve_dates` and does not persist exact dates until the explicit `confirm_working_dates` action.
- Revalidated the frontend with fresh `lint` and `build` checks after the board-preview and date-selection changes.

Plain-English Summary:
- The new working-date step now shows up properly on the right-side board instead of disappearing behind the old “we’ll use this later” placeholder.
- Picking a date option is once again just a provisional choice, not an automatic date lock.
- Wandrix now waits for the explicit `Proceed with this trip window` confirmation before moving into the four Advanced Planning anchors.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

Technical Summary:
- Updated `frontend/src/components/package/travel-package-workspace.tsx` so the workspace no longer trusts a stale in-memory auth snapshot for protected trip requests.
- `resolveWorkspaceAuthSnapshot` now re-reads the current Supabase session instead of immediately returning an existing snapshot, which allows fresh access tokens to flow into chat, board, trip-list, and trip-management requests.
- Added a Supabase `onAuthStateChange` subscription in the workspace so `SIGNED_IN`, `TOKEN_REFRESHED`, and `SIGNED_OUT` session changes keep the shared `authSnapshot` current while the page remains open.
- Kept the rest of the conversation-first `/chat` architecture unchanged; this is a frontend auth-refresh fix to unblock long-lived live-planning sessions and browser testing.

Plain-English Summary:
- The chat workspace was sometimes hanging onto an old Supabase access token for too long.
- Wandrix now asks Supabase for the latest session before protected trip calls and updates itself when Supabase refreshes the token in the background.
- This should stop the live `/chat` flow from suddenly failing with `Invalid or expired Supabase access token` just because the tab stayed open for a while.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Added Advanced Working Date Resolution Before Anchor Choice

Technical Summary:
- Recorded the new Advanced Planning timing rule in `docs/future-improvements.md`: rough timing must be narrowed into a working trip window before the main Advanced anchors appear.
- Added a new `resolve_dates` Advanced step, `advanced_date_resolution` board mode, and a typed date-option contract across backend and frontend conversation schemas.
- Introduced `advanced_date_resolution` conversation state and a new date-resolution generator that turns rough timing like `late March` or `long weekend` into three concrete date windows plus a recommended option.
- Added new board actions for `select_date_option`, `pick_dates_for_me`, and `confirm_working_dates`, including backend merge behavior that persists confirmed exact dates and advances Advanced Planning into anchor choice.
- Updated assistant responses and the right-side board so the user sees a dedicated date-choice workspace with pinned rough brief context, three date options, a `Pick for me` action, and an explicit proceed confirmation step.
- Expanded runtime coverage to prove rough-timing Advanced turns now enter date resolution, exact dates skip it, weekend prompts generate weekend windows, and confirmed working dates advance to anchor choice.

Plain-English Summary:
- Advanced Planning now pauses to lock a workable trip window before it asks what should lead the trip.
- If the user gives rough timing like `late March` or `long weekend`, Wandrix narrows that into three concrete date options, explains the reasoning, and waits for the user to approve one before moving on.
- This makes the later stay, hotel, flight, and activity decisions much more grounded instead of asking the user to choose anchors while the trip dates are still fuzzy.

Files / Areas Touched:
- `docs/future-improvements.md`
- `backend/app/graph/planner/date_resolution.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-22 - Cleaned Up Advanced Hotel Cards And Refreshed Stale Hotel Data

Technical Summary:
- Tightened hotel module cache reuse in `provider_enrichment.py` so previously saved hotel outputs are only reused when they are rich enough for the new card UI. Older cache entries without hotel imagery now trigger a fresh provider fetch instead of staying stuck on weak data.
- Added a regression test proving stale image-less hotel caches are refreshed even when the trip inputs themselves have not changed.
- Refined Advanced hotel-card shaping so rough-date trips fall back to planning-grade spend labels instead of the harsher old “Dates not fixed” treatment, while exact-date trips still show real nightly pricing when available.
- Simplified the Advanced hotel card and selected-hotel panel UI by removing address/source rows, dropping random destination-image fallbacks, and replacing them with a calmer hotel-specific visual treatment that only uses real hotel imagery or an explicit placeholder state.
- Applied the same no-random-image cleanup to supporting hotel surfaces so live-board and hotel reference cards no longer pretend a city photo is a hotel photo.

Plain-English Summary:
- The hotel cards on the Advanced board now look cleaner and more honest.
- If Wandrix has a real hotel photo, it uses it. If it does not, it now says so clearly instead of showing a random destination image as if it were the hotel.
- The cards also stop surfacing noisy address/source rows, and older trips can now refresh into the richer hotel data instead of staying trapped on outdated shortlist results.

Files / Areas Touched:
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_provider_enrichment.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/hotels/hotel-reference-card.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Upgraded Advanced Hotel Cards With Images And Live Nightly Rates

Technical Summary:
- Extended hotel provider normalization so `HotelStayDetail` now preserves structured hotel metadata including image URL, street address, source URL and label, hotel key, and live nightly-rate fields.
- Updated the Xotelo provider adapter to request live nightly pricing from `/api/rates` when exact stay dates exist, then keep the lowest live rate, tax estimate, and provider name alongside the search result.
- Expanded the Advanced stay hotel card contract across backend and frontend so shortlist cards can render real hotel imagery, nightly pricing, address, and source metadata instead of only summary text and a soft price hint.
- Redesigned the Advanced stay hotel shortlist and selected-hotel panels in `trip-suggestion-board.tsx` with image-led layouts, pinned nightly-rate blocks, address/source strips, and stronger visual hierarchy tied to the actual hotel fields.
- Updated supporting hotel displays on the live board and hotel reference card so selected hotels now surface richer visuals and pricing outside the shortlist too.
- Added provider-focused tests for Xotelo search and rate mapping, and expanded planner runtime assertions to verify the richer hotel metadata reaches the Advanced hotel shortlist.
- Added remote image allowlists in `frontend/next.config.ts` and moved the destination suggestion board image to `next/image`, removing the previous lint warning in the shortlist view.

Plain-English Summary:
- Hotel selection on the board now feels much closer to a real travel product instead of a plain text list.
- Wandrix can now show proper hotel photos, an honest nightly budget when exact dates exist, the hotel address, and the external source behind each option.
- The selected hotel also looks richer on the live trip board, so users can understand what they picked at a glance.

Files / Areas Touched:
- `backend/app/services/providers/hotels.py`
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_hotels_provider.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/next.config.ts`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/hotels/hotel-reference-card.tsx`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-22 - Fixed Empty Module Cache Reuse Blocking Live Shortlists

Technical Summary:
- Fixed `provider_enrichment.py` so flights, hotels, weather, and activities only reuse prior module outputs when those cached outputs actually contain data.
- Previously, if a module was ready and the configuration had not changed, Wandrix would reuse even an empty cached list, which prevented the first real live provider fetch from ever running on later planning steps like `stay -> hotel shortlist`.
- Added focused regression tests in `backend/tests/test_provider_enrichment.py` to prove that hotel and activity enrichment now refresh when the existing cached outputs are empty but the trip inputs are already ready.

Plain-English Summary:
- Wandrix was sometimes getting stuck with no live options because it treated an empty old result like a valid cache.
- This fix makes it try the real provider again when the trip is ready, so hotel shortlists and similar live results can actually appear instead of stopping at an empty state.

Files / Areas Touched:
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/tests/test_provider_enrichment.py`
- `CHANGELOG.md`

## 2026-04-22 - Added Hotel Shortlists Inside Selected Stay Strategies

Technical Summary:
- Extended `docs/future-improvements.md` to record the next Advanced Planning rule: once a stay strategy is selected, Wandrix should move directly into a hotel shortlist inside that chosen base while keeping both the stay direction and hotel choice revisable.
- Expanded the stay-planning conversation schema and frontend mirrored types with hotel shortlist state, hotel board modes, a normalized hotel card contract, selected hotel fields, and the new `select_stay_hotel` board action.
- Added stay-driven hotel shortlist generation in `suggestion_board.py`, ranking normalized hotel outputs against the selected stay strategy so hotel cards explain fit relative to that base instead of reading like generic hotel facts.
- Updated the stay-planning merge logic and runner flow so Advanced stay mode now triggers hotel enrichment, stores recommended hotels under the existing stay-planning block, and persists a working hotel selection without treating it as booked.
- Extended assistant responses and the suggestion board UI to support `advanced_stay_hotel_choice`, `advanced_stay_hotel_selected`, and `advanced_stay_hotel_review`, while keeping the selected stay strategy pinned above the hotel shortlist.
- Updated the live board stay panel to prefer the selected working hotel when one exists.
- Added backend regression coverage for hotel-shortlist activation, hotel selection persistence, and the live-hotels-first handoff inside the stay branch.

Plain-English Summary:
- Advanced Planning now goes one step further after the user chooses a stay direction.
- Instead of stopping at “what kind of area should I stay in,” Wandrix now moves into real hotel options inside that chosen base, lets the user pick a working hotel, and keeps that choice editable later if the rest of the trip changes.
- The board and planner now feel much closer to a real guided stay-selection flow rather than a placeholder stay step.

Files / Areas Touched:
- `docs/future-improvements.md`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-22 - Added Stay As The First Revisable Advanced Planning Branch

Technical Summary:
- Updated `docs/future-improvements.md` to record the new Advanced Planning rule that `stay` is the first real deep anchor path and that stay selections are working decisions that can later be reviewed instead of silently overwritten.
- Added a dedicated stay-planning state block to the planner conversation schema, including active segment tracking, recommended stay options, selected stay direction, selection rationale, assumptions, and compatibility or review status.
- Replaced the generic stay anchor placeholder with real stay-specific board modes: `advanced_stay_choice`, `advanced_stay_selected`, and `advanced_stay_review`.
- Added a shared stay card contract across backend and frontend and generated four area-strategy stay options for the first stay-first flow.
- Added the `select_stay_option` board action and persisted selected stay direction state without treating it as a hotel or booking.
- Updated assistant responses so stay-first planning now explains whether the user is choosing a stay direction, building around one, or reviewing one under strain.
- Added backend regression coverage for stay anchor selection, stay option selection persistence, review-state rendering, and non-stay anchor fallback behavior.

Plain-English Summary:
- Advanced Planning can now do something real when the user chooses `stay` first.
- Instead of stopping at a generic placeholder, Wandrix now shows four stay strategies, lets the user choose one as the current base for the trip, and keeps that choice explicitly revisable if later planning makes it weaker.
- The board and chat now stay aligned around that stay decision, which makes Advanced Planning feel more like guided trip-building and less like a staged mock flow.

Files / Areas Touched:
- `docs/future-improvements.md`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-22 - Restored The Original New Chat Prompt Cards

Technical Summary:
- Removed the newer prompt-card helper layer from the `/chat/new` welcome surface and restored the older four-card starter set directly in the assistant welcome component.
- Kept the previously restored board helper copy and retained the empty-thread scroll reset so the original presentation still opens from the top correctly.
- Cleaned up the restored greeting text so the original assistant intro renders correctly again.

Plain-English Summary:
- The new chat page now uses the older prompt cards again instead of the newer prompt style you called out.
- The original look is back, but the fix for the cut-off opening behavior is still in place.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-22 - Restored The Previous New Chat Welcome And Board Copy

Technical Summary:
- Reverted the most recent `/chat/new` welcome-surface simplification and restored the earlier assistant intro, starter prompt layout, and helper card presentation.
- Restored the previous starter-board loading shell and board-stage helper copy, including the original text for the early planning state.
- Kept the underlying empty-thread scroll reset in place so the restored layout still opens from the top correctly.

Plain-English Summary:
- The new chat page is back to the earlier version you had before the latest redesign pass.
- The board text now matches the original wording again, while the fix for the cut-off loading issue stays intact.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Reset The New Chat Opening Surface

Technical Summary:
- Reworked the `/chat/new` assistant welcome state into a simpler chat-native layout with a short intro, a smaller starter list, and a lighter loading shell while keeping the empty-thread scroll reset in place.
- Reduced the starter prompts from a taller multi-card stack to a cleaner compact set so the first screen sits naturally above the composer without feeling like a landing page inside the thread.
- Simplified the starter live board shell and helper copy so the right pane reads as a quiet staged placeholder instead of a large mockup block.

Plain-English Summary:
- The new chat screen has been reset to feel cleaner and calmer.
- The opening chat view is simpler now, and the board side stays present without pulling too much attention before trip planning really begins.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Fixed New Chat Welcome Clipping

Technical Summary:
- Simplified the `/chat/new` empty-state assistant layout so the opening content behaves like a compact chat surface instead of a stacked hero block inside the thread.
- Split the empty-thread viewport behavior from the normal conversation layout and added an explicit top-scroll reset so brand-new chats no longer load at the bottom of the chat pane.
- Kept the richer starter prompts and composer guidance from the earlier first-turn polish while making the initial shell fit safely above the fixed composer.

Plain-English Summary:
- The new chat screen no longer opens in a cut-off or partially scrolled state.
- Starting a fresh trip should now feel cleaner and more stable, with the welcome content showing from the top instead of looking chopped off.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Fixed Advanced Brief Flexibility And Anchor Flow Sync

## 2026-04-21 - Polished The First-Turn Chat Surface

Technical Summary:
- Reworked the empty `/chat` assistant surface into a more intentional opening layout with a stronger intro, clearer "talk naturally" guidance, and richer starter prompts that better match the conversation-first product shape.
- Added reusable starter-prompt helpers and refreshed the initial loading shell so the first-load state mirrors the real chat surface instead of feeling like a generic skeleton.
- Updated the composer placeholder so the first input reads more like a natural travel conversation prompt and shifts to a lighter follow-up prompt once the thread has started.

Plain-English Summary:
- The first chat screen should now feel more polished and easier to start from.
- Instead of a plain empty state, users now get clearer examples, better starter ideas, and a prompt that encourages natural conversation rather than form-filling.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

Technical Summary:
- Added `from_location_flexible` to the structured board action contract end to end, wired the Advanced details board to let users explicitly mark departure as flexible, and persisted that flag through board confirmation into planner memory and draft state.
- Fixed the planner merge path so departure flexibility can be turned on or off cleanly instead of only sticking once set.
- Tightened assistant-response branching so Advanced anchor selection now returns the anchor-specific reply even when the chat audit message also contains `requested_planning_mode="advanced"`.
- Stabilized the chat sidebar's first render during hydration by deferring live trip-row rendering and relative-time formatting until the client is hydrated.
- Replaced the theme bootstrap `next/script` usage with a static inline head script to reduce the client-side script-tag warning observed during live testing.
- Added backend regression coverage for flexible-departure board confirmation and for Advanced anchor selection winning over stale mode-selection echo behavior.

Plain-English Summary:
- The Advanced brief board now truly supports "departure still flexible" instead of quietly forcing the user to enter an origin.
- After choosing an Advanced anchor like `stay`, the chat reply now matches the board instead of repeating the older "Advanced Planning is selected" message.
- The left sidebar should now hydrate more cleanly on load instead of briefly rendering the wrong empty state before recent trips appear.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/app/layout.tsx`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_bootstrap.py`
- `CHANGELOG.md`

## 2026-04-21 - Kept Greeting Turns Light Before Trip Planning Starts

Technical Summary:
- Added an LLM-driven opening-turn endpoint so Wandrix can decide whether a first message is still generic conversation or the real start of trip planning before a persisted trip is created.
- Added a detached persisted-trip handoff in the chat workspace so `/chat/new` can create a real backend thread behind the scenes without immediately swapping the visible UI onto a saved trip after the first planning message.
- Updated the assistant runtime to keep non-planning opening turns on the lightweight draft surface, append hidden backend turns into the real trip cache only after planning begins, and only activate the persisted trip once the backend draft shows actual trip-planning signal.
- Tightened the backend planning-mode gate so generic conversation no longer triggers Quick Plan versus Advanced Planning before the trip brief is actually confirmed, and refreshed the opening-phase assistant copy to introduce Wandrix more naturally.

Plain-English Summary:
- Saying something simple like "hi" should no longer make the chat feel like it reloads into a saved trip before the reply appears.
- Wandrix now stays conversational for generic opening messages, introduces itself more clearly, and only brings in planning-mode choices once the trip has genuinely started.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/lib/api/conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `backend/app/api/router.py`
- `backend/app/api/routes/conversation.py`
- `backend/app/graph/planner/opening_turn.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/conversation.py`
- `backend/app/services/conversation_service.py`
- `CHANGELOG.md`

## 2026-04-21 - Kept Sidebar Sessions Stable While Opening /chat/new

Technical Summary:
- Added route-memory and pre-paint cached-trip hydration to the chat workspace so navigating between `/chat` and `/chat/new` no longer remounts the sidebar into an empty state before recent trips reload.
- Passed the signed-in user ID from the shared chat page shell so the client workspace can immediately restore the correct recent-trip cache for that user without waiting for the slower auth/trip bootstrap flow.

Plain-English Summary:
- Clicking New Trip should no longer wipe the left sidebar for a moment before your saved chats come back.
- The new chat route now opens quickly while the existing recent sessions stay visible and steady.

Files / Areas Touched:
- `frontend/src/components/chat/chat-page-shell.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added A Real /chat/new Route For The New Trip Button

Technical Summary:
- Added a dedicated `/chat/new` route and shared server-side chat page shell so the New Trip action can open a fresh planner state without reusing the same `/chat` URL.
- Updated the chat workspace to honor an `initialMode="new"` fast path that opens an ephemeral local draft immediately, while still hydrating the saved-trip sidebar in the background.
- Ensured saved-trip selection and trip persistence route back onto the normal `/chat?trip=...` path so only the New Trip flow uses `/chat/new`.

Plain-English Summary:
- Clicking New Trip now has its own clean URL, `/chat/new`, instead of pretending to be the same page as an existing chat.
- That makes a fresh chat open more predictably and keeps the saved chats behavior separate from the new-chat flow.

Files / Areas Touched:
- `frontend/src/components/chat/chat-page-shell.tsx`
- `frontend/src/app/chat/page.tsx`
- `frontend/src/app/chat/new/page.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Stopped Saved-Trip Sidebar Loads Timing Out Too Early

Technical Summary:
- Increased the recent-trip bootstrap and refresh timeouts in the chat workspace after confirming the current backend trip-list query takes roughly 4.8 seconds for the active user’s dataset.
- This prevents the frontend from abandoning `/api/v1/trips?limit=24` prematurely and falling back to an empty sidebar even when the backend eventually responds successfully.

Plain-English Summary:
- The saved chats list was going empty because the frontend was giving up before the trip list finished loading.
- Wandrix now waits long enough for the real trip list to come back, so previous chats should actually appear instead of being treated like there are none.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Restored Sidebar Hydration While A Local Draft Is Open

Technical Summary:
- Fixed the chat workspace bootstrap so an active ephemeral local draft no longer short-circuits saved-trip hydration before cached and remote recent trips are loaded.
- Preserved the current local draft workspace while still refreshing the sidebar list for the signed-in user, preventing the left rail from going empty just because the main pane is in a temporary draft state.

Plain-English Summary:
- Opening or landing in a temporary local draft no longer blanks out the saved chats sidebar.
- The app should now keep your current draft chat open while still showing your real saved sessions on the left.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Restored Persisted Chats To The Sidebar And Blocked Draft IDs

Technical Summary:
- Removed the over-aggressive recent-trip “meaningful” filter for persisted trips so the sidebar no longer hides legitimate saved chats that are still in early planning states.
- Kept the new guard that excludes local-only `draft_trip_*`, `draft_browser_session_*`, and `draft_thread_*` identifiers from recent-trip hydration and API-driven workspace loading.
- Updated the chat workspace to ignore and strip stale draft trip IDs from the URL instead of attempting backend fetches for them.

Plain-English Summary:
- Real saved chats should show up in the sidebar again, even if they were still pretty early or lightly filled out.
- Fake local draft IDs are still blocked, so the app should stop making those broken `draft_trip_...` API requests.

Files / Areas Touched:
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Reverted Navbar-Driven Forced New Chat Routing

Technical Summary:
- Removed the `/chat?new=1` routing from the primary Chat entry points and restored the chat workspace bootstrap to its previous selection flow without the forced-new override path.
- Kept the separate saved-trip rename feature intact while reverting only the navbar and placeholder behavior that had started interfering with chat/session loading.

Plain-English Summary:
- The Chat link now behaves the old way again instead of trying to force a fresh session.
- This reverts the navbar-specific change that was disrupting how chats and saved sessions were loading.

Files / Areas Touched:
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/placeholder-page.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Kept Saved Chats Visible While Navbar Chat Starts Fresh

Technical Summary:
- Moved the `/chat?new=1` handling deeper into the workspace bootstrap so a forced-new chat now creates an ephemeral active workspace without short-circuiting the normal saved-trip sidebar hydration flow.
- Updated the workspace selection logic to ignore `last active trip` restoration when the new-chat flag is present, while still loading cached and refreshed recent trips for the left rail.

Plain-English Summary:
- Clicking Chat in the navbar now starts a fresh conversation without hiding the saved chats list.
- The left sidebar still loads your previous chats normally; only the active chat opens as new.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Made Navbar Chat Open A Fresh Planner And Added Trip Rename

Technical Summary:
- Updated the primary Chat entry points to route into `/chat?new=1`, and taught the chat workspace bootstrap to honor that flag by opening an ephemeral new planning session instead of auto-restoring the most recent saved trip.
- Kept the saved-trip sidebar hydrated during forced-new chat loads by still resolving auth and refreshing recent trips in the background, without letting that flow take over the active workspace.
- Added a saved-trip rename action in the chat sidebar that persists a new title through the trip-draft API and updates the active workspace, prefetched workspaces, and recent-trip list in place.

Plain-English Summary:
- Clicking Chat in the navbar should now start a fresh conversation instead of unexpectedly dropping you back into an older trip.
- Saved chats can also be renamed directly from the sidebar now, so it is easier to keep the trip list tidy and recognizable.

Files / Areas Touched:
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/placeholder-page.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Preserved Destination Alternatives And Advanced Anchor Sequencing

Technical Summary:
- Added `requested_advanced_anchor` to planner turn updates and taught the Advanced Planning runtime to accept anchor choices directly from chat, so instructions like `stay first, flights later` can move the flow into `anchor_flow` without forcing flights out of scope.
- Added unresolved-destination helper handling so when the user names multiple possible places like `Kyoto or Osaka`, the board and assistant can keep both options visible instead of falling back to a generic helper state.
- Extended planner prompt coverage and runtime regressions for destination-option preservation and chat-driven Advanced anchor selection, while keeping existing merge semantics and board-action anchor selection intact.

Plain-English Summary:
- Wandrix is now better at handling `there are two real options here` and `I know the sequence I want, but not every final detail yet`.
- If someone says `Kyoto or Osaka`, the planner can keep both destinations alive instead of acting like one has to be chosen immediately.
- If someone says `stay first, flights later` inside Advanced Planning, Wandrix can treat that as a real sequencing choice and move the trip into the `stay` path without pretending flights are no longer part of the trip.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-21 - Kept Sidebar Order Steady During Saved-Trip Refreshes

Technical Summary:
- Added a sidebar-refresh merge path that updates saved-trip metadata in place while preserving the existing visible order for trips already on screen.
- Limited background recent-trip refreshes to append only truly unseen trips in recency order instead of re-sorting the entire sidebar list every time the backend sends fresh trip metadata.
- Wired the chat workspace refresh flow to use this calmer merge behavior so sidebar updates feel less jumpy during normal session use.

Plain-English Summary:
- The saved chats list should move around less now when Wandrix refreshes trip data in the background.
- Existing trips stay in a steadier order, while genuinely new trips can still appear without making the whole sidebar feel like it reshuffled itself.

Files / Areas Touched:
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Trimmed The Activities-Only Intake Path

Technical Summary:
- Updated the frontend trip-details step model so the `budget` step is no longer shown when the active scope is `activities` only, matching the backend planner logic that already treated budget as irrelevant outside flights and hotels.
- Added an Advanced Planning details-board subtitle branch for `activities`-only scope so the board now explicitly says flights and hotels can wait, instead of falling back to generic full-trip brief language.
- Added a planner runtime regression proving that an Advanced activities-only brief stays in a narrowed details-collection state without surfacing budget as a needed detail.

Plain-English Summary:
- When someone tells Wandrix to focus only on activities for now, the board should actually behave that way.
- The planner no longer shows a stray budget step for that scope, and the board copy now makes it clearer that flights and hotels can be left for later instead of feeling half-required in the background.
- This makes narrowed scope feel intentional rather than like a full-trip form with a few optional boxes hidden.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-model.ts`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-21 - Replaced Generic First-Load Chat Placeholders With A Steadier Shell

Technical Summary:
- Added a dedicated initial assistant shell for the very first `/chat` load so the empty thread now renders structured planning cards instead of falling straight into a generic disabled welcome state while the workspace attaches.
- Added a matching initial board shell that previews the future trip-board layout with lightweight skeleton blocks instead of the old generic loading copy and spinner-only treatment.
- Updated the chat composer’s disabled placeholder so the first-load state reads as a deliberate workspace-preparation step rather than an indeterminate attach error.

Plain-English Summary:
- The first time `/chat` opens, Wandrix should now feel more intentional and less awkward.
- Instead of looking half-loaded, the page shows a calm preview of the chat and board layout while the workspace gets ready in the background.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Reused Auth And Recent-Trip State During Chat Switches

Technical Summary:
- Refactored the chat workspace bootstrap path to reuse the existing auth snapshot and in-memory recent-trip state instead of re-reading both on every trip change.
- Limited the saved-trip background refresh to once per active recent-trip cache key, avoiding repeated sidebar refresh work during each saved-chat switch.
- Kept the trip-loading fast path compatible with the earlier sidebar prefetch changes so warmed trips can still be adopted without extra bootstrap churn.

Plain-English Summary:
- Opening another saved chat should feel a bit lighter now because Wandrix stops repeating some setup work it already finished earlier in the session.
- The sidebar also does less background refreshing during switches, which should make the whole page feel calmer and more consistent.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Made Traveller Count Flexibility A Real Intake State

Technical Summary:
- Added structured `travelers_flexible` support across trip configuration, conversation schemas, planner turn updates, board actions, and shared details-form state so the planner can preserve explicitly soft traveller counts instead of treating them as simply missing.
- Updated Advanced-mode missing-field logic, details checklist formatting, provider-readiness checks, and planner observability so a flexible traveller count can keep the shared brief moving while still blocking flight and hotel enrichment until a reliable adult count exists.
- Removed the hidden `1 adult` board default, normalized zero counts back to `null`, and added runtime regressions proving that flexible traveller counts can reach Advanced anchor choice while `0 adults` never counts as reliable selection data.

Plain-English Summary:
- Wandrix can now understand the difference between `we have not decided yet` and `we forgot to answer`.
- If someone says the traveller count is still flexible, Advanced Planning can keep building the brief without forcing a hard headcount too early.
- At the same time, the planner no longer quietly treats placeholder values like `0 adults` or the old default `1 adult` as real trip decisions, so the intake flow should feel less pushy and more honest.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/details_collection.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Prefetched Saved Trip Workspaces From The Chat Sidebar

Technical Summary:
- Added sidebar-triggered trip warmup so hovering or focusing a saved chat can preload its workspace payload and conversation history before the route switch completes.
- Reworked the workspace bootstrap path to reuse prefetched trip payloads instead of immediately re-fetching the same trip after the URL changes.
- Updated the sidebar selection handshake so clicking a saved chat marks the next requested trip earlier, giving the workspace a cleaner handoff target during the switch.

Plain-English Summary:
- Saved chats should open more quickly now because Wandrix starts loading the next trip a little earlier, often before you fully switch into it.
- The app also does less duplicate work during a trip change, which should make the whole handoff feel snappier and more consistent.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Reduced Chat Runtime Remounts During Trip Switches

Technical Summary:
- Removed the trip-keyed assistant runtime remount from the chat pane and replaced it with in-place thread hydration that resets the existing assistant thread only when the active trip truly changes.
- Added guarded runtime hydration logic so background history sync can refresh the current thread when the user has not diverged locally, while leaving in-progress local conversation state alone.
- Consolidated thread-message serialization helpers so runtime hydration and local cache persistence use the same text-only snapshot rules.

Plain-English Summary:
- Switching between saved chats should feel steadier now because the chat engine stays alive instead of fully restarting every time you open another trip.
- If Wandrix loads fresher saved messages for the same trip in the background, it can update the thread more cleanly without clobbering what someone is actively doing.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Made Custom Trip Style A Real Planner Field

Technical Summary:
- Added structured `custom_style` support across trip configuration, conversation schemas, board actions, planner turn updates, and shared details-form state so freeform trip-style notes can persist like any other brief field.
- Updated planner merge, checklist, and response logic so a custom style now satisfies the trip-style requirement, appears in saved brief summaries, and can influence Advanced Planning behavior instead of living only in temporary frontend form state.
- Extended the planner understanding prompt and regression suite so style descriptions that do not fit the preset style chips can be preserved explicitly rather than dropped.

Plain-English Summary:
- The free-text trip-style input on the board now actually works as a real saved planner detail.
- If someone types a vibe like “slow temple mornings and market-heavy afternoons,” Wandrix now keeps that as part of the trip brief instead of losing it after the form step.
- This makes the trip-style part of intake much more trustworthy, because the board is no longer promising something the planner was not truly storing.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/details_collection.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Debounced Local Chat History Persistence

Technical Summary:
- Debounced the assistant thread’s local-storage persistence so message-state updates no longer write the full cached conversation on every immediate runtime change.
- Added a serialized snapshot guard so identical thread states are skipped entirely instead of being re-written redundantly.

Plain-English Summary:
- Chat should feel a bit steadier during message generation and restore because Wandrix is doing less unnecessary browser storage work in the background.
- The app still keeps local chat history, but it now saves it more efficiently.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Let Budget Posture Stand On Its Own During Intake

Technical Summary:
- Aligned the frontend details-board budget-step completion rule with the backend planner contract so a required budget step now completes when the user provides either `budget_posture` or `budget_gbp`, instead of incorrectly forcing both.
- Updated the budget-step copy to explain that a budget posture alone is enough for early planning and that the exact amount can stay optional until the user knows it.
- Added a runtime regression covering the “posture only” case so the shared brief continues to treat a soft budget as sufficient planner signal.

Plain-English Summary:
- Users no longer have to enter both a budget label and an exact GBP number just to move past the budget step.
- Saying something like “mid-range” is now enough during intake, which matches how the planner already thinks about early budget guidance.
- This makes the board less pushy and keeps Advanced Planning more conversational in the early brief-building stage.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-21 - Kept Advanced Mode In Guided Brief Collection For Thinner Trips

## 2026-04-21 - Removed The Fake Client-Side Chat Typing Delay

Technical Summary:
- Removed the client-side sentence chunking and `sleep(120)` replay in the assistant runtime so completed backend responses are now yielded to the chat UI immediately.
- Kept the same backend conversation path and abort behavior, but stopped artificially stretching already-finished responses in the browser.

Plain-English Summary:
- Chat replies should now feel faster because Wandrix no longer pretends to type out a response that the backend has already finished.
- This makes the assistant feel more direct and reduces the sense of lag after each message.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

Technical Summary:
- Relaxed the details-board gate for Advanced Planning so the shared trip-details board can appear as soon as a destination exists, even before an origin signal is present, instead of dropping weaker briefs into generic decision cards.
- Updated Advanced details-board titles, subtitles, and assistant copy so the shared brief-building stage is named explicitly and the user is told that anchor choice comes after the brief is stronger.
- Added regression coverage proving that selecting Advanced on a thin brief now prefers `details_collection` over generic decision cards while preserving the later branch into anchor choice.

Plain-English Summary:
- Advanced Planning now feels more guided earlier in the flow.
- If the user picks Advanced before all the trip basics are filled in, Wandrix will keep them in the structured trip-details step instead of showing vague “next decisions” cards too soon.
- This makes the path easier to understand: first finish the brief, then choose the first Advanced Planning anchor.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `CHANGELOG.md`

## 2026-04-21 - Let Advanced Intake Keep Departure Flexible

Technical Summary:
- Added structured `from_location_flexible` planner state through trip configuration, conversation types, turn updates, and the shared details-form contract so Wandrix can distinguish an intentionally flexible departure from a simply missing origin.
- Updated Advanced intake missing-field logic, route checklist rendering, anchor recommendation, provider-readiness checks, and assistant copy so a flexible departure no longer behaves like an immediate blocker during brief-building, while still preventing flight-ready execution until a real origin is chosen later.
- Updated the frontend trip-details route step to treat a flexible departure as route-complete, added clearer board copy explaining that origin can stay open for now, and added regressions for the Kyoto-style flexible-origin flow plus prompt coverage for the new extraction rule.

Plain-English Summary:
- If the user says their departure point is still flexible, Wandrix now treats that as a real planning choice instead of acting like the user forgot to fill something in.
- In Advanced Planning, the brief can now move forward without forcing a departure city too early, and the planner will avoid recommending flight-first just because flights are switched on by default.
- This makes the flow feel more natural for prompts like “Kyoto in late March for five nights, departure still flexible for now.”

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/details_collection.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Tightened Advanced Anchor State Quality Before Stay Flow

Technical Summary:
- Fixed Advanced anchor decision-history deduplication so reselecting the same anchor no longer creates duplicate `Advanced anchor selected` events in planner memory.
- Refined the anchor recommendation heuristic so short or route-soft trips can recommend `flight` before defaulting too eagerly to `stay` when hotels are simply enabled in the scope.
- Corrected the selected-anchor board copy so `advanced_next_step` no longer tells the user that the anchor choice still lies ahead after it has already been made, and added regressions covering both the new recommendation behavior and anchor dedupe.

Plain-English Summary:
- The new Advanced anchor step is now cleaner and more trustworthy.
- Wandrix is less likely to keep recommending `stay` for the wrong reasons, it will not keep recording the same anchor choice over and over, and the board wording now matches the state the user is actually in.
- This gives us a safer base before building the first deeper `stay` planning flow.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added The First Real Advanced Planning Anchor Choice

Technical Summary:
- Added structured Advanced Planning anchor state with `advanced_anchor` plus a new board action for selecting one of four anchors: `flight`, `stay`, `trip_style`, or `activities`.
- Replaced the placeholder post-brief Advanced board with a real `advanced_anchor_choice` state that shows all four anchor cards, marks one as recommended using structured planner heuristics, and lets the user select any of them.
- Persisted anchor selection into conversation state and decision history, then routed Advanced into `anchor_flow` with dedicated board and assistant copy instead of falling back to generic helper messaging.

Plain-English Summary:
- Advanced Planning now has its first real guided decision.
- Once the trip brief is ready, Wandrix shows four ways to begin the deeper planning flow: flights, stay, trip style, or activities.
- The planner recommends a sensible starting point, but the user stays in control and can pick any anchor they want.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Split Advanced Planning Into A Real Post-Brief Guided Flow

Technical Summary:
- Added structured `advanced_step` state to the planner conversation model and now resolve Advanced Planning into `intake` while the shared brief is still being collected, then `choose_anchor` as soon as the brief is confirmed and ready to branch.
- Updated planner board generation and assistant response logic so Advanced Planning no longer falls through to generic post-brief copy; it now surfaces a dedicated `advanced_next_step` board state and guided response that explicitly pauses before itinerary drafting.
- Kept Quick Plan behavior intact while protecting Advanced from quick-plan generation, and added a regression proving Advanced reaches `choose_anchor` without calling the quick itinerary draft path.

Plain-English Summary:
- Advanced Planning now behaves like a real separate mode once the trip brief is ready.
- Instead of jumping straight into an itinerary draft, Wandrix now stops and shows that the next guided step is choosing what should lead the trip first.
- This gives us a clean base for the next phase, where the user will actually choose between flights, stay, trip style, or activities as the first Advanced Planning anchor.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Kept Current Chat And Board Visible During Trip Switches

Technical Summary:
- Split the chat workspace into requested-trip and displayed-trip state so `/chat` can keep rendering the current conversation and board while the newly selected trip is still hydrating.
- Passed the switching state through the assistant and board preview so inputs are temporarily disabled during the handoff, while lightweight in-place banners explain that the next saved trip is opening.
- Updated the board sandbox preview to match the new board-preview contract introduced by the trip-switch continuity work.

Plain-English Summary:
- When you click another saved trip, Wandrix now keeps the current chat and board on screen instead of dropping into an awkward empty loading state.
- You still get a clear signal that a different trip is opening, but the page feels steadier and more polished while the handoff happens.
- This is the second smoothing pass for chat, focused on making trip switching feel continuous instead of jarring.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added A Smoother Chat-To-Chat Handoff Transition

## 2026-04-21 - Simplified The Chat Switch Motion To A Cleaner Fade

Technical Summary:
- Removed the more animated trip-switch treatment and replaced it with a much simpler handoff: a light fade on the outgoing content plus a quiet status pill instead of a larger transfer card with animated progress.
- Kept the improved requested-trip handoff structure intact while reducing motion complexity in both the chat pane and the live board.

Plain-English Summary:
- Chat switching should now feel calmer and less distracting.
- The handoff is still clearer than before, but the transition no longer tries to animate so much.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

Technical Summary:
- Reworked the trip-switch state in the chat pane and live board so the currently displayed content now eases into a dimmed handoff state instead of staying fully static while the next trip hydrates.
- Replaced the plain switch banners with subtle overlay cards and a lightweight animated progress line, making the transition feel intentional without introducing heavy motion or dashboard-style chrome.
- Added shared transition utilities in global CSS, including reduced-motion fallbacks so the switch treatment stays calm and accessible.

Plain-English Summary:
- Switching between chats should now feel smoother and more polished instead of looking like the old trip is just frozen on screen.
- The previous chat and board still stay visible briefly, but they now fade into a proper “handoff” state while the next trip opens.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-21 - Softened The Sidebar Delete Affordance

Technical Summary:
- Reduced the visual weight of the sidebar delete control by shrinking the trigger, lowering its idle contrast, and revealing it primarily on row hover or focus instead of keeping it fully present at all times.
- Kept the same delete dialog behavior and theme tokens, while making the row action feel secondary to the trip title and activity metadata.

Plain-English Summary:
- The delete icon is still there, but it should feel much more subtle now.
- It stays out of the way until you hover the row, so the sidebar reads more like a clean chat list and less like an action menu.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Matched The Chat Delete Action To Sidebar Theme Tokens

Technical Summary:
- Replaced the sidebar trip-delete trigger from an overflow-style icon to an explicit trash icon so the affordance reads as a destructive action immediately.
- Swapped the delete dialog actions onto the shared button system so the cancel and delete states now use the same theme-aware variants and token-driven styling as the rest of the chat UI.

Plain-English Summary:
- The delete action now looks like a real delete control instead of a generic menu button.
- The confirmation dialog also fits the rest of the app better now, without one-off colors that felt out of place.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added Permanent Trip Deletion From The Chat Sidebar

Technical Summary:
- Added a real backend trip-deletion route and service path so deleting from the chat sidebar now removes the owned trip record and its cascade-owned draft and brochure data from the database.
- Extended the frontend trip API client with `DELETE` support, then wired the chat sidebar to show a confirmation dialog before deletion and to remove the deleted trip from recent-trip state and cached local thread history.
- Updated `/chat` workspace recovery so deleting the currently open trip cleanly routes to the next saved trip when available, or back to an ephemeral new-draft shell when no saved trips remain.

Plain-English Summary:
- You can now delete a saved chat directly from the sidebar instead of leaving old trips stuck in the account forever.
- Wandrix asks for confirmation first, and once deleted the trip is fully removed rather than just hidden from the list.
- If you delete the trip you are currently viewing, the app now moves you to the next sensible state instead of leaving the page stranded.

Files / Areas Touched:
- `backend/app/api/routes/trips.py`
- `backend/app/services/trip_service.py`
- `backend/app/repositories/trip_repository.py`
- `backend/app/schemas/trip.py`
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/trips.ts`
- `frontend/src/lib/chat-history-cache.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Stabilized Chat Sidebar Recents And Stopped Auto-Creating Blank Trips

Technical Summary:
- Reworked recent-trip handling so the chat sidebar now filters out untouched placeholder trips, keeps a stable updated-at sort, and stops forcing the currently open workspace to the top on every local refresh.
- Kept the selected trip inside the visible recent-trips window and ignored no-op clicks on the already-open trip, reducing the jumpy behavior where items appeared to disappear or reshuffle unexpectedly.
- Changed `/chat` bootstrap fallback so opening chat without a meaningful saved trip now starts from an ephemeral local draft instead of creating a persisted empty trip record before the user actually begins planning.

Plain-English Summary:
- The recent chats list should now feel steadier: older chats should stop jumping to the top or vanishing from the visible list when you open them.
- Placeholder trips that were never really started are now hidden from the sidebar, which cuts down on confusing blank items.
- Wandrix also stops creating those accidental empty saved trips just because the chat page opened before a real conversation started.

Files / Areas Touched:
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added Weather Preference To Shared Quick And Advanced Intake

Technical Summary:
- Extended the shared trip-details intake contract so `weather_preference` now flows through planner turn updates, trip configuration, conversation board actions, details-form state, checklist rendering, and assistant trip-shape summaries.
- Updated the planner understanding prompt and conversation-state question logic so weather preference is treated as a structured timing-adjacent preference rather than a heuristic side note, while still keeping it optional for confirmation.
- Added the timing-step UI for weather preference selection in the shared trip-details board and covered both LLM-extracted persistence and board-confirmed persistence with backend regressions.

Plain-English Summary:
- Quick Plan and Advanced Planning now ask about preferred weather in the same shared trip-details flow instead of treating it like a separate later concern.
- Users can say they want something warm, sunny, mild, cool, snowy, or dry, and Wandrix will keep that as part of the working brief.
- This makes the early intake feel more complete without forcing weather to become a required blocker before planning can continue.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/details_collection.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/conversation.ts`
- `CHANGELOG.md`

## 2026-04-21 - Smoothed Chat Trip Opening By Removing Extra Blocking Work

Technical Summary:
- Shortened the `/chat` bootstrap path for existing trips by skipping browser-session creation when only loading an already persisted trip workspace and by parallelizing `getTrip` with `getTripDraft`.
- Removed the explicit-trip dependency on a fresh saved-trips fetch during critical path bootstrap so chat can open the selected trip using cached sidebar data first and refresh supporting lists later.
- Updated the assistant pane to use cached thread messages immediately on trip change instead of showing a separate restore screen while history sync catches up in the background.

Plain-English Summary:
- Opening chat or switching to another saved trip should now feel more immediate because Wandrix no longer waits on setup work that is only needed for creating brand-new trips.
- The conversation pane also keeps more continuity now: if local thread history exists, it appears right away instead of flashing a temporary restore message before the chat comes back.
- This is the first smoothing pass focused on reducing visible waiting and inconsistent state changes during chat boot.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Added Post-Prompt Planning Mode Gate For Quick And Advanced

Technical Summary:
- Updated the planner runner so the first user prompt can populate the working trip brief, but Wandrix now pauses to require a planning mode choice before continuing normal planning when no mode has been selected yet.
- Changed planning mode resolution so `select_advanced_plan` now sets a real `advanced` mode instead of immediately converting to Quick fallback, and wired a new mode-choice-required flag through conversation state, suggestion-board generation, and assistant response building.
- Reworked the planning-mode choice board copy so both Quick and Advanced are selectable after the first prompt, updated Advanced selection messaging to remove fallback wording, and added regressions for the new gate plus real Advanced mode selection.

Plain-English Summary:
- After the user sends their first trip message, Wandrix now stops and asks whether they want Quick Plan or Advanced Planning before going further.
- The app still keeps what the user already said, so they do not have to repeat the trip request after choosing.
- Advanced Planning now behaves like a real chosen mode at this stage instead of being described as an automatic Quick Plan fallback.

Files / Areas Touched:
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_runtime_quality.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Expanded Spinner Demo With 50 More Travel Loading Studies

Technical Summary:
- Added a new `spinner-demo` catalog module with 50 extra travel-related spinner variants built from reusable animation families instead of adding another large block of inline demo JSX to the page file.
- Introduced demo-scoped keyframes for lane travel, shutter panels, and bobbing icon motion so the added loaders can feel more layered while keeping the implementation organized.
- Updated the spinner demo page to render the combined 130-option catalog and refreshed the intro copy to reflect the larger travel-focused set.

Plain-English Summary:
- The spinner demo now includes 50 more travel-themed loading animations, bringing the page up to 130 options.
- The new group leans into planes, trains, hotels, tickets, maps, routes, luggage, ships, and other travel cues, but keeps the motion tidy and readable instead of chaotic.
- The demo is also easier to extend now because the extra spinners live in their own catalog file instead of making the page even more unwieldy.

Files / Areas Touched:
- `frontend/src/app/spinner-demo/page.tsx`
- `frontend/src/components/spinner-demo/more-travel-spinners.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Simplified Advanced Planning To Selected-State Only For Now

Technical Summary:
- Refined `docs/future-improvements.md` again to remove redirect-specific state tracking from the near-term `Advanced Planning` roadmap.
- Kept the product boundary that real booking happens outside Wandrix, but simplified current planner semantics to center on `recommended`, `selected`, and a later user-confirmed `booked` state.
- Updated the suggested implementation order and board-state language so the next build phase does not depend on redirect tracking.

Plain-English Summary:
- The roadmap is now simpler and more practical for the next build phase.
- For now, Wandrix only needs to remember what the user selected. We do not need special redirect tracking yet.
- Booking still happens outside Wandrix, and a true booked state can be added later when we build that part.

Files / Areas Touched:
- `docs/future-improvements.md`
- `CHANGELOG.md`

## 2026-04-21 - Added Advanced Planning And Manual Organizer Roadmap Notes

Technical Summary:
- Expanded `docs/future-improvements.md` with a dedicated `Advanced Planning Roadmap` section.
- Documented Advanced Planning as a real trip-building mode rather than a slower Quick Plan, including staged progression through brief confirmation, planning anchor choice, trip skeleton building, tradeoff resolution, sequential enrichment, and reviewed pre-finalization.
- Added future roadmap notes for `recommended / shortlisted / selected / booked / rejected / manual` semantics across flights, hotels, activities, and events.
- Added a dedicated manual trip-organizer subsection covering user-entered bookings, contacts, addresses, confirmation details, and logistics notes for items booked outside Wandrix.

Plain-English Summary:
- The roadmap now clearly says what Advanced Planning is supposed to become.
- Instead of just being “better planning,” it is now defined as the mode where Wandrix helps choose the real trip components and eventually organizes the whole trip in one place.
- The doc also now captures the future direction for manual additions, so later we can support user-booked hotels, flights, reservations, notes, and contact details inside the same trip plan.

Files / Areas Touched:
- `docs/future-improvements.md`
- `CHANGELOG.md`

## 2026-04-21 - Clarified Advanced Planning As Selection And External Booking Redirect Flow

Technical Summary:
- Refined the `Advanced Planning Roadmap` in `docs/future-improvements.md` so Wandrix is explicitly documented as a selection-and-organization product rather than a booking platform.
- Added a dedicated `Keep Booking External` subsection describing the intended flow: recommend, select, redirect to provider, and optionally confirm the booking later.
- Expanded future state semantics to distinguish `selected`, `redirected_for_booking`, and later `booked` confirmation, and updated the implementation order and board-state language to match that boundary.

Plain-English Summary:
- The roadmap now clearly says Wandrix helps users choose what to book, but does not do the booking itself.
- When someone picks a flight or hotel, Wandrix should send them to the external provider site and remember what they chose, rather than pretending the booking already happened.
- This keeps the product honest and gives us a cleaner foundation for future manual booking confirmation features.

Files / Areas Touched:
- `docs/future-improvements.md`
- `CHANGELOG.md`

## 2026-04-21 - Moved Saved Trips Into Global Navigation And Removed Brochure Shortcut From Chat

Technical Summary:
- Added `Saved Trips` to the shared top navigation directly beside `Chat` and updated nav active-state logic so brochure detail routes also resolve under the saved-trips section.
- Replaced the chat sidebar footer brochure shortcut with an empty `Configuration` placeholder control so the chat workspace stays focused on conversation and the live board.
- Renamed the `/trips` library heading and empty-state copy from brochure-centric wording to `Saved Trips` so the destination page matches the new navigation label.

Plain-English Summary:
- Saved trips now have a clear place in the main navbar instead of being tucked into the chat sidebar.
- The chat page no longer advertises brochures in a place that feels off-flow, and there is now a placeholder for future trip configuration work.
- The saved-trips page wording now matches what people will expect after clicking the new nav item.

Files / Areas Touched:
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-21 Through PI-25 Resume Summaries, Provider Discipline, Evaluation Set, Regressions, And Observability

Technical Summary:
- Extended planner turn summaries so they now store structured resume state including compact summary text, open fields, next open question, and active planner focus.
- Reworked provider activation so readiness is evaluated through structured signals instead of only broad missing-field checks, and passed allowed-module gating into provider enrichment.
- Updated assistant behavior so Quick Plan can explicitly wait on missing provider readiness instead of sounding like live planning already started.
- Added a fixed evaluation fixture set for planner scenarios covering broad asks, rough timing, corrections, rejections, soft approvals, explicit confirmation, profile-context handling, and module-scope narrowing.
- Added new runtime regressions for resume summaries, provider gating, non-flight Quick Plan readiness, and evaluation-set integrity, plus structured `planner_observability` metadata in the runner for easier debugging.

Plain-English Summary:
- Wandrix now remembers the last meaningful planning turn in a much more useful way, so resumed trips should feel less like starting over.
- The planner is also more disciplined about when it triggers live provider work. It now waits for the brief to be strong enough and tells the truth if Quick Plan is selected but still blocked by missing certainty.
- On top of that, the repo now has a fixed planner evaluation pack and better runtime observability, which makes future planner improvements easier to measure and debug.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/fixtures/planner_evaluation_cases.json`
- `backend/tests/test_planner_runtime_quality.py`
- `backend/tests/test_planner_bootstrap.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-19 And PI-20 Stronger Quick-Plan Timelines And Applied Option Memory

Technical Summary:
- Strengthened the quick-plan drafting prompt so itinerary previews ask for clearer day shape, thematic pacing, destination-specific anchors, route-like sequencing, and weather-aware adaptation instead of generic city-break filler.
- Added preview refinement in timeline assembly so vague arrival, departure, and check-in placeholder blocks are filtered out when provider-backed flight or hotel anchors already cover those moments.
- Added destination-suggestion filtering against rejected destination memory, plus cleaner destination-card deduping, so stale rejected places do not keep resurfacing on the board.
- Added option-memory reconciliation so newly rejected options stop lingering as active mentions, and explicitly reintroduced options are removed from rejected memory when the user brings them back into consideration.
- Added regression coverage for quick-plan prompt quality, timeline-anchor filtering, rejected-destination suggestion filtering, and reintroduced-destination memory behavior, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now produces stronger first-draft trip timelines and makes better use of planning memory.
- Quick plans are less likely to feel like generic filler because the drafting rules now push for more coherent day structure, and the timeline merge stops vague arrival/check-in placeholders from crowding out real flight or hotel anchors.
- The planner also remembers rejected destinations more usefully now: if you ruled out Prague, it should stop reappearing as a fresh suggestion, but if you later bring Prague back yourself, Wandrix can accept that change cleanly.

Files / Areas Touched:
- `backend/app/graph/planner/quick_plan.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_quick_plan_quality.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-17 And PI-18 Softer Profile Defaults And Explicit Planning-Mode Gating

Technical Summary:
- Strengthened the planner understanding prompt so saved profile context is treated as personalization and soft grounding, not as structured trip data to copy into fields by default.
- Removed the runner behavior that auto-promoted resolved location context into `from_location` during brief confirmation, which prevented saved home-base data from silently becoming a locked departure point.
- Updated assistant response framing so opening, shaping, and brief-confirmation replies can mention a saved home base as an optional starting point without presenting it as a confirmed trip fact.
- Tightened planning-mode semantics in both response selection and planner memory so Quick Plan or Advanced Planning fallback copy only appears when the mode request was actually accepted, and decision history only records planning-mode events when they were truly selected.
- Added regression coverage for soft profile-context handling, prompt guidance around explicit planning-mode semantics, ignored weak pre-confirmation quick-mode requests, and accepted explicit post-confirmation quick-mode requests, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now uses saved profile data in a much safer way. It can still use your saved home base to help the conversation along, but it no longer quietly turns that into the trip's departure airport or city unless you actually adopt it.
- The planner is also clearer about Quick Plan versus Advanced Planning. A vague `go ahead` no longer acts like a mode choice, but a clear request to build the draft still works once the trip brief is strong enough.
- Together, those changes make the planner feel more trustworthy because it is less likely to over-assume what you meant.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/location_context.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_planner_understanding.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-15 And PI-16 Earlier Shaping And Clearer Planner Framing

Technical Summary:
- Updated planner phase logic so a trip can move into `shaping_trip` once it has a destination plus usable timing, instead of waiting for every secondary requirement to be filled first.
- Added an early-draft readiness check in conversation-state handling and updated turn summaries so the planner records when it has enough signal for a useful first direction.
- Reworked assistant response framing so shaping replies now describe the working trip shape, call out provisional assumptions, and name the highest-value next confirmation.
- Tightened the decision-card response path so it carries the same early-draft momentum language when the board is leading the next choice.
- Added regression coverage for early shaping transitions, shaping-response wording, and the decision-card response branch, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now starts acting like a planner earlier in the conversation instead of over-questioning once it already has a solid destination and rough timing.
- The assistant also explains itself more clearly now: it tells you what trip shape it is currently working with, what still feels provisional, and what answer would help most next.
- That makes the experience feel less like a form and more like a confident planning partner.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-13 And PI-14 Destination Suggestion And Decision Card Discipline

Technical Summary:
- Tightened suggestion-board gating so destination shortlist cards only remain visible while the destination is still unresolved, and clear cleanly when the user switches to `own choice`.
- Reworked fallback decision cards to be more contextual around timing shape, departure choice, and trip feel, replacing the most generic placeholder-style variants.
- Added deterministic decision-card filtering in planner state so filler cards like `Next trip decisions` or placeholder option lists do not survive into the board, and added assistant response framing for decision-card mode that references the real next choice.
- Added regression tests for stale-destination-card clearing, contextual default cards, filler-card filtering, and decision-card response framing, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix is now more disciplined about when it shows destination suggestions and when it moves on.
- If the user decides to type their own destination, the shortlist clears instead of lingering visually, and once the destination is concrete the board stops acting like the trip is still in exploration mode.
- Decision cards also feel more intentional now because generic filler cards get filtered out and the defaults are tied to real trip choices instead of templated prompts.

Files / Areas Touched:
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-11 And PI-12 Traveller And Module-Scope Semantics

Technical Summary:
- Strengthened the planner understanding prompt so traveller composition is handled more carefully: explicit counts are captured normally, couples can map to a soft `adults=2` inference when clear, and family or child context without counts no longer invites invented numbers.
- Strengthened the prompt's module-scope rules so requests like `just activities`, `I already booked flights`, or `hotels later` update `selected_modules` meaningfully instead of leaving every module active by default.
- Updated the default planner follow-up copy so traveller questions ask about group makeup and children explicitly, module-scope questions ask what Wandrix should actually help with first, and the default all-modules state is now treated as unresolved scope in missing-field logic.
- Added regression tests for the new prompt guidance, default question wording, inferred module-scope narrowing, and the updated missing-field behavior, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now handles group makeup and module focus more like a real planner.
- A family trip no longer tempts the planner into inventing exact adult and child counts, and traveller follow-ups now ask in a way that naturally covers children too.
- The planner is also much better at understanding what parts of the trip you actually want help with, instead of quietly assuming it should plan every module just because the app can.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/details_collection.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_bootstrap.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-09 And PI-10 Tentative Origin And Budget Nuance

Technical Summary:
- Strengthened the planner understanding prompt so tentative origin phrasing can stay provisional, allowing one inferred working origin while preserving fallback or comparison origins in `mentioned_options` instead of collapsing them into a hard route.
- Strengthened the prompt's budget rules so mixed signals like `not too expensive`, `keep hotels sensible`, and `happy to splurge on food` are treated as nuanced posture hints rather than direct keyword-to-label mappings.
- Updated the default planner follow-up copy so origin questions ask for the user's most likely departure point and budget questions ask about tradeoffs and splurge-vs-sensible choices more naturally.
- Added regression tests for the new prompt guidance plus the updated open-question wording, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now handles soft origin language and nuanced budget language more like a real planner.
- If someone says they would probably leave from London but Manchester could work too, the planner is now guided to keep that route provisional instead of treating it like a fully locked departure point.
- Budget follow-ups also sound more natural now and are better at capturing mixed tradeoffs instead of forcing a blunt label too early.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_planner_understanding.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-08 Rough Timing Preservation And Re-Verified PI-07

Technical Summary:
- Strengthened the planner understanding prompt with explicit rough-timing rules and examples so phrases like `early October`, `around Easter`, `sometime in spring`, `long weekend`, and `five-ish days` are kept in `travel_window` and `trip_length` unless the user gave fixed dates.
- Added timing-aware merge normalization in `draft_merge.py` so inferred exact dates no longer override rough timing, confirmed rough timing clears stale exact dates, and confirmed exact dates clear stale rough timing.
- Added dedicated backend regression coverage for rough-timing merge behavior plus prompt-level coverage for the updated understanding rules, which also re-verified the PI-07 ambiguity-preservation contract.
- Re-ran the full backend suite successfully after the timing changes landed.

Plain-English Summary:
- Wandrix now handles fuzzy timing much more safely.
- If a user says something like `early October for five-ish days`, the planner keeps that broad timing instead of silently inventing exact dates.
- The timing state also cleans itself up better now when a trip moves from rough timing to exact dates, or back from exact dates to rough timing.

Files / Areas Touched:
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/understanding.py`
- `backend/tests/test_planner_timing_merge.py`
- `backend/tests/test_planner_understanding.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-06 And PI-07 Question Ranking And Ambiguity Preservation

Technical Summary:
- Added structured planner question updates with `field`, `step`, `priority`, and `why`, then extended persisted `ConversationQuestion` state to store that metadata instead of relying on loose question strings alone.
- Reworked open-question merging so Wandrix now ranks questions deterministically, dedupes them by field and planning step, normalizes early timing asks toward `travel_window` and `trip_length`, and marks no-longer-relevant questions as `answered`.
- Strengthened the planner understanding prompt with explicit ambiguity-preservation rules and examples covering broad destination asks, tentative origin language, rough timing, and uncertain traveller counts.
- Added backend regression tests for question ranking, answered-question lifecycle, and prompt content, then re-ran the full backend suite successfully.

Plain-English Summary:
- Wandrix now asks better follow-up questions in a better order.
- Instead of piling up random prompts, it keeps structured question objects and pushes the highest-value next question to the top, like asking for the destination before drilling into exact timing details.
- The planner prompt is also now much more explicit about staying broad when the user is broad, which makes it less likely to overcommit too early.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `backend/tests/test_planner_understanding.py`
- `frontend/src/types/trip-conversation.ts`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Completed PI-02 Source-Semantics Verification

Technical Summary:
- Re-ran the current `PI-02` per-field source semantics verification suite against the existing planner patch with targeted backend planner tests, backend compile checks, frontend production build, and frontend lint.
- Confirmed `backend/tests/test_planner_bootstrap.py` and `backend/tests/test_planner_merge_semantics.py` still pass, `backend/app` compiles cleanly, `frontend` builds successfully, and lint now runs cleanly apart from one existing `@next/next/no-img-element` warning in `frontend/src/components/package/trip-suggestion-board.tsx`.
- Used Playwright MCP against the existing signed-in `/chat` session to verify that the planner-source change remains stable while the live chat shell is still blocked separately: the board stays on `Loading your planning board.`, the composer remains disabled, and triggering `New Trip` produced no non-static network requests.
- Updated the planner boundary tracker to record the third `testing done once` pass for `PI-02` and moved the tracker status from `reviewing` to `done`.

Plain-English Summary:
- The source-tracking planner improvement has now been checked three times and is complete in the tracker.
- The core planner logic still behaves correctly and the app continues to build, lint, and pass its targeted tests.
- The only thing still visibly broken in live chat is the existing board-loading shell issue, which appears separate from the `PI-02` planner change itself.

Files / Areas Touched:
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Added Structured Planner Field Source Semantics

Technical Summary:
- Added a structured `field_sources` contract to the planner turn schema so the LLM can explicitly mark whether a touched field came from direct user intent, softer inference, profile context, or assistant-derived reasoning.
- Extended planner field-memory merges to persist those source semantics, treat board-confirmed facts as a first-class `board_action` source, and still count board-originated values as confirmed state for downstream status and response-building logic.
- Added backend regression coverage for profile-default and assistant-derived source paths plus board-confirmation source handling, and updated the planner boundary tracker to mark `PI-02` as implemented and under review.
- Updated the shared frontend trip-conversation type contract so persisted field memory can safely represent the new `board_action` source.

Plain-English Summary:
- The planner can now tell the difference between a fact the user typed, something it is inferring, a saved profile default, and a value the user confirmed on the board.
- That makes the trip state more trustworthy because the app no longer has to pretend every confirmed detail came from chat text.
- This gives us a cleaner foundation for later clarification, correction, and profile-context work without slipping into brittle heuristics.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/types/trip-conversation.ts`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Finished PI-04 And PI-05 Correction And Confirmation Semantics

Technical Summary:
- Added explicit corrected-field detection in the planner merge path so confirmed field changes are now recognized as structured corrections rather than only appearing as rejected-option fallout.
- Recorded first-class `Trip details corrected` decision-history events with before-and-after descriptions, which gives the planner an explicit history of user corrections instead of relying only on inferred side effects.
- Updated trip-brief confirmation resolution so a later confirmed correction invalidates earlier `Trip details confirmed` history until the user confirms the revised brief again.
- Routed the suggestion-board and assistant response layers through the same resolved `brief_confirmed` value from the runner, preventing them from treating stale historical confirmation as current truth after a correction.
- Added targeted regression coverage for correction-triggered reconfirmation behavior and re-ran the full backend test suite successfully.

Plain-English Summary:
- Wandrix now handles "actually, change this" moments much more cleanly.
- If a user corrects a confirmed trip detail, the planner now treats that as a real correction event and stops pretending the old confirmation still applies.
- That means the board and assistant are less likely to push the user forward as if the brief were still locked when it really needs a fresh confirmation.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Verified PI-03 Explicit Vs Inferred Merge Protection

Technical Summary:
- Verified that planner field-memory merge precedence now keeps stronger explicit provenance attached to stable trip facts when later turns only mention alternatives or softer inferred possibilities.
- Confirmed through the targeted planner merge suite that a later inferred turn does not silently downgrade a previously explicit confirmed field and that explicit corrections still replace earlier inferred values cleanly.
- Re-ran the full backend test suite after the PI-01 follow-up changes to ensure the explicit-vs-inferred protections remain intact in the current planner codebase.
- Marked PI-03 as done in the planner intelligence tracker with an updated progress note reflecting the verification pass.

Plain-English Summary:
- The planner now reliably keeps clearly confirmed facts feeling confirmed, even if a later message brings up another option more casually.
- That means Wandrix is less likely to quietly weaken a destination or route that the user had already made clear.
- I treated this as a verification-and-closeout step rather than adding duplicate code, because the protection is already present and passing tests.

Files / Areas Touched:
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-21 - Hydrated Legacy Planner Confidence Memory And Verified PI-01 Live

Technical Summary:
- Added runner-side hydration that rebuilds `conversation.memory.field_memory` from legacy `status.confirmed_fields` and `status.inferred_fields` when older persisted drafts do not yet carry structured field memory.
- Hydrated legacy confirmed fields as high-confidence explicit memory entries and legacy inferred fields as medium-confidence inferred entries so older trips continue to participate in the newer field-confidence model on the next turn.
- Updated stale backend tests to the current runner-based planner flow and added direct regression coverage that legacy confirmed and inferred fields hydrate back into structured planner memory on the next processed turn.
- Installed `pytest` in the local backend virtual environment to restore backend verification, then validated the change with targeted planner tests, the full backend test suite, and a live smoke test through the existing signed-in chat session on the `DevTools Snapshot Proof Trip`.

Plain-English Summary:
- Older trips no longer lose planner certainty data just because they were saved before the newer confidence memory existed.
- When the planner revisits an existing trip, it now rebuilds that memory and keeps working with explicit vs inferred facts safely.
- In the live app test, a fuzzy message about flying from London versus Manchester kept London as the working departure point, stored a medium confidence level for it, and remembered Manchester as an alternative instead of switching too aggressively.

Files / Areas Touched:
- `backend/app/graph/planner/runner.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_trip_draft_schema.py`
- `backend/tests/test_trip_service.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-20 - Added Structured Planner Field Confidence

Technical Summary:
- Added a structured `field_confidences` contract to the planner turn schema so the LLM can attach low, medium, or high confidence to each touched trip field instead of relying on source-based fallback scoring.
- Updated planner conversation memory to persist `confidence_level` per field, keep the strongest same-value confidence across later turns, and stop writing new fake-precision numeric confidence defaults.
- Extended board-confirmation merge behavior so structured board-confirmed facts also land with high confidence, added targeted backend regression coverage for both LLM and board-action paths, and marked PI-01 as in progress in the planner boundary tracker.
- Updated the frontend trip-conversation types to match the new persisted confidence contract.

Plain-English Summary:
- The planner is now more honest about uncertainty at the field level.
- Instead of quietly pretending inferred facts have precise confidence scores, it stores clear low, medium, or high confidence signals for each trip detail the model touched.
- This gives Wandrix a safer foundation for later clarification and board-behavior improvements without slipping back into brittle heuristics.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/tests/test_planner_merge_semantics.py`
- `frontend/src/types/trip-conversation.ts`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-20 - Protected Explicit Planner Facts From Inference Downgrades

Technical Summary:
- Tightened planner field-memory merge precedence so a later inferred turn can no longer silently downgrade a previously explicit fact when the persisted trip value itself has not changed.
- Added deterministic source-priority helpers in the planner conversation state merge path to keep stronger explicit field provenance attached to stable trip facts while still allowing explicit corrections to replace older inferred values.
- Added targeted backend regression coverage for both the downgrade case and the explicit-correction case, and marked PI-03 as in progress in the planner boundary tracker with a concrete status note.

Plain-English Summary:
- The planner now keeps clearly confirmed trip details feeling confirmed, even if a later message mentions alternatives or uncertainty around the same area.
- This makes the live trip state more trustworthy because a firm choice like a destination will not quietly become "just inferred" again unless the user really changes it.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/tests/test_planner_merge_semantics.py`
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-20 - Expanded Planner Intelligence Guide With Granular Tracker

Technical Summary:
- Expanded the planner intelligence boundary guide from a high-level rulebook into a granular implementation tracker with individual planner-intelligence change IDs.
- Added a tracker table covering priority, status, target files, why each change matters, and the safe implementation shape for twenty-five distinct planner-intelligence tasks.
- Added detailed per-change notes explaining exactly what each planner task is, why it matters, what the implementation should do, what it must not do, and before-and-after examples to reduce design mistakes during execution.
- Kept the guidance aligned with the repo rule that planner understanding remains LLM-first while deterministic logic is limited to validation, merge semantics, gating, and persistence.

Plain-English Summary:
- The planner intelligence doc is now much more practical and much harder to misunderstand.
- Instead of broad advice, it now breaks the work into small tracked changes and explains each one clearly with examples of good and bad behavior.
- This should make it much easier to improve the planner carefully without slipping back into brittle keyword or rule-based logic.

Files / Areas Touched:
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-20 - Documented Planner Intelligence Boundaries And Anti-Heuristic Rules

Technical Summary:
- Added a dedicated planner intelligence boundary document that defines the repo-safe split between LLM-first planner understanding and deterministic application logic.
- Documented which planner changes are safe, which are unsafe, which gray zones need careful review, and how the boundary should be enforced in implementation and code review.
- Included detailed Wandrix-specific before-and-after examples showing how broad asks, rough timing, corrections, profile defaults, confirmation language, provider triggering, and board actions should behave.
- Added a practical review checklist and safe backlog guidance so future planner work can improve intelligence without drifting back into regex, keyword, or heuristic extraction.

Plain-English Summary:
- The repo now has a clear written rulebook for making the planner smarter without turning it into a brittle keyword parser.
- This explains what kinds of intelligence upgrades are good, what kinds would be a mistake, and shows concrete examples so the boundary is easy to understand.
- It should make future planner work much safer and more consistent.

Files / Areas Touched:
- `docs/planner-intelligence-boundaries.md`
- `CHANGELOG.md`

## 2026-04-20 - Restricted Saved Trips To Finalized Brochures Only

## 2026-04-20 - Refined Hotel Cards In The Reference And Live Board Views

Technical Summary:
- Added a dedicated hotel reference card component so the hotel module workspace no longer renders flat text rows inline inside the already-large module workspace file.
- Updated the hotel module surface to show a clearer stay window, address extraction, highlights, and source CTA when a provider link is available.
- Refined the live board hotel summary so it mirrors the stay-focused structure more cleanly instead of showing only a generic gradient block and the first raw note.
- Kept the hotel presentation grounded in the existing theme tokens and premium travel-product style without reintroducing generic dashboard card styling.

Plain-English Summary:
- Hotel results now look much more like real stay options and much less like raw backend data.
- The hotels page is easier to scan, and the live board gives a cleaner snapshot of the current stay direction.
- This makes the new Xotelo-backed hotel results feel like part of the product instead of a temporary data dump.

Files / Areas Touched:
- `frontend/src/components/hotels/hotel-reference-card.tsx`
- `frontend/src/components/modules/trip-module-workspace.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Added Xotelo Hotel Search With RapidAPI Usage Tracking

Technical Summary:
- Added RapidAPI-backed hotel configuration and a shared RapidAPI client so hotel discovery can be routed through app-owned adapters rather than provider payloads leaking into the planner.
- Introduced a new hotel provider service that uses Xotelo cached hotel search as the active destination-based hotel source, with a structured LLM fallback when cached provider results are unavailable.
- Wired planner module enrichment to populate hotel outputs from the new provider chain instead of leaving the hotel layer unchanged.
- Added app-owned provider usage metrics persistence, usage summary schemas and routes, and a new authenticated `/providers` frontend page to track monthly request budgets and last-known provider health.
- Extended provider status reporting to include Xotelo plus the additional RapidAPI hotel/reference providers that are configured for future property-level expansion.
- Validated the new flow with real Xotelo hotel searches, planner enrichment, usage counter increments, route-level provider endpoint checks, and frontend build/lint verification.

Plain-English Summary:
- Wandrix can now pull real cached hotel options through Xotelo instead of leaving hotels as an empty placeholder layer.
- If cached hotel results are thin, the planner can still fall back to clearly-labeled AI hotel suggestions so the trip keeps moving.
- There is now an in-product provider usage page so you can track how much of the RapidAPI hotel quota the app is using.

Files / Areas Touched:
- `backend/app/core/config.py`
- `backend/app/integrations/rapidapi/client.py`
- `backend/app/models/provider_usage_metric.py`
- `backend/app/repositories/provider_usage_repository.py`
- `backend/app/schemas/provider_usage.py`
- `backend/app/services/provider_status_service.py`
- `backend/app/services/provider_usage_service.py`
- `backend/app/services/providers/hotels.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/api/routes/providers.py`
- `backend/alembic/versions/3c9d8e7f6a5b_add_provider_usage_metrics.py`
- `frontend/src/app/providers/page.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/modules/trip-module-workspace.tsx`
- `frontend/src/components/providers/provider-usage-page.tsx`
- `frontend/src/lib/api/providers.ts`
- `frontend/src/types/provider-usage.ts`
- `CHANGELOG.md`

## 2026-04-20 - Added Travelpayouts Cached Flight Fallback

Technical Summary:
- Added Travelpayouts configuration support to backend settings so Wandrix can use the repo `.env` token and base URL for cached Aviasales flight data.
- Introduced a dedicated Travelpayouts integration client and a lightweight city/IATA lookup helper so flight fallback does not depend entirely on Amadeus location lookup succeeding.
- Updated the flight provider layer to try Amadeus first, then fall back to Travelpayouts cached Aviasales offers when live search is unavailable or returns nothing useful.
- Broadened the Travelpayouts request strategy to try exact-date cache lookups first and then month-level cache lookups, which works better for sparse cached availability.
- Wired planner flight enrichment to use the shared fallback entry point instead of the Amadeus-only path and validated the flow with a live London-to-Barcelona smoke test.

Plain-English Summary:
- Wandrix can now show cached Aviasales flight options through Travelpayouts when Amadeus is unreliable.
- This fits the current product direction well because cached flight results are enough for planning and comparison without needing fully live booking inventory.
- Flights are now much less likely to disappear just because one provider is unstable.

Files / Areas Touched:
- `backend/app/core/config.py`
- `backend/app/integrations/travelpayouts/client.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/services/providers/flights.py`
- `backend/app/services/providers/iata_lookup.py`
- `CHANGELOG.md`

Technical Summary:
- Updated the Saved Trips library so it now filters to `brochure_ready` trips only instead of mixing in in-progress and review-state planning sessions.
- Removed the old trip-stage filter controls (`All trips`, `In progress`, `Ready for review`, `Brochure-ready`) and simplified the page into a brochure-only search surface.
- Adjusted the trip cards and page copy so the shelf now speaks in terms of finalized brochure versions, PDF downloads, and history rather than active planning phases.

Plain-English Summary:
- The Saved Trips page now only shows trips that were actually finalized and turned into brochures.
- Unfinished trips no longer appear there, and the page now behaves like a clean brochure archive instead of a mixed planning inbox.

Files / Areas Touched:
- `frontend/src/components/trips/trip-library.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Added Immutable Brochure Snapshots And Editorial PDF Flow

Technical Summary:
- Added a new `brochure_snapshots` persistence layer with versioned immutable brochure records, plus an Alembic migration to create the owned table in Supabase Postgres.
- Wired the conversation finalization path so confirming a trip now creates a brochure snapshot automatically, reopening leaves earlier versions untouched, and re-finalizing creates the next version.
- Added backend brochure services and routes for listing brochure history, loading the latest brochure, loading a specific brochure version, and rendering a server-side PDF with Playwright/Chromium.
- Extended trip list contracts with brochure snapshot metadata so Saved Trips can show brochure version actions without extra guessing.
- Replaced the old live-draft brochure page with an editorial snapshot-based brochure experience that includes a hero cover, version history rail, structured warnings, itinerary sections, and PDF download.
- Updated Saved Trips to expose `Open brochure`, `Download PDF`, and `View history` for brochure-ready trips.
- Installed Playwright, downloaded Chromium for server-side PDF rendering, and validated the full finalize -> reopen -> re-finalize path against the real database flow.

Plain-English Summary:
- Wandrix brochures are now saved as permanent versions when a trip is finalized instead of changing whenever the live trip draft changes.
- Users can reopen a trip, make changes, and save a brand-new brochure version later without losing the older brochure they already finalized.
- The brochure page now looks and behaves more like a polished travel document, and users can download the same saved brochure as a PDF.

Files / Areas Touched:
- `backend/app/models/brochure_snapshot.py`
- `backend/app/repositories/brochure_snapshot_repository.py`
- `backend/app/services/brochure_service.py`
- `backend/app/services/conversation_service.py`
- `backend/app/services/trip_service.py`
- `backend/app/schemas/brochure.py`
- `backend/app/schemas/trip.py`
- `backend/app/api/routes/brochures.py`
- `backend/app/api/router.py`
- `backend/app/utils/destination_images.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/2b7e8a9c4d1f_add_brochure_snapshots.py`
- `backend/requirements.txt`
- `frontend/src/types/brochure.ts`
- `frontend/src/types/trip.ts`
- `frontend/src/lib/api/brochures.ts`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/lib/recent-trips-cache.ts`
- `frontend/src/app/brochure/[tripId]/page.tsx`
- `docs/architecture.md`
- `docs/decision-log.md`
- `README.md`
- `CHANGELOG.md`

## 2026-04-20 - Fixed Board-Only Finalize Memory Crash

Technical Summary:
- Fixed the planner conversation-memory merge path so board-only actions no longer try to write an empty `user_message` into `ConversationTurnSummary`.
- Added a board-action summary fallback in `conversation_state.py`, which lets finalize/reopen actions record a valid memory entry even when no free-text user message was sent.
- Re-ran backend compile checks and a direct finalize-trip service call to confirm the quick-plan confirmation flow now reaches the finalized state successfully.

Plain-English Summary:
- The `Confirm plan` button was crashing because the backend expected a typed user message, even though this action came from the board.
- Wandrix now records a proper board-action summary instead, so confirming a plan from the right-side board works normally.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `CHANGELOG.md`

## 2026-04-20 - Added Quick Plan Finalize And Reopen Flow

Technical Summary:
- Added a real quick-draft confirmation lifecycle to the planner state with `confirmation_status`, `finalized_at`, and `finalized_via` on both conversation and trip-draft status models.
- Extended planner phases with `finalized` and updated the backend phase/status builders so brochure readiness is now derived from finalized state instead of generic review state.
- Extended the structured LLM turn schema with `planner_intent` so chat can interpret `confirm_plan` and `reopen_plan` without regex or keyword parsing.
- Added explicit board action types for `finalize_quick_plan` and `reopen_plan`, and mapped them into the same backend confirmation transition path as chat.
- Updated the planner runner so finalized trips behave like a soft lock: the saved quick plan stays frozen until the user explicitly reopens planning.
- Added assistant copy for the pre-confirm quick-draft prompt, the post-confirm success state, the reopen confirmation, and the “plan is still locked” response when someone tries to edit a finalized trip without reopening it.
- Changed the board-action runtime so finalize and reopen actions are submitted as real board actions to the backend instead of synthetic free-text user messages.
- Added the live-board confirm CTA, confirmation dialog, and reopen CTA on the quick-plan itinerary surface.
- Updated starter/mock trip-draft data and sandbox data so the new finalized-state fields are represented consistently across the app.

Plain-English Summary:
- Users can now lock a quick trip plan from either chat or the right-side board.
- Once the plan is confirmed, Wandrix treats it as finalized, saves it as brochure-ready, and points the user to Saved Trips as the place to open or download it later.
- If the user wants to change the plan afterwards, they can reopen planning and keep editing instead of starting over.
- The board button now behaves like a real planner action rather than pretending the user typed a confirmation message.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/trip_draft.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/runner.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/app/layout.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Summary Stats To Match Trip Details Board Styling

Technical Summary:
- Redesigned the summary stats section to match the exact styling pattern of the trip details board.
- Converted each stat into its own card using `border-[var(--planner-board-border)]` and `bg-white`.
- Changed layout from horizontal flex to vertical stack with icon on top.
- Updated icon container to `size-10` with `rounded-full` and `bg-[var(--planner-board-cta)]/8`.
- Icon color uses `text-[var(--planner-board-cta)]` for consistency.
- Card padding standardized to `p-4` matching traveller cards.
- Label uses `text-[var(--planner-board-muted)]` token.
- Value text uses `text-[var(--planner-board-text)]` token with `font-medium`.
- Grid gap set to `gap-4` for consistent card spacing.
- All styling now uses planner board design tokens instead of generic theme tokens.

Plain-English Summary:
- The summary stats section (Route, Timing, Party, Planning mode) now matches the exact look and feel of the trip details board.
- Each stat is in its own white card with consistent borders and spacing.
- Icons are positioned at the top with the accent color, matching the traveller count cards.
- The section now feels cohesive with the rest of the planning interface.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Improved Trip Live Board Spacing And Visual Breathing Room

Technical Summary:
- Increased padding and margins throughout the trip live board to reduce visual density.
- Updated container padding from px-4 py-6 to px-6 py-8 (xl: px-8).
- Increased section spacing from space-y-10 to space-y-12 and subsection spacing from space-y-6 to space-y-8.
- Expanded gaps in grid layouts from gap-6 to gap-8 and summary stat grids from gap-4 to gap-5.
- Increased timeline section padding from px-6 py-5 to px-7 py-6 and timeline item spacing from space-y-4 to space-y-5.
- Adjusted timeline rail positioning and item gaps for better visual hierarchy.
- Increased InfoCard padding from px-5 py-5 to px-6 py-6 and improved internal spacing.
- Enhanced text line-height from leading-6 to leading-relaxed throughout for better readability.
- Improved BoardHero spacing with larger gaps and more generous padding.
- Adjusted tab button padding from px-4 py-2 to px-5 py-2.5.
- Increased filter badge padding and gaps in FilterStack component.

Plain-English Summary:
- The trip live board now has much better breathing room and feels less cramped.
- All sections, cards, and timeline items have more space between them.
- Text is easier to read with improved line spacing.
- The overall layout feels more premium and less cluttered.
- Cards and sections have more generous padding making content easier to scan.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Restored The Richer Live Trip Board Layout For Quick Plan

Technical Summary:
- Reworked the Quick Plan live board so it uses the stronger previously designed board composition instead of the flatter interim layout.
- Restored the richer structure inside the current board shell, including the destination hero, itinerary versus selections tabs, timeline rail treatment, and the right-side flight, weather, hotel, and highlights cards.
- Kept the current planner runtime intact by mapping the restored board to the existing persisted trip draft, conversation summary, module outputs, and Quick Plan state rather than reviving old placeholder behavior.

Plain-English Summary:
- The main itinerary board on the right now looks and feels like the stronger earlier design again.
- Instead of a plain list, it is back to being a more polished travel board with a destination image, clearer itinerary flow, and a better side panel for flights, weather, stay details, and highlights.
- This only changes the board presentation. The current chat planning flow and saved trip data still work underneath it.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Itinerary Section With Cleaner Cards And Better Visual Flow

Technical Summary:
- Redesigned timeline day sections to use individual white cards with planner board borders instead of nested container layout.
- Split day header into its own card separate from timeline items for better visual separation.
- Converted timeline items to individual bordered cards with hover effects (`hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)]`).
- Repositioned time display to the left with fixed width (`min-w-[4.5rem]`) and right-aligned tabular numbers.
- Increased icon container size from `h-8 w-8` to `h-9 w-9` with `bg-[color:var(--accent)]/8` background.
- Updated timeline rail to use gradient (`from-[color:var(--accent)]/20 via-[color:var(--accent)]/10 to-transparent`) instead of solid border.
- Enhanced timeline markers: lead marker now `h-7 w-7` with stronger shadow, non-lead markers use `bg-[color:var(--accent)]/30`.
- Added bullet points to detail lists with small circular markers (`h-1 w-1 rounded-full`).
- Improved spacing: day sections use `space-y-4`, items use `space-y-3` for tighter grouping.
- All cards now use consistent `border-[var(--planner-board-border)]` and `bg-white` matching trip details board.

Plain-English Summary:
- The itinerary timeline now looks much cleaner and more modern.
- Each day and each activity is in its own white card, making it easier to scan.
- The timeline rail has a subtle gradient fade effect instead of a plain line.
- Times are positioned on the left with better alignment, and icons are slightly larger.
- Cards have a subtle hover effect to show interactivity.
- The overall design now matches the rest of the planning interface perfectly.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Simplified The Live Board And Relaxed The Top Summary Strip

Technical Summary:
- Removed the `Selections` tab and its supporting tab-switching logic from the live Quick Plan board so the right side stays focused on one primary itinerary view.
- Replaced the cramped four-up summary strip with a calmer two-column summary block that uses the existing board theme, shell borders, and background tokens instead of the off-theme white card treatment.
- Moved the most useful non-itinerary context into the right-side `Planner notes` card so the board still keeps key refinement signals without needing a second tab.

Plain-English Summary:
- The live trip board is now simpler and more focused.
- There is no extra `Selections` tab anymore, and the top summary section feels less cramped and more in line with the rest of the board design.
- The useful trip notes are still there, but they now live in the side panel instead of forcing a second view.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Split The Route Summary And Removed Planning Mode From The Top Strip

Technical Summary:
- Updated the live board summary strip so route information is shown as separate `From` and `To` cards instead of one cramped combined route card.
- Removed the `Planning mode` card from the top summary area entirely to free space and let the remaining trip facts breathe.
- Kept the same board shell and summary-card styling while improving information density and scanability.

Plain-English Summary:
- The top of the live board is easier to read now.
- Instead of squeezing the full route into one box, it now shows where the trip starts and where it goes as separate items.
- I also removed the planning-mode box from that row so the layout feels less cramped.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Removed The Mini Card Containers From The Live Board Summary Strip

Technical Summary:
- Simplified the top summary section of the live trip board by removing the individual stat-card containers around `From`, `To`, `Timing`, and `Party`.
- Kept the outer board section intact while changing the inner summary layout to a cleaner four-column strip with spacing instead of nested boxes.

Plain-English Summary:
- The trip facts at the top of the board now feel lighter and less cramped.
- Instead of looking like four separate small cards inside another card, they now sit together as one cleaner summary strip.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Stacked The Live Board Summary Facts Vertically And Removed The Outer Wrapper

Technical Summary:
- Reworked the live board summary facts so `From`, `To`, `Timing`, and `Party` now render as a vertical stacked list rather than a horizontal strip.
- Removed the extra outer summary container around that section and used subtle row dividers instead, reducing visual nesting at the top of the itinerary column.

Plain-English Summary:
- The trip facts at the top of the board are now stacked vertically.
- I also removed the extra surrounding box, so that area feels cleaner and less crowded.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Removed Duplicate Hero Facts And Dropped The Brochure Button From The Live Board

Technical Summary:
- Trimmed the lower live-board fact stack so it now only shows `From` and `To`, removing duplicated `Timing` and `Party` information that was already present in the hero section.
- Removed the `Brochure` call-to-action from the live board hero to keep the top area quieter and more focused on the trip itself.

Plain-English Summary:
- The board was repeating the travel window and traveller count in two places, so I removed the duplicate copies from the lower section.
- I also removed the `Brochure` button from the top of the board to make the hero feel cleaner.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Removed Planner Notes And Tightened Quick Plan Timing Detail

Technical Summary:
- Removed the `Planner notes` sidebar card from the live trip board and cleaned up the now-unused supporting UI helpers.
- Extended the Quick Plan structured timeline model so proposed itinerary items can carry `start_at` and `end_at` values.
- Tightened the Quick Plan drafting prompt to demand more concrete destination-specific itinerary blocks, explicit travel-time context, and real timed flight blocks when provider data exists.
- Updated timeline merging so provider-backed flight and hotel items are preserved alongside the LLM draft instead of getting dropped when a quick-plan preview exists.
- Updated the flight card UI to display departure and arrival times whenever live flight data is available.

Plain-English Summary:
- The extra `Planner notes` panel is gone from the board.
- I also made the planner aim for more specific itinerary blocks and better travel-time detail, especially around flights.
- When the flight provider returns real timings, the board can now show them more clearly instead of only showing airport codes.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/quick_plan.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `CHANGELOG.md`

## 2026-04-20 - Restored Modules As A Required Details-Board Step

Technical Summary:
- Reverted the brief experiment that treated the modules section as an optional final refinement in the trip-details board model.
- Restored the original required-step behavior so modules appear first again, remain part of the required confirmation path, and budget returns to requiring both posture and amount when that step is active.

Plain-English Summary:
- The modules section is no longer optional in the board flow.
- It is back to being a required part of the trip brief, which matches the intended product behavior.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-model.ts`
- `CHANGELOG.md`

## 2026-04-20 - Fixed Details-Board Confirmation Rules And Made Modules Truly Optional

Technical Summary:
- Updated the trip-details board model so the visible flow starts with core trip fields and keeps `modules` as an optional final step instead of a first required gate.
- Adjusted confirmation rules so the board now requires at least one active module plus only the module-dependent required steps, rather than always treating the modules step itself as a blocker.
- Relaxed budget completion so budget posture or a positive budget amount can satisfy the budget step when that step is required.
- Restored the details-board form defaults so traveller counts normalize to `1` adult and `0` children even when persisted state contains nulls.

Plain-English Summary:
- The board was still blocking confirmation in cases where the form looked complete, especially after narrowing the trip to only a few modules.
- Modules now behave like a real optional refinement: the trip can confirm with the default full scope, and changing modules no longer feels like a separate required hurdle.
- I also made the budget step less brittle, so it matches the UI better and doesn’t quietly demand more than the board suggests.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Added Quick Plan Mode After Trip Brief Confirmation

Technical Summary:
- Added persisted planning-mode state to the live planner conversation model with `planning_mode` and `planning_mode_status`, plus new board actions for `select_quick_plan` and `select_advanced_plan`.
- Changed the planner runtime so confirming trip details no longer jumps straight into enrichment. It now moves into a dedicated post-confirmation `planning_mode_choice` board state.
- Implemented Quick Plan runtime handling in the active planner runner: Quick Plan starts module enrichment and timeline generation immediately, while Advanced Planning requests now fall back to Quick Plan with explicit status tracking.
- Updated the LLM structured turn contract so it can request quick or advanced planning in chat and generate fuller first-pass itinerary timelines once planning begins.
- Added a real planning-mode choice UI on the right board with an active Quick Plan card and a disabled Advanced Planning card marked in development.
- Replaced the old helper-only post-confirmation board behavior with a true live itinerary board once Quick Plan is active, using persisted timeline and module-output data already saved in the trip draft.
- Kept the planner honest by relying on structured LLM output and provider enrichment only, without reintroducing deterministic trip parsing or fake placeholder module data.

Plain-English Summary:
- After the user confirms the trip basics, Wandrix now stops and asks one clean question: do you want a Quick Plan now, or a more advanced planning flow later.
- Quick Plan works today and immediately builds a first draft itinerary that appears on the live board.
- Advanced Planning is visible so the product direction is clear, but it is intentionally disabled and marked as still in development.
- If the user asks for Advanced Planning in chat anyway, Wandrix now handles that gracefully, explains that it is not ready yet, switches to Quick Plan, and still generates the itinerary instead of getting stuck.
- The right side no longer falls back to vague helper text after confirmation. It now becomes a real itinerary board once planning starts.

Files / Areas Touched:
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/runner.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Made Quick Plan Itineraries More Specific And Put Them Back In The Main Board Shell

Technical Summary:
- Added a dedicated Quick Plan itinerary drafting pass in the backend so Wandrix can generate a concrete first-pass itinerary from the confirmed brief and any provider-backed module outputs instead of relying only on a broad generic timeline preview.
- Updated the Quick Plan drafting prompt to prefer named neighborhoods, landmarks, markets, and destination-specific pacing while staying honest when flight or hotel provider data is missing.
- Adjusted timeline assembly so Quick Plan can use its richer generated itinerary blocks directly instead of always mixing them with the generic derived timeline.
- Moved the live itinerary rendering back under the main `TripBoardPreview` shell so the quick-plan board uses the same primary board container instead of feeling like a separate board mode.

Plain-English Summary:
- Quick Plan should now feel less vague. Wandrix has a new itinerary-writing step that aims to produce more specific trip blocks instead of generic suggestions.
- The live itinerary also sits back inside the main board layout, so it feels like the same travel board continuing into the itinerary stage rather than a completely different panel taking over.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/quick_plan.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/runner.py`
- `frontend/src/components/package/trip-live-board.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Tightened Quick Plan Coverage And Summary Quality

Technical Summary:
- Extended the dedicated Quick Plan itinerary schema to allow a longer board summary when needed.
- Refined the Quick Plan drafting prompt so it explicitly covers the full trip span and avoids cutting the itinerary short before the final day.
- Added a stricter summary rule so the board summary comes back as one clean complete sentence instead of an awkward clipped fragment.

Plain-English Summary:
- Quick Plan should now do a better job of covering the whole trip instead of stopping too early.
- The short summary at the top of the board should also read more naturally instead of ending abruptly.

Files / Areas Touched:
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/quick_plan.py`
- `CHANGELOG.md`

## 2026-04-20 - Smoothed The Advanced-Planning Fallback Label On The Live Board

Technical Summary:
- Adjusted the live board planning-mode badge so it always displays `Quick Plan` even when the user asked for Advanced Planning and Wandrix had to fall back.
- Kept the fallback explanation in the live board summary line instead of splitting that nuance across both the badge and the summary.

Plain-English Summary:
- When someone asks for Advanced Planning before it exists, the trip board now stays calmer and clearer.
- Wandrix still explains that it fell back to Quick Plan, but the mode label itself no longer changes into awkward wording like `Quick Plan fallback`.

Files / Areas Touched:
- `frontend/src/components/package/trip-live-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Made Details Collection Module-First And More Human

Technical Summary:
- Replaced the old details-stage `Known` / `Still needed` contract with grouped `have_details` and `need_details` sections in the planner conversation schema.
- Added a shared backend details-collection helper to drive active modules, visible steps, required steps, and scope-aware missing fields from one place.
- Reworked the details board into a module-first adaptive stepper so the form changes by scope: full-trip, flights-only, hotels-only, activities-only, or weather-only.
- Updated the planner response builder so the assistant now says `Here's what I have so far` and `To move this forward, I still need` instead of robotic status tags.
- Tightened planner confirmation handling so `confirm_trip_details` is the primary structured board commit path and older trip-brief confirmation logic is no longer used by the main route-to-details flow.
- Updated starter data, sandbox mocks, and board contracts to the new `have_details` / `need_details` / `visible_steps` / `required_steps` shape.
- Live-tested the refreshed flow in the existing Chrome session, including the default route-to-details handoff and an `activities`-only module narrowing pass.

Plain-English Summary:
- Once Wandrix knows the route, it now asks for the remaining details in a much more natural way.
- The assistant now tells you what it already has and what it still needs, instead of showing awkward `Known` tags in the chat.
- The board now starts with module selection first, so it can adapt to what the user actually wants planned.
- If the user only wants something like activities, the board immediately becomes lighter and stops pushing unrelated flight-heavy fields.
- The whole route-to-details handoff now feels more like a real travel planner and less like a generic checklist form.

Files / Areas Touched:
- `backend/app/graph/planner/details_collection.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/schemas/trip_conversation.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-20 - Added Review-And-Confirm Behavior For Fully-Specified Prompts

Technical Summary:
- Updated the details-collection board state so if all required fields are already present, the board switches from a fill-in prompt to a review-and-confirm surface with prefilled values.
- Changed the assistant details-stage response so it stops asking for more details when nothing is missing and instead tells the user to confirm in chat or edit on the board before Wandrix proceeds.

Plain-English Summary:
- If a user gives Wandrix the full trip brief in one message, it will no longer keep asking for extra details unnecessarily.
- Instead, Wandrix now shows the prefilled board for review and asks the user to either confirm in chat or make any edits first.

Files / Areas Touched:
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `CHANGELOG.md`

## 2026-04-20 - Relaxed Narrow-Scope Confirmation And Clarified Module Selection

Technical Summary:
- Relaxed the timing requirement for narrower board scopes so focused plans like `activities + weather` can confirm with a single usable timing signal instead of forcing both a window and a trip length.
- Updated the backend details-collection helper to stop treating trip length as missing for narrow scopes where it is not actually required.
- Refined the module step UI so it explains more clearly that every module is optional and that `full trip` is only the default starting point.
- Adjusted the module step summary to read `Full trip` when all modules are active instead of listing all four names mechanically.
- Re-tested the live board flow in Chrome and confirmed that an `activities + weather` configuration can now confirm after setting just a rough timing signal.

Plain-English Summary:
- The board was being too strict when only a few modules were selected.
- If the user narrows the scope to something like activities and weather, they no longer have to overfill timing details just to unlock confirmation.
- The module section is also easier to understand now because it explicitly says that all modules are optional and that full-trip planning is simply the default starting state.

Files / Areas Touched:
- `backend/app/graph/planner/details_collection.py`
- `frontend/src/components/package/trip-details-board-model.ts`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Fixed The Live Route-To-Details Flow

Technical Summary:
- Removed the fake one-adult default from the live details board and kept traveller counts nullable until the user explicitly sets them.
- Changed the board confirm path so `Confirm trip details` is the real structured commit instead of an intermediate step that led into a second hidden confirmation flow.
- Updated planner phase and board-visibility logic so the board collapses back to helper mode immediately after a successful details confirm.
- Refreshed the assistant response builder with cleaner, warmer details-stage copy and a simpler post-confirmation response.
- Reworked the budget step away from a misleading prefilled slider toward explicit amount entry while tightening confirmation gating so incomplete details cannot be submitted as valid.
- Cleaned the board action message copy so the chat reflects structured board input in a more natural way.

Plain-English Summary:
- The trip-details board no longer pretends there is already one adult on the trip before the user sets that.
- Clicking `Confirm trip details` now actually commits the details and gets out of the way, instead of leading into another awkward extra confirmation step.
- The assistant now asks for missing trip details in a more natural, personal way.
- The budget step is more honest and less confusing because it no longer shows a fake default amount.
- Overall, the route-to-details stage now behaves more like a polished planner and less like a broken multi-step form.

Files / Areas Touched:
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Budget Section And Separated Modules Into Optional Step

Technical Summary:
- Split the combined "Budget & Scope" step into two separate steps: "Budget" and "Modules".
- Redesigned budget section with a prominent card showing total budget with CircleDollarSign icon.
- Budget style buttons now use card-based design with selection states and checkmarks.
- Created modules step as an optional step (always marked complete) with "Optional" badge.
- Each module now displays in a card with icon, name, description, and selection state.
- Added module icons: Plane (flights), Hotel (hotels), Sparkles (activities), Cloud (weather).
- Created `getModuleConfig` helper function to map modules to their icons and descriptions.
- Updated step completion logic to treat budget and modules as separate steps.
- Modules step is always complete since all modules are enabled by default.
- Updated step order, titles, icons, and summaries for the new structure.

Plain-English Summary:
- The budget and modules settings are now in separate steps instead of being combined.
- The budget section has a cleaner, more prominent design with a large card showing your total budget.
- Budget style options (Budget/Mid-range/Premium) now look like the other selection cards with proper highlighting.
- The modules step is now optional and clearly marked with an "Optional" badge.
- Each module (Flights, Hotels, Activities, Weather) has its own card with an icon and description.
- Since all modules are enabled by default, you can skip this step entirely if you want everything planned.
- The flow is now: Route → Timing → Travellers → Style → Budget → Modules (optional).

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Fixed Null Traveller State Overriding The One-Adult Default

Technical Summary:
- Updated the trip-details board form normalizer so persisted `null` traveller values no longer override the board's default of `1` adult and `0` children.
- This keeps the rendered traveller count and the actual completion state in sync when a fresh or partially-filled board is loaded.

Plain-English Summary:
- The traveller step could still behave like it was empty even when the UI showed one adult.
- That happened because old null values from saved state were quietly overwriting the new default.
- The board now treats one adult as the real starting state, so the step unlocks properly without needing a workaround.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Trip Style Section With Custom Input

Technical Summary:
- Redesigned the trip style/vibe section with a modern card-based layout featuring icons for each style.
- Added unique icons for each style: UtensilsCrossed (food), Compass (culture), Palmtree (relaxed), Wine (luxury), Heart (romantic), UsersRound (family), Mountain (adventure/outdoors), Sparkles (nightlife).
- Implemented visual selection states with CTA color highlights, checkmarks, and subtle background tints.
- Added custom style input field allowing users to describe their own preferences (e.g., "photography-focused", "wellness retreat").
- Cards show hover effects and smooth transitions between selected/unselected states.
- Added `custom_style` field to TripDetailsCollectionFormState type and form default state.
- Created `getStyleConfig` helper function to map styles to their icon configurations.

Plain-English Summary:
- The trip style section now has a much more visual, engaging design with icons representing each style.
- Each style is displayed in its own card with a relevant icon (fork/knife for food, compass for culture, etc.).
- When you select a style, the card lights up with the CTA color and shows a checkmark.
- Added a custom input field below the style cards where you can type your own preferences if the preset styles don't fit.
- The whole section feels more interactive with smooth hover effects and clear visual feedback.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-20 - Defaulted Traveller Count To One Adult In The Details Board

Technical Summary:
- Updated the trip-details board's empty form defaults so the traveller step now initializes with `1` adult and `0` children instead of null values.
- This aligns the underlying form state with the intended UI default, so the traveller step can be treated as complete immediately when the board starts at one adult.

Plain-English Summary:
- The board was acting like `1 adult` was only a visual placeholder, so the user sometimes had to change the control and change it back before the step would unlock.
- It now starts with a real default of one adult, so the traveller step works properly from the beginning.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Constrained End-Date Selection To Valid Future Dates

Technical Summary:
- Extended the shared date-picker component to accept disabled-day matchers and passed a start-date-based constraint into the timing step's end-date picker.
- The end-date calendar now disables every date before the selected start date, and the board clears an existing end date automatically if the start date is moved past it.

Plain-English Summary:
- The trip board now behaves like a proper date range picker.
- Once someone picks a start date, the end-date calendar stops them from choosing earlier dates, and it also clears the old end date if it becomes invalid.

Files / Areas Touched:
- `frontend/src/components/ui/date-picker.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Traveller Count Section

Technical Summary:
- Redesigned the traveller count section with a modern card-based layout instead of simple counter fields.
- Added visual icons (Users for adults, Baby for children) with colored circular backgrounds.
- Implemented gradient backgrounds and hover effects on cards for better visual appeal.
- Increased counter number size to 2xl and made them bold for better readability.
- Added descriptive text ("18 years and older" / "Under 18 years") for clarity.
- Used a 2-column grid layout on larger screens for better space utilization.
- Fixed null safety issues by providing default values (1 for adults, 0 for children).

Plain-English Summary:
- The traveller count section now has a much more polished, modern look.
- Each traveller type (adults and children) is displayed in its own card with an icon and description.
- The cards have subtle gradients and hover effects that make them feel more interactive.
- The counter numbers are larger and easier to read.
- Everything is laid out in a clean 2-column grid that looks great on all screen sizes.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Allowed Exact Dates To Complete The Timing Step

Technical Summary:
- Updated the trip-details timing-step completion rule so users can move forward with either a rough timing plus trip length, or a full exact-date range.
- This removes the unintended frontend dependency on selecting a rough travel window when both `start_date` and `end_date` are already present.

Plain-English Summary:
- The timing step was blocking people even when they had already picked exact start and end dates.
- It now works the way it should: either rough timing or exact dates is enough to continue.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Replaced Default Date Inputs With shadcn Studio Calendar Component

Technical Summary:
- Installed `react-day-picker@^9.0.0` and `date-fns` dependencies to support modern calendar functionality with React 19.
- Installed shadcn studio calendar component (calendar-09) which provides a polished calendar with built-in month/year dropdown navigation.
- Created Popover component wrapper using @radix-ui/react-popover for the calendar dropdown interaction.
- Built a DatePicker component that combines the Calendar and Popover into a reusable date selection interface with proper formatting using date-fns.
- Replaced the ugly default HTML date inputs in the timing step with the new DatePicker component that shows a beautiful calendar popup.
- Configured calendar to use `captionLayout="dropdown"` for clean month and year selection dropdowns.
- Added auto-close functionality so the calendar popup closes immediately after selecting a date for better UX.
- Fixed weekend selection bug by explicitly setting `disabled={false}` to ensure all days including weekends are selectable.
- Fixed timezone bug where selected dates would shift by one day due to UTC conversion - now uses local date formatting to preserve the exact selected date.
- Calendar uses shadcn's design system with proper styling, spacing, and interactions out of the box.

Plain-English Summary:
- The default HTML date inputs looked ugly and inconsistent with the rest of the interface.
- I've replaced them with a beautiful calendar component from shadcn studio that pops up when you click the date field.
- The calendar has a clean, professional design with dropdown selectors for month and year, making it easy to quickly jump to any date.
- When you click a date, the calendar automatically closes and confirms your selection - no extra clicks needed.
- Fixed a bug where weekends couldn't be selected - now all days are clickable including Saturdays and Sundays.
- Everything is properly styled and matches modern UI standards.
- This new calendar component is now the default for all date selection across the app.

Files / Areas Touched:
- `frontend/package.json`
- `frontend/src/components/ui/popover.tsx` (new)
- `frontend/src/components/ui/calendar.tsx` (new)
- `frontend/src/components/ui/date-picker.tsx` (new)
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Completely Redesigned Trip Details Board With Cleaner Interface

Technical Summary:
- Removed all nested card-within-card patterns that created visual clutter and excessive borders throughout the details board.
- Simplified the step card design to use minimal borders with subtle dividers instead of heavy shadowed containers, reducing visual weight by ~60%.
- Replaced gradient backgrounds and complex nested containers with clean white/50 backgrounds and simple border treatments.
- Streamlined all form components (CounterField, ChoiceButton, ToggleRow) to remove unnecessary card wrappers and use consistent border/background patterns.
- Removed the RouteTerminal component entirely and replaced it with standard FieldBlock inputs for a more uniform interface.
- Updated input styling to use cleaner borders with focus states that highlight with the CTA color instead of accent-soft.
- Simplified button styling across continue actions and the main CTA to use consistent rounded-lg treatment instead of mixed rounded-full/rounded-2xl.
- Reduced spacing complexity by standardizing on space-y-5 for step content and removing variable padding throughout nested components.

Plain-English Summary:
- The trip details board had too many cards inside cards, making it feel cluttered and heavy. The entire interface has been redesigned with a much cleaner, more breathable layout.
- Instead of multiple layers of borders, shadows, and backgrounds, everything now uses simple, consistent styling that feels lighter and more modern.
- All the form controls (counters, choice buttons, toggles) have been simplified to remove unnecessary decoration while keeping them easy to use.
- The overall feel is now more like a clean form and less like a dashboard with lots of panels, which makes it easier to focus on filling in trip details.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Added Clean Location Suggestions To The Route Inputs

Technical Summary:
- Added a dedicated route-location input component with a lightweight suggestion dropdown for the `From` and `To` fields in the trip-details step flow.
- Introduced a typed location-suggestion helper so the route autocomplete stays isolated from the board layout code and does not bloat the step component.
- Simplified the visible suggestion labels to city-first values instead of airport-style strings, removed the duplicated value line above each input, and deduplicated repeated locations like `London`.

Plain-English Summary:
- The route fields now suggest locations as you type, which makes the first step feel faster and more polished.
- I also cleaned up the route inputs so they stop repeating the city name above the field and stop showing airport-heavy labels that made the UI feel messy.
- The result is a simpler city-style autocomplete that fits the board much better.

Files / Areas Touched:
- `frontend/src/components/package/route-location-input.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/lib/location-suggestions.ts`
- `CHANGELOG.md`

## 2026-04-20 - Replaced Hardcoded Route Suggestions With Live Provider Search

Technical Summary:
- Removed the frontend-only hardcoded route suggestion list and replaced it with a real authenticated FastAPI location-search route backed by Mapbox geocoding.
- Added typed backend schemas and a dedicated location-search service so the route autocomplete now returns live place results without baking location data into the UI.
- Updated the route input component to debounce live provider search, thread the auth token through the board preview into the details board, and render live results instead of static seeded values.

Plain-English Summary:
- The route autocomplete was fake before because it was just showing a fixed list.
- It now searches live locations through the backend, so the suggestions can change based on what the user actually types.
- I also removed the hardcoded suggestion source entirely so this part of the UI is no longer pretending to be dynamic.

Files / Areas Touched:
- `backend/app/api/routes/providers.py`
- `backend/app/schemas/location_search.py`
- `backend/app/services/location_search_service.py`
- `frontend/src/components/package/route-location-input.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/lib/api/providers.ts`
- `frontend/src/types/location-suggestions.ts`
- `CHANGELOG.md`

## 2026-04-20 - Redesigned Timing Step With Cleaner Single-Column Layout

Technical Summary:
- Redesigned the timing step from a cramped two-column grid to a cleaner single-column layout with better spacing and visual hierarchy.
- Changed the button grid from 2 columns to 3 columns for both travel window and trip length, making each option more readable and easier to tap.
- Replaced the nested card container for exact dates with a simple border-top divider, reducing visual clutter while maintaining clear separation.
- Removed the FieldBlock wrappers around date inputs and used direct Input components for a lighter feel.
- Updated the exact dates section label from "Optional exact dates" to "Or set exact dates" for clearer language.

Plain-English Summary:
- The timing step felt cramped with two columns of small buttons side by side.
- It now uses a cleaner single-column layout where each section has more breathing room and the buttons are arranged in 3 columns instead of 2.
- The exact dates section is now separated with a simple line instead of a heavy card, making the whole step feel lighter and easier to scan.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Simplified The Timing Step By Removing Extra Custom Inputs

Technical Summary:
- Removed the extra `Custom window` and `Custom length` inputs from the timing step after the quick-pick timing redesign.
- Kept the guided timing chips and the optional exact-date block, so the step still captures the important timing detail without introducing extra visual clutter.

Plain-English Summary:
- The timing step had started to feel too busy because it offered too many ways to enter the same information.
- It is cleaner now: users pick from the main timing options, and exact dates remain available if needed.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-20 - Rebuilt The Details Board Into A Structured Step Flow

Technical Summary:
- Replaced the cluttered multi-card details dashboard with a single guided step flow that uses collapsible sections for route, timing, travellers, trip style, and budget/module scope.
- Reworked the details-board container to reset cleanly per board payload without effect-driven state sync, keeping the local step form stable while still reflecting persisted planner state.
- Tightened the UI system so the details board uses the same planner-board tokens, typography, and interaction palette as the destination suggestion board, including the budget slider and module toggles.
- Downloaded the Stitch `Trip Details - Structured Flow` reference into `.codex-temp/stitch/` and used it as the layout direction for the new accordion-style hierarchy.

Plain-English Summary:
- The old details board still felt messy and overcrowded, so it has been rebuilt into a much cleaner step-by-step flow.
- Instead of showing everything at once, Wandrix now guides the user through one section at a time, which gives each part of the trip setup more space and makes the board feel calmer.
- The details board now feels much closer to the destination suggestion board instead of looking like a separate interface.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `.codex-temp/stitch/trip-details-structured-flow.html`
- `.codex-temp/stitch/trip-details-structured-flow.png`
- `CHANGELOG.md`

## 2026-04-20 - Polished The Route Step And Primary Actions In The Details Board

Technical Summary:
- Redesigned the route step so it now reads as a terminal-to-terminal layout instead of two plain stacked inputs, with a calmer route shell, clearer `From` / `To` presentation, and a centered connector treatment.
- Added a dedicated `RouteTerminal` component inside the details-board sections file so the route step has stronger hierarchy without making the rest of the step flow heavier.
- Tightened the continue and confirm button styling to feel more deliberate and less generic, and cleaned up the lingering summary/budget encoding artifacts in the same pass.

Plain-English Summary:
- The route card was still feeling too basic, so it now looks more like a travel step and less like a raw form.
- I also polished the main action buttons so the board feels more intentional overall instead of just functional.
- This pass mainly improves the first impression of the details flow without changing how the planner works.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Restyled The Details Board To Match The Stitch Stepped Layout

Technical Summary:
- Rebuilt the trip-details board into a stepped travel-brief layout based on the Stitch screen `Trip Details - Stepped Layout`.
- Split the oversized board file into a smaller container component and a new sections/primitives file so the stepped UI, counters, chips, summary strip, and footer CTA each have a clearer responsibility.
- Replaced the previous stacked form-card treatment with a stitched layout: large board shell, compact working-brief strip, numbered steps for route, timing, party, vibe, and module focus, plus a stronger confirmation footer action.
- Kept all existing board behavior and action payloads intact while updating only the presentation layer and field ergonomics.

Plain-English Summary:
- The trip-details board looked too generic and cluttered, so it has been redesigned to feel much closer to the Stitch concept you pointed me to.
- It now reads like a guided travel brief with clear numbered steps instead of a pile of form blocks, while still using Wandrix’s own data and flow.
- I also split the code up so we do not keep growing one huge frontend file every time the board changes.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Unified The Details Board With The Suggestion-Board Visual System

Technical Summary:
- Reworked the details board again so it now shares the same visual system as the destination suggestion board: the same teal-led heading treatment, soft grey board background, white rounded cards, and the same display/body typography balance.
- Removed the interim `working brief` strip completely and replaced the form layout with a cleaner dashboard-style arrangement inspired by the Stitch visual-dashboard references.
- Replaced the old budget input block with a slider-driven budget card plus segmented posture controls, and tightened the card structure around route, vibe, companions, timing, and module focus.
- Added dedicated budget-slider track/thumb styling in `globals.css` and kept the implementation split into a board container plus reusable board sections so the file size stays under control.

Plain-English Summary:
- The first redesign still looked like a separate UI from the destination suggestion board, so it has been rebuilt again to feel like the same product stage instead of a different theme.
- The board is now cleaner, more visual, and closer to the Stitch references you shared, especially in the card treatment, spacing, and overall hierarchy.
- Budget is now handled with a proper slider instead of another plain form field, which makes the board feel more deliberate and easier to use.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-19 - Tightened Board Hierarchy And Moved Board Styling Onto Shared Tokens

Technical Summary:
- Simplified the route card so it no longer repeats the route summary as both a heading and a card title, replacing it with a calmer `Route details` block plus a directional field layout.
- Reduced timing clutter by separating rough timing from optional exact dates, so the main travel-window card is easier to scan.
- Replaced module chips with toggle-style rows and moved board hover/selection colors onto shared planner-board CSS variables so the details board and suggestion board now draw from the same palette.
- Updated both board modes to use the shared planner-board tokens for background, card surface, borders, muted text, accent states, and CTA color.

Plain-English Summary:
- The details board was still feeling messy, especially in the route and timing sections, and the interaction colors were too one-off.
- It now has a cleaner route card, a less crowded timing section, and module controls that feel more deliberate.
- The destination suggestions board and the details board now share the same visual language much more closely instead of feeling like two different products.

Files / Areas Touched:
- `frontend/src/components/package/trip-details-board-sections.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-19 - Fixed Conversational Trip-Brief Confirmation Runtime

Technical Summary:
- Fixed the planner runtime after the new route-to-details confirmation work by replacing stale `origin_summary` references with the actual resolved location-context `summary` field.
- Finished the conversational brief-confirmation flow so destination-card clicks, board detail confirms, and final brief confirms all appear as visible user-style chat turns while still going through the typed board-action path.
- Extended the details board with editable `from` and `to` fields, kept the board in helper mode until all required trip parameters are present, and only allowed module enrichment after the trip brief is explicitly confirmed.
- Verified the updated flow end to end in the live browser: broad destination suggestions, destination-card handoff, details collection, final recap, partial chat-only updates, and final confirmation.

Plain-English Summary:
- Wandrix had a backend crash right in the middle of the new planning flow because the planner was reading the wrong location field name.
- That crash is fixed now, and the trip setup flow feels more conversational: choosing a destination, filling details on the board, and confirming the final brief all show up cleanly in chat instead of feeling like hidden system actions.
- I also verified that if you give only one detail in chat, Wandrix now acknowledges just that piece and keeps asking only for what is still missing.

Files / Areas Touched:
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `CHANGELOG.md`

## 2026-04-19 - Polished Destination-Suggestion Reply Copy

Technical Summary:
- Adjusted the destination-suggestion response builder so greeting text and location-source sentences are stitched together more cleanly.
- Removed an extra punctuation join that could produce doubled sentence endings like `..` in the assistant reply.

Plain-English Summary:
- The destination suggestion reply sounded awkward and sometimes showed a double full stop when it mentioned browser location.
- Wandrix now phrases that opening more cleanly so the first suggestion message reads like a real assistant instead of glued-together system text.

Files / Areas Touched:
- `backend/app/graph/planner/response_builder.py`
- `CHANGELOG.md`

## 2026-04-19 - Fixed Details-Stage Chat Handoff And Hid Synthetic Board Messages

Technical Summary:
- Reordered planner response composition so structured board-aware replies for `destination_suggestions` and `details_collection` take precedence over generic LLM fallback text.
- Added a frontend message filter in the chat renderer so synthetic board-triggered helper messages used to drive backend actions are no longer shown as normal user bubbles in the transcript.
- Kept the underlying board-action runtime behavior intact, so destination-card clicks and board confirms still go through the same typed backend path without cluttering the visible chat.

Plain-English Summary:
- Wandrix was opening the details board, but the chat was still showing a generic freeform reply instead of the promised checklist-style handoff.
- The board was also leaking awkward system-like messages into the conversation, which made the helper feel intrusive.
- Now the assistant shows the proper checklist response when the details stage starts, and board actions stay behind the scenes instead of making the chat look messy.

Files / Areas Touched:
- `backend/app/graph/planner/response_builder.py`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Added Route-To-Details Collection Stage In Chat

Technical Summary:
- Extended the planner state with a new `details_collection` board mode, checklist items, a structured details-form payload, and a typed `confirm_trip_details` board action.
- Added `budget_posture` to trip configuration and planner turn models, then wired explicit board-confirm payloads into the planner merge path so board-confirmed values become structured confirmed inputs without relying on heuristic parsing.
- Updated board-state construction and assistant response composition so once Wandrix has a usable route, chat sends a checklist-style message and the right board becomes an adaptive details form for timing, travelers, style, budget, and module scope.
- Added a new frontend details-board component, connected its confirm action through the existing conversation route, and returned the right board to helper mode after the board-confirm event.
- Updated the chat planner spec to document the new details-collection stage.

Plain-English Summary:
- Once Wandrix has the route, it can now move into a cleaner “fill in the rest” stage instead of jumping straight toward itinerary output.
- The assistant now gives a short checklist in chat, and the board on the right can collect the same details in a structured way if the user prefers clicking instead of typing.
- When the user confirms the board, Wandrix treats those values as real trip inputs, recaps them in chat, and then hides the board again until a later stage.

Files / Areas Touched:
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/conversation.py`
- `backend/app/graph/planner/board_action_merge.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/draft_merge.py`
- `backend/app/graph/planner/turn_models.py`
- `backend/app/graph/planner/understanding.py`
- `frontend/src/components/package/trip-details-board.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `docs/chat-planner-spec.md`
- `CHANGELOG.md`

## 2026-04-19 - Removed Markdown Emphasis Markers From Assistant Chat Replies

Technical Summary:
- Updated the planner prompt so `assistant_response` should stay plain prose instead of returning markdown styling like bold markers or headings.
- Added backend assistant-text sanitization in the response builder so markdown emphasis markers such as `**bold**`, `__underline__`, backticks, and heading markers are stripped before the chat UI receives the message.
- Kept the existing plain-text chat rendering path intact instead of adding markdown rendering to the assistant surface.

Plain-English Summary:
- The assistant was sending markdown-style formatting into a chat view that only shows plain text, which is why stray `**` markers were appearing in the conversation.
- Wandrix now cleans that up before the message reaches the UI, so the chat should look much cleaner without changing how the chat component works.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/response_builder.py`
- `CHANGELOG.md`

## 2026-04-19 - Fixed Browser-Location Suggestions Getting Stuck In Helper Mode

Technical Summary:
- Reworked the chat-side planner location helper so browser geolocation gets a longer window to resolve and only permanent blockers like permission denial or unsupported geolocation are cached.
- Stopped transient geolocation failures from poisoning a trip with a forever-unavailable location state, including cleanup for legacy cached values.
- Tightened the planner prompt and response copy so broad asks with browser location available should produce destination suggestions first, while still inviting the user to correct the detected departure point when needed.

Plain-English Summary:
- Wandrix was asking for a departure city even when browser location was available because the location lookup could fail too quickly and then get stuck in a bad cached state.
- The planner now gives browser location more time, retries better, and is more direct about using the detected location as a starting point while still letting the user correct it.

Files / Areas Touched:
- `frontend/src/lib/planner-location.ts`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/response_builder.py`
- `CHANGELOG.md`

## 2026-04-19 - Fixed Recent Sidebar Title Drift After Reload

Technical Summary:
- Fixed the draft-update path in the chat workspace so sidebar recent-trip entries are updated from the latest in-memory workspace state instead of a stale outer `workspace` closure.
- This removes a race where the active chat title could update correctly in the workspace while the cached recent-trips list stayed on an older generic `Trip abc123` label, especially after first-message persistence and reload.

Plain-English Summary:
- The latest chat should no longer keep showing its trip code in the sidebar after reload just because the recent list missed the title update.
- When Wandrix gets a real title for the trip, the saved chat list should now stay in sync.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Improved Broad Chat Titles And Active Sidebar Title Sync

Technical Summary:
- Strengthened the planner title-generation prompt so broad but meaningful first-turn asks now produce grounded saved-chat titles like `Warm Getaway` instead of falling back to generic `Trip abc123` labels.
- Re-ran the trip retitle script against existing saved chats so recently created generic chats could pick up better names from their stored conversation context.
- Updated the chat sidebar so the currently open trip prefers the live workspace draft title over any stale cached list title while the page is attaching after reload.

Plain-English Summary:
- Broad chats like “I want to go somewhere warm” now get a proper saved name instead of a trip code.
- Even right after reload, the active chat should settle onto the real trip title instead of sticking to the generic cached label.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/scripts/retitle_and_prune_trips.py`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Stabilized The First Real Chat Send From A New Trip

Technical Summary:
- Changed the `/chat` first-send flow so ephemeral new-trip shells do not immediately swap routes before the first backend conversation turn finishes.
- `TravelPlannerAssistant` now waits for the real persisted trip to be created, sends the first turn to that trip, seeds the local thread cache with the first user/assistant exchange, and only then activates the persisted workspace.
- Added a workspace handoff guard so the chat bootstrap logic does not immediately re-run while the route is still catching up from `/chat` to the newly persisted trip, which was causing extra empty trips and blank-chat resets.

Plain-English Summary:
- Starting a brand-new chat should now feel much more stable.
- The first message stays visible, the assistant reply comes back properly, and Wandrix should no longer jump into another blank chat right in the middle of that first exchange.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Filtered Stale Empty Trips Out Of Sidebar Cache

Technical Summary:
- Added recent-trip cache hygiene in `frontend/src/lib/recent-trips-cache.ts` so blank generic trips are filtered out when reading and writing the sidebar cache.
- The filter now drops stale cached rows that still look like untouched placeholder chats, which prevents deleted empty trips from reappearing in the sidebar from `localStorage` after the database has already been cleaned.
- Cleared the live browser cache entry for the current user and reloaded `/chat` to verify the sidebar now reflects the real cleaned trip list.

Plain-English Summary:
- The empty chats you were still seeing were coming from old browser cache, not the database.
- Wandrix now cleans those stale blank entries out of the sidebar cache so they do not keep popping back in after cleanup.

Files / Areas Touched:
- `frontend/src/lib/recent-trips-cache.ts`
- `CHANGELOG.md`

## 2026-04-19 - Retitled Used Chats And Removed Empty Saved Trips

Technical Summary:
- Added a backend maintenance script at `backend/scripts/retitle_and_prune_trips.py` to clean up old saved-trip data.
- The script reads persisted trip context and raw checkpointed chat messages, generates short sidebar-friendly titles for real chats through the LLM, updates both `trips.title` and `trip_drafts.title`, and removes trips that have no real planning activity.
- The empty-trip cleanup also deletes any matching LangGraph checkpoint rows by `thread_id` so the removed chats do not leave orphaned checkpoint data behind.
- Ran the cleanup against the current database and removed 57 empty trips while retitling 19 meaningful chats.

Plain-English Summary:
- Old blank chats are gone now, so the sidebar should be much easier to scan.
- The chats you actually used now have more useful names instead of generic `Trip abc123` labels.

Files / Areas Touched:
- `backend/scripts/retitle_and_prune_trips.py`
- `CHANGELOG.md`

## 2026-04-19 - Synced LLM Trip Titles Into Saved Trips And Sidebar Time Labels

Technical Summary:
- Updated the planner extraction prompt so the LLM now aims to produce a concise 2-6 word trip title when there is enough real trip signal, instead of falling back to generic labels.
- Persisted the draft title into the main `trips` row after conversation turns, so sidebar listings and later reloads use the same summarized title that the planner generated.
- Updated the chat workspace to sync the in-memory workspace trip title with the latest draft title immediately after each turn.
- Replaced the sidebar's old route-shaping fallback text with relative activity time formatting based on `updated_at`, using minutes/hours ago for today, days ago within a week, and weekday labels after that.

Plain-English Summary:
- Wandrix now gives used chats a better short title after the first real message, so the sidebar is easier to scan.
- The saved trip list no longer says vague things like `Route still being shaped`; it now shows when each chat was last active in a more natural way.

Files / Areas Touched:
- `backend/app/graph/planner/understanding.py`
- `backend/app/repositories/trip_repository.py`
- `backend/app/services/conversation_service.py`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Fixed New Trip Route Activation In Chat

Technical Summary:
- Replaced the browser-level `window.history.replaceState(...)` call in the chat workspace new-trip flow with Next.js app-router navigation through `router.replace(...)`.
- This keeps the `?trip=` query in sync with the actual client router state after creating a fresh trip, so the newly created trip becomes the active route instead of leaving the interface logically attached to the previous one.

Plain-English Summary:
- Clicking `New Trip` should now open the new trip properly.
- Wandrix now switches to the fresh trip through Next’s router instead of using a lower-level history update that could leave the old trip selected.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Made New Trip Switch Active Chat Immediately

Technical Summary:
- Added an optimistic pending trip id in the chat workspace so a freshly created trip becomes the active chat target immediately instead of waiting for the router query to finish updating.
- Added a bootstrap short-circuit for the exact selected trip already present in workspace state, which prevents a redundant reload of the same new trip right after creation.

Plain-English Summary:
- `New Trip` should now feel much faster and more direct.
- As soon as Wandrix creates the new trip template, the chat switches to it right away instead of hanging onto the old trip until the route cycle completes.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Stopped New Trips From Mounting With Old Conversation History

Technical Summary:
- Changed the assistant runtime’s saved-message state to track both the `tripId` and the messages together, instead of keeping one generic message array across trip switches.
- The chat now only mounts a thread runtime with history that belongs to the currently active trip, which prevents a newly created trip from briefly rendering the previous trip’s messages before its own history state catches up.

Plain-English Summary:
- A fresh trip should no longer open with the old chat still visible.
- Wandrix now keeps each trip’s message state properly separated, so a new trip starts clean instead of momentarily showing the previous conversation.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Cleared Stale Local Thread Cache When A Trip Has No Saved History

Technical Summary:
- Updated the assistant history loader so an empty backend conversation history now explicitly resets the local cached thread for that trip instead of leaving stale client-only messages in place.
- This prevents fresh or empty trips from continuing to show bad cached content after reloads when the server has no actual conversation for that trip.

Plain-English Summary:
- If a trip has no saved chat history, Wandrix now clears the local copy instead of showing old messages by mistake.
- That means empty trips should stay empty, even after refresh, instead of inheriting leftover chat from another trip.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Made New Trip Open With A Local Starter Draft

Technical Summary:
- Added a frontend starter-draft builder so a newly created trip can mount immediately with the known default planner shape instead of waiting on a follow-up `getTripDraft()` request before the UI feels ready.
- Updated the chat workspace new-trip flow to use that local starter draft as soon as `createTrip()` returns, and marked freshly created trip ids so the assistant skips the initial history-sync call for those blank trips.

Plain-English Summary:
- Opening a new trip should now feel much faster.
- Wandrix now shows the fresh planner template right away after the trip is created instead of pausing to fetch an empty draft and empty history before the chat looks usable.

Files / Areas Touched:
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Stopped Empty New Trips From Being Persisted Before First Use

Technical Summary:
- Reworked the `/chat` new-trip flow so clicking `New Trip` now opens an ephemeral local workspace instead of immediately creating a database trip and draft.
- Added an explicit persisted/ephemeral workspace flag, a local ephemeral trip builder, and a first-send persistence hook so the real browser session and trip are only created when the user actually sends the first message.
- Prevented ephemeral trips from polluting recent trips, last-active-trip storage, and initial history sync while keeping the assistant able to convert the local draft into a real trip transparently on first use.

Plain-English Summary:
- Empty chat templates are no longer being saved as real trips.
- Wandrix now waits until you actually send a message before it creates a trip in the database, which keeps the trip list cleaner and avoids storing unused blank sessions.

Files / Areas Touched:
- `frontend/src/types/planner-workspace.ts`
- `frontend/src/lib/trip-draft-starter.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Saved Stitch Reference Assets For The Improved Travel Planner Screen

## 2026-04-19 - Rebuilt Destination Suggestions As A Separate Stitch-Matched Board Component

## 2026-04-19 - Added A Dedicated Destination Image Resolver For Suggestion Cards

Technical Summary:
- Added a new frontend destination-image resolver that caches card images per session and prefers place-specific imagery instead of treating all suggestion cards as generic travel wallpaper.
- The resolver now uses a three-step strategy: curated destination matches first, Wikimedia page-summary images second, and only then a safe fallback image.
- Updated the destination suggestion cards to resolve their images asynchronously through the new utility while keeping the suggestion UI isolated from the rest of the board flow.

Plain-English Summary:
- The destination cards now have a better image system behind them.
- Instead of just showing random travel photos, Wandrix now tries much harder to show something that actually matches the destination, and it remembers the result so the board feels more stable during the session.

Files / Areas Touched:
- `frontend/src/lib/destination-images.ts`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

Technical Summary:
- Recreated the destination-suggestion UI as its own dedicated board component instead of mixing the Stitch-style layout into the broader board preview file.
- Replaced the previous uneven editorial layout with a stricter Stitch-style two-column card grid, matching the saved reference much more closely with a flat travel-editorial composition, image-first cards, compact badges, and a single `Select this` action.
- Kept the destination-suggestion mode isolated so later board stages can evolve independently without rewriting the early suggestion surface again.

Plain-English Summary:
- The destination suggestions on the right are now built as their own separate piece, which makes the design easier to control and easier to reuse later.
- I also reshaped the layout to look much closer to the Stitch example you shared instead of keeping the older custom version that still felt off.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `CHANGELOG.md`

Technical Summary:
- Downloaded the hosted Stitch screenshot and generated HTML for the `Improved Travel Planner` screen from project `7418467430330422379`.
- Stored both reference assets locally under the repo docs area so the board redesign can follow the exact screen style instead of loosely approximating it.

Plain-English Summary:
- The Stitch design you pointed me to is now saved inside the project.
- We can use that exact visual direction as the reference for the next UI pass, including treating `Explore this` as the `Select this` interaction pattern.

Files / Areas Touched:
- `docs/stitch-references/improved-travel-planner/improved-travel-planner.png`
- `docs/stitch-references/improved-travel-planner/improved-travel-planner.html`
- `CHANGELOG.md`

## 2026-04-19 - Redesigned The Destination Suggestion Board And Hardened Image Fallbacks

Technical Summary:
- Rebuilt the destination suggestion board into a more editorial split layout with one lead destination, three supporting options, and a cleaner own-choice action instead of the previous uniform generated-looking card grid.
- Added stronger destination image fallbacks in the shared board-image helper so common suggestion cities now resolve to high-quality curated Unsplash images instead of depending on fragile generic source URLs.
- Updated the suggestion board image resolver to ignore low-quality `source.unsplash.com` links from planner output and replace them with stable curated destination imagery.

Plain-English Summary:
- The destination suggestions on the right side should now look much better and feel more like a real travel product.
- The images should also be much more reliable and higher quality, instead of random weak placeholders or broken generic wallpaper pulls.

Files / Areas Touched:
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Added Location-Aware Destination Suggestions To Early Chat Planning

Technical Summary:
- Extended the planner turn contract and persisted conversation state with a structured `suggestion_board` payload, destination suggestion cards, location-context input, and board-action input so `/chat` can drive early destination choices without relying on freeform text alone.
- Added backend location-context resolution, suggestion-board state building, and warmer suggestion responses so broad destination asks can use browser location first, fall back to saved home-base context, and stay conservative about what is actually confirmed.
- Wired the frontend chat and board together with an on-demand browser-location helper, a board-action bridge for destination-card clicks and `Own choice`, and a new right-side suggestion board that renders from persisted trip conversation state instead of placeholder copy.
- Switched conversation routes to compile a fresh planning graph from the pooled checkpointer per request, which keeps the pooled setup but avoids reusing a stale graph/checkpointer object during conversation sends and history reads.
- Updated the chat planner spec so the destination-suggestion board flow is documented as part of the core `/chat` planner behavior.

Plain-English Summary:
- Wandrix can now suggest destinations much more intelligently when the user says something broad like wanting somewhere sunny or romantic.
- If location assistance is allowed, the assistant can use the user's current location; otherwise it falls back to the saved home base and says so clearly.
- The right board can now show four visual destination options plus an `Own choice` path, and clicking a suggestion now behaves like a real planner input instead of a fake UI-only interaction.
- The backend conversation history/send path is also safer again because it no longer depends on one reused graph object.

Files / Areas Touched:
- `backend/app/api/routes/conversation.py`
- `backend/app/core/application.py`
- `backend/app/graph/planner/runner.py`
- `backend/app/graph/planner/understanding.py`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/conversation_state.py`
- `backend/app/graph/planner/location_context.py`
- `backend/app/graph/planner/suggestion_board.py`
- `backend/app/schemas/conversation.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/services/conversation_service.py`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/assistant/travel-planner-board-actions.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-suggestion-board.tsx`
- `frontend/src/lib/planner-location.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/planner-board.ts`
- `docs/chat-planner-spec.md`
- `CHANGELOG.md`

## 2026-04-19 - Deduplicated Destination Geocoding Across Weather And Activities

Technical Summary:
- Extracted destination coordinate lookup into a shared provider helper so weather and activity enrichment no longer each call Mapbox separately for the same destination.
- Updated planner provider enrichment to resolve destination coordinates once per turn when weather or activities actually need fresh data, then pass those coordinates into both module enrichers.
- Kept the change local to the planner flow and added a safe fallback so a failed shared geocode lookup does not break the whole turn.

Plain-English Summary:
- Wandrix now does less duplicate location work when planning weather and activity ideas.
- If both modules need fresh information for the same destination, the planner looks up the place once and reuses it instead of asking Mapbox twice.

Files / Areas Touched:
- `backend/app/services/providers/location_lookup.py`
- `backend/app/services/providers/weather.py`
- `backend/app/services/providers/activities.py`
- `backend/app/graph/planner/provider_enrichment.py`
- `CHANGELOG.md`

## 2026-04-19 - Kept The Chat Workspace Mounted While Switching Existing Trips

Technical Summary:
- Removed the eager `setWorkspace(null)` reset at the start of chat workspace bootstrap so switching from one saved trip to another no longer tears down the entire attached workspace shell first.
- Kept the existing cache-first and delayed-attach flow intact, but now the sidebar, chat shell, and board container stay mounted while the newly selected trip hydrates in the background.

Plain-English Summary:
- Moving between saved trips should feel less like a page reload now.
- Wandrix keeps the chat layout in place while the new trip attaches, instead of blanking the whole workspace first.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Reused One Browser Auth Snapshot Across The Chat Workspace

Technical Summary:
- Added a shared browser auth snapshot helper so the workspace resolves the Supabase session once and passes the access token, user id, and user metadata into the assistant runtime.
- Updated the chat workspace bootstrap and trip-creation flow to reuse that snapshot instead of scattering repeated `supabase.auth.getSession()` calls through the chat send, history sync, and profile-default loading paths.
- Removed the assistant-level session lookup so conversation history fetches, profile-context hydration, and backend conversation sends now all ride on the same workspace-owned auth state.

Plain-English Summary:
- The chat frontend now does less repeated auth work in the background.
- Wandrix reads the signed-in session once for the workspace and reuses it, instead of repeatedly asking Supabase for the same session during normal chat activity.

Files / Areas Touched:
- `frontend/src/lib/supabase/auth-snapshot.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Replaced Per-Request Graph Creation With A Pooled Checkpointer

Technical Summary:
- Switched the LangGraph Postgres checkpoint lifecycle from a fresh per-request saver/graph to a startup-owned `psycopg_pool.ConnectionPool`.
- Compiled the planning graph once against a pooled `PostgresSaver`, kept startup responsible for checkpoint setup, and closed the pool cleanly on shutdown.
- Preserved the stale-connection fix while removing the expensive per-request graph recompilation and connection creation path.

Plain-English Summary:
- The backend chat graph should now be cheaper to use on every request.
- Instead of rebuilding the graph and database connection every time, Wandrix now keeps a safer pooled setup alive for the app and reuses it across requests.

Files / Areas Touched:
- `backend/app/graph/checkpointer.py`
- `backend/app/core/application.py`
- `backend/app/api/routes/conversation.py`
- `CHANGELOG.md`

## 2026-04-19 - Stopped Provider Enrichment From Re-Running On Every Chat Turn

Technical Summary:
- Updated planner provider enrichment so flight, weather, and activity calls only re-run when the module becomes ready for the first time or when the inputs that matter for that module actually change.
- Added per-module input-change guards based on route, timing, and activity-style changes instead of re-calling external providers on every follow-up message.
- Kept the behavior simple and local to the planner flow without introducing a broader custom caching layer.

Plain-English Summary:
- Wandrix should no longer keep re-querying live providers every time the user says something minor like “okay” or asks a follow-up.
- The planner now reuses the current results unless the trip details relevant to that module actually changed.

Files / Areas Touched:
- `backend/app/graph/planner/provider_enrichment.py`
- `backend/app/graph/planner/runner.py`
- `CHANGELOG.md`

## 2026-04-19 - Removed The Extra Draft Fetch After Every Chat Turn

Technical Summary:
- Extended the backend conversation response contract so each successful trip-message send now returns the freshly persisted `trip_draft` alongside the assistant message.
- Updated the frontend assistant runtime to consume the returned draft directly instead of issuing a second `getTripDraft()` request after every chat turn.
- Reduced one backend round-trip and one extra draft read from the hot chat-send path.

Plain-English Summary:
- Sending a message in chat now does less unnecessary work.
- Wandrix no longer asks the backend for the same updated trip draft twice after every turn, which should make chat responses a bit leaner.

Files / Areas Touched:
- `backend/app/schemas/conversation.py`
- `backend/app/services/conversation_service.py`
- `frontend/src/types/conversation.ts`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Stopped Conversation History From Reusing A Closed Checkpointer Connection

Technical Summary:
- Removed the long-lived compiled LangGraph instance from FastAPI app state so conversation routes no longer depend on a single startup-time Postgres checkpointer connection.
- Added a request-scoped planning graph context that opens a fresh checkpointer for each conversation send/history call, which avoids stale closed psycopg connections during checkpoint reads.
- Kept startup responsible only for one-time checkpoint table setup.

Plain-English Summary:
- The backend was trying to read chat history through an old database connection that had already closed.
- Now each conversation request gets a fresh graph connection, so loading saved chat history should be much more stable.

Files / Areas Touched:
- `backend/app/graph/checkpointer.py`
- `backend/app/core/application.py`
- `backend/app/api/routes/conversation.py`
- `CHANGELOG.md`

## 2026-04-19 - Made Chat Load First, Board Load Later, And Seeded The Sidebar From Cache

Technical Summary:
- Added client-side recent-trip caching so the sidebar can render saved trips from local storage immediately before the network refresh completes.
- Updated the chat runtime to restore local conversation history first for an existing trip, then sync checkpoint history from the backend in the background instead of blocking the whole pane.
- Split the loading behavior so the chat can open quickly while the right-side board stays in a later-loading helper state with a subtle animated loading treatment.
- Tightened the composer and sidebar selection logic so the active trip is reflected immediately while a selected trip is still attaching its workspace.

Plain-English Summary:
- The left side should now feel much faster because saved trips and past chat messages appear from cache first.
- The board now waits its turn instead of blocking the whole experience.
- Opening an old trip should feel smoother and more understandable because chat appears first, while the right side quietly catches up.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/lib/chat-history-cache.ts`
- `frontend/src/lib/recent-trips-cache.ts`
- `CHANGELOG.md`

## 2026-04-19 - Made New Trip Create A Fresh Workspace In Place

Technical Summary:
- Reworked the chat sidebar `New Trip` action so it no longer relies on the `new` query parameter to force a full workspace bootstrap.
- Added an in-place trip creation flow in the travel workspace that creates a brand-new persisted trip, swaps it into the active workspace immediately, and updates the URL without reloading the entire planner state.
- Disabled the new-trip button while the fresh trip is being created so duplicate trip creation is less likely.

Plain-English Summary:
- Clicking `New Trip` now opens a genuinely new trip instead of tearing everything down and rebuilding the page.
- The planner should feel much smoother because it no longer reloads all the saved-trip and workspace setup just to start a fresh chat.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Reserved The Right Board For Later Itinerary Generation

Technical Summary:
- Simplified the right-side chat board into a single centered helper state instead of rendering live itinerary cards during early planning.
- Tightened the helper copy so it explicitly states that the board is reserved for the later confirmed-trip stage, not for active detail collection.
- Left the chat as the primary planning surface while preserving the previously richer board snapshot in the docs for future restoration.

Plain-English Summary:
- The right side now stays intentionally quiet while the trip is still being discussed.
- Wandrix will collect details in chat first, and only later should that area turn into the real itinerary board.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Saved A Recoverable Snapshot Of The Current Chat UI And Ignored Local Workspace Noise

Technical Summary:
- Added a dated UI snapshot folder under `docs/ui-snapshots/chat-page-2026-04-19/` to preserve the exact `/chat` implementation state for future reference.
- Recorded the purpose and preserved-file list in a snapshot README so the saved chat layout can be traced and recovered later.
- Updated `.gitignore` to ignore local temp logs and repo-local Codex metadata so commit history stays focused on product code rather than machine-specific noise.

Plain-English Summary:
- I saved the current chat-page version so we can always come back to this exact layout later.
- I also stopped local temp files and Codex workspace metadata from cluttering the repo.

Files / Areas Touched:
- `.gitignore`
- `docs/ui-snapshots/chat-page-2026-04-19/README.md`
- `docs/ui-snapshots/chat-page-2026-04-19/files/`
- `CHANGELOG.md`

## 2026-04-19 - Restored The Rich Live Board Layout And Split Board Cards Into A Shared File

Technical Summary:
- Reverted the temporary summary-first board experiment and restored the richer right-side board layout with the itinerary flow, flight card, weather card, hotel panel, and highlight panel.
- Split the rich board cards into a dedicated shared frontend file so the main board component stays smaller and the premium travel modules can be reused or swapped later without bloating the core board file.
- Kept the recent chat-side improvements in place while removing the accidental board regression the user flagged.

Plain-English Summary:
- The board is back to the fuller version with the travel cards you were using before.
- I also pulled those cards into their own file so the main board is cleaner and easier to maintain.
- The chat improvements stay, but the broken board experiment is gone.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`

## 2026-04-19 - Made Chat More Conversational And Added A Visible Thinking State

Technical Summary:
- Updated the assistant chat shell to show a visible thinking state in the composer while a planner turn is running.
- Adjusted the welcome and fallback copy in the chat shell so Wandrix feels more conversational and less like a thin transport wrapper.
- Tightened the planner prompt and response-composition layer so fallback responses are warmer and more planner-like.

Plain-English Summary:
- Wandrix now feels more alive while it is thinking, because the chat shows a small loading state instead of leaving the input area static.
- The assistant's tone is a little more natural and chatty.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`

## 2026-04-19 - Made Chat More Conversational And Turned The Board Into A True Pre-Confirmation Canvas

Technical Summary:
- Updated the assistant chat shell to show a visible thinking state in the composer while a planner turn is running.
- Adjusted the welcome and fallback copy in the chat shell so Wandrix feels more conversational and less like a thin transport wrapper.
- Tightened the planner prompt and response-composition layer so non-LLM fallback responses are warmer and a bit more conversational.
- Changed the right-side board behavior so it no longer shows the hero-and-itinerary layout before the trip is brochure-ready.
- Added a dedicated pre-confirmation board state that uses the whole right pane for planning context, open questions, active goals, module status, and decision options instead of partial itinerary content.

Plain-English Summary:
- Wandrix now feels more alive while it is thinking, because the chat shows a small loading state instead of leaving the input area static.
- The assistant’s tone is a little more natural and chatty.
- The right side now behaves the way you described: before the trip is really confirmed, it works like a planning canvas for choices and missing information instead of pretending the itinerary is already built.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `backend/app/graph/planner/response_builder.py`
- `backend/app/graph/planner/understanding.py`

## 2026-04-19 - Implemented Structured Chat Planner Memory And Lifecycle

Technical Summary:
- Added a new chat-planner source-of-truth document at `docs/chat-planner-spec.md` and linked it from the main repo docs.
- Refactored the backend planner away from the oversized bootstrap node into smaller modules for turn understanding, draft merge, conversation-state merge, provider enrichment, response composition, and runner orchestration.
- Added a persisted `conversation` object to `trip_drafts`, along with typed backend/frontend contracts for planner phases, open questions, decision cards, field memory, option memory, decision history, and turn summaries.
- Updated the conversation route flow so LangGraph state now keeps raw checkpointed messages while the saved trip draft keeps structured planner memory.
- Switched the frontend chat runtime to restore conversation history from the backend checkpoint route, and updated the right-side board to stay summary-first by reading conversation questions, goals, and decision cards from persisted state.
- Added and successfully applied an Alembic migration for the new `trip_drafts.conversation` column, using a safer migration pattern after clearing a stale database lock.

Plain-English Summary:
- Wandrix now has a real planner memory model instead of treating the chat like a loose stream of messages.
- The app can separately remember what the user confirmed, what is still uncertain, what choices are open, and what the next planning step should be.
- The chat, board, and saved trip state are now aligned around the same planner structure, and the new spec is written down so we can keep building consistently.

Files / Areas Touched:
- `backend/app/graph/planner/`
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/schemas/trip_conversation.py`
- `backend/app/schemas/trip_planning.py`
- `backend/app/schemas/trip_draft.py`
- `backend/app/schemas/conversation.py`
- `backend/app/services/conversation_service.py`
- `backend/app/services/trip_service.py`
- `backend/app/services/providers/*.py`
- `backend/app/models/trip_draft.py`
- `backend/app/repositories/trip_draft_repository.py`
- `backend/alembic/versions/1a2b3c4d5e6f_add_conversation_to_trip_drafts.py`
- `frontend/src/types/trip-conversation.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/conversation.ts`
- `frontend/src/lib/api/conversation.ts`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `README.md`
- `docs/architecture.md`
- `docs/decision-log.md`
- `docs/future-improvements.md`
- `docs/chat-planner-spec.md`

## 2026-04-19 - Added File Size Discipline To Project Rules

Technical Summary:
- Updated the repo-wide, backend, and frontend coding rules to explicitly discourage oversized files and require splitting modules by responsibility once they start growing too large.
- This makes the existing “prefer small modules” guidance more concrete and applies it consistently across graph nodes, services, route files, pages, and feature components.

Plain-English Summary:
- Wandrix now has an explicit rule against stuffing too much logic into one file.
- As the project grows, we should split large files earlier so the code stays easier to understand and maintain.

Files / Areas Touched:
- `AGENTS.md`
- `docs/backend-coding-rules.md`
- `docs/frontend-coding-rules.md`

## 2026-04-19 - Forced Backend Config To Prefer Repo Env Values

Technical Summary:
- Updated the backend dotenv loader to use `override=True` so values from the repository root `.env` replace already-set machine or session environment variables during app startup.
- This makes provider configuration deterministic inside Wandrix, especially for `CODEX_LB_API_KEY`, where a stray local shell key could otherwise silently override the project’s intended value.

Plain-English Summary:
- Wandrix will now use the API keys and settings from this project’s `.env` file instead of accidentally picking up a different key from your computer environment.
- That makes debugging much clearer because the app should now use exactly the credentials you expect.

Files / Areas Touched:
- `backend/app/core/config.py`

## 2026-04-19 - Extended Chat API Timeouts For Real Planner Turns

Technical Summary:
- Added per-request timeout support to the shared frontend API client instead of forcing every request through the old short timeout budget.
- Raised the general frontend API timeout to `15s` and gave the trip conversation route a dedicated `45s` timeout so planner turns can survive LangGraph, LLM, and provider latency without the browser aborting the request.
- This keeps a timeout safety net in place for wedged backends while matching the actual runtime cost of a conversation-first planner turn.

Plain-English Summary:
- The chat should stop failing just because the planner takes more than a few seconds to think.
- Wandrix still won’t wait forever if the backend truly hangs, but it now gives real trip-planning turns enough time to finish.

Files / Areas Touched:
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/conversation.ts`

## 2026-04-19 - Removed Stale Local API Fallback And Paused Rich Board Rendering

Technical Summary:
- Simplified the shared frontend API client so it always uses the configured `NEXT_PUBLIC_API_BASE_URL` instead of retrying local calls against `http://127.0.0.1:8001` and caching the last successful local backend in session storage.
- This removes the dev-only port failover path that was causing real `/chat` conversation requests to stick to a dead `8001` backend and surface `failed to fetch` before FastAPI or the LLM were ever reached.
- Switched the right-side trip board into explicit placeholder mode so it no longer renders generated itinerary cards, weather cards, hotel picks, or highlight content while the chat intelligence is being stabilized.

Plain-English Summary:
- Wandrix will stop trying to talk to the wrong local backend port, which should fix the `failed to fetch` crash you were seeing from the starter prompt.
- The trip board now stays honest and minimal for now instead of pretending it already has finalized trip details.

Files / Areas Touched:
- `frontend/src/lib/api/client.ts`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Added Local API Failover For Wedged Dev Backends

Technical Summary:
- Updated the shared frontend API client to put a timeout around browser fetches, retry local requests against `http://127.0.0.1:8001` when the default `http://127.0.0.1:8000` dev backend is hung or refusing connections, and cache the last successful local API base in session storage so later requests do not keep hitting the dead port first.
- This keeps `/chat` and other product surfaces from hanging indefinitely in the browser when a local Windows `uvicorn --reload` process wedges `8000`, while still preserving the configured backend base URL for normal environments.
- Verified the fallback path with the live `/chat` session by observing successful trip list, trip hydrate, and draft hydrate calls on `8001` after failed `8000` attempts.

Plain-English Summary:
- When the normal local backend port gets stuck, Wandrix can now fall back to a second local backend port instead of leaving the app frozen forever.
- That means the chat page can still load saved trips and the live board even if the first dev server is misbehaving.

Files / Areas Touched:
- `frontend/src/lib/api/client.ts`

## 2026-04-19 - Moved Blocking Planner Routes Off The Async Event Loop

Technical Summary:
- Changed the browser-session, trip, conversation, provider-status, and package-generation endpoints from `async def` to synchronous FastAPI route handlers so Starlette runs their blocking SQLAlchemy, planner graph, and provider work in the threadpool instead of on the main event loop.
- Kept lightweight auth and system endpoints async so cheap checks like `/health` and `/api/v1/ping` can stay responsive even while a trip bootstrap or planner turn is taking time in the background.
- This reduces the risk that a single slow trip workspace request will freeze the whole backend process and leave the frontend stuck waiting on pending preflight or trip bootstrap calls.

Plain-English Summary:
- Wandrix should be much less likely to “lock up” when chat is creating trips, loading drafts, or running the planner.
- Slow backend work can still be slow, but it should not take the whole API down with it, so pages and health checks have a better chance of staying responsive.

Files / Areas Touched:
- `backend/app/api/routes/browser_sessions.py`
- `backend/app/api/routes/trips.py`
- `backend/app/api/routes/conversation.py`
- `backend/app/api/routes/providers.py`
- `backend/app/api/routes/packages.py`

## 2026-04-19 - Recovered Chat Bootstrap When Saved Trips Misbehave

Technical Summary:
- Updated the `/chat` workspace bootstrap so the recent-trip sidebar is populated as soon as the saved-trip list loads, instead of waiting for the active workspace hydrate to succeed first.
- Made auto-selection of saved trips more resilient by trying the remembered or recent sessions in order and skipping broken auto-selected workspaces before falling back to a fresh trip when needed.
- Synced the active workspace back into the recent-trip list immediately after bootstrap and draft updates so newly created or repaired trips appear in the sidebar without waiting for a later refresh.

Plain-English Summary:
- The chat page should no longer feel completely blocked just because one saved trip has a bad or incomplete workspace behind it.
- Your recent sessions can keep showing up, and Wandrix has a better chance of opening a working trip or starting a fresh one instead of leaving the chat stranded in a shell state.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`

## 2026-04-19 - Made Planner Merges More Careful Around Confirmed Facts

Technical Summary:
- Updated the graph merge logic so inferred LLM updates only fill open gaps or reaffirm existing values, instead of overwriting already-established trip facts.
- Kept confirmed LLM updates able to replace earlier values when the user clearly changes direction.
- Tightened the extraction prompt so traveler counts are no longer inferred from social phrasing alone, and profile context is treated strictly as soft guidance rather than override material.
- Added planner tests covering inferred-vs-confirmed destination updates, although `pytest` could not be executed locally because it is not installed in the backend virtual environment.

Plain-English Summary:
- Wandrix should now be more careful when the user is still exploring options.
- Soft guesses can help fill blanks, but they should not bulldoze over details the user already made clear.
- If the user clearly changes something, the planner can still update it.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`
- `backend/tests/test_planner_bootstrap.py`

## 2026-04-19 - Persisted Flexible Trip Timing Across Chat, Board, And Brochure

Technical Summary:
- Extended the shared trip-draft contract with `travel_window` and `trip_length` so the planner can persist rough timing like "late September" or "4 or 5 nights" without converting it into fake exact dates.
- Updated the LangGraph bootstrap turn schema and merge logic so flexible timing counts as valid structured timing signal, clears stale exact dates when the user switches back to rough timing, and stops marking the timing fields as missing when that softer signal is already present.
- Wired the saved draft timing through the trip list response and the main timing read surfaces in `/chat`, the trip library, module reference views, the live board, the brochure, and the board sandbox so the UI reflects the persisted draft consistently.

Plain-English Summary:
- Wandrix can now keep rough date clues like "late April" and "3 or 4 nights" in the saved trip instead of dropping them or pretending they are exact travel dates.
- That means the chat, right-hand board, brochure, and saved-trip summaries should all stay closer to what the traveler actually said, especially early in planning when the timing is still flexible.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/schemas/trip.py`
- `backend/app/schemas/trip_draft.py`
- `backend/app/services/trip_service.py`
- `frontend/src/components/brochure/trip-brochure.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/modules/trip-module-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `frontend/src/lib/trip-timing.ts`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/types/trip.ts`

## 2026-04-19 - Persisted Planner Decision Cards On The Live Board

Technical Summary:
- Extended the shared trip-draft status contract with persisted `decision_cards` so the backend planner can store concrete, LLM-generated choice bundles alongside its clarification questions instead of forcing the board to guess from generic frontend fallbacks.
- Updated the LangGraph bootstrap node prompt and structured turn-update schema so ambiguous but high-signal turns can return specific option cards, while also nudging the model to infer obvious adult traveler counts from natural phrasing and to avoid locking exact dates unless the user provided them explicitly.
- Wired the `/chat` board choices rail to render the persisted decision cards from the saved draft first, and refreshed the board sandbox data so the preview path matches the richer planner contract.

Plain-English Summary:
- When a traveler gives Wandrix a messy but useful brief, the right-hand board can now show concrete next-step choices like destination shortlists or trip-length options instead of bland placeholder chips.
- The planner is also better at carrying conversational clues like "me and my sister" into the saved trip state so the live board stays closer to what the chat actually established.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/schemas/trip_draft.py`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/types/trip-draft.ts`

## 2026-04-19 - Stopped Supabase Cookie Writes From Crashing Chat Pages

Technical Summary:
- Updated the shared frontend Supabase server helper so cookie writes are best-effort instead of mandatory when `createServerClient` runs inside a server-rendered page.
- Kept cookie reads intact for auth checks on `/chat` and other protected pages, while allowing route handlers like the auth callback to continue setting cookies where Next.js permits it.
- Removed the localhost-only crash path where `supabase.auth.getUser()` attempted a cookie refresh during render and triggered Next 16's `cookies().set` restriction.

Plain-English Summary:
- The main planner page should stop failing with a server error when Wandrix checks whether you are signed in.
- Protected pages can still read your session normally, and the login callback can keep saving auth cookies without the chat workspace crashing first.

Files / Areas Touched:
- `frontend/src/lib/supabase/server.ts`

## 2026-04-19 - Deferred Sidebar Preference Hydration In Chat Workspaces

Technical Summary:
- Added a shared chat-sidebar preference hook that reads the persisted collapsed state only after mount instead of during the initial render.
- Updated both the main `/chat` workspace shell and the `/board-preview` sandbox to use the shared hook so server-rendered markup starts from the same sidebar shape as the client.
- Prevented the first client render from immediately overwriting the saved sidebar preference before that preference has been loaded from `localStorage`.

Plain-English Summary:
- The planner shell should stop fighting itself on load when the sidebar was previously collapsed.
- Wandrix now restores the sidebar preference after the page mounts, which avoids a hydration mismatch in the chat-and-board layout and should make the workspace feel steadier.

Files / Areas Touched:
- `frontend/src/components/chat/use-chat-sidebar-collapsed-state.ts`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Aborted Stalled Chat Workspace Requests

Technical Summary:
- Added `AbortSignal` support to the shared frontend API client and threaded it through the trip, browser-session, and conversation helpers used by the chat workspace.
- Replaced the old Promise-only timeout helper in the `/chat` workspace bootstrap with an aborting timeout so timed-out saved-trip and workspace requests stop in-flight instead of lingering as zombie fetches.
- Stopped the fresh-trip bootstrap path from waiting on the recent-trips sidebar before attaching the main planner workspace, and added an aborting timeout for the sidebar refresh as well.

Plain-English Summary:
- The chat workspace should no longer sit on a never-ending loading state when a trip boot request stalls.
- Wandrix now cuts off stuck startup requests more cleanly and prioritizes opening the main planner before worrying about refreshing the saved-trip rail.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/trips.ts`
- `frontend/src/lib/api/browser-sessions.ts`
- `frontend/src/lib/api/conversation.ts`

## 2026-04-19 - Made Chat Bootstrap Recover From Slow Trip Lists

Technical Summary:
- Reworked the `/chat` workspace bootstrap so the main planner no longer stays blocked behind the sidebar trip-list fetch.
- Added a timeout-limited initial trip-list load, support for restoring the last active trip when available, and a background recent-trips refresh after the workspace comes up.
- Kept recovery scoped to the chat workspace so a slow or wedged recent-trip request can degrade the sidebar without freezing the assistant pane and live board bootstrap.

Plain-English Summary:
- The chat workspace should feel less fragile now when the saved-trip rail is slow.
- Instead of letting one trip-list request freeze the whole planning screen, Wandrix now tries to get the trip workspace attached first and fills the sidebar in afterward.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`

## 2026-04-19 - Added Planner Clarification Metadata And Softer Ambiguity Fallbacks

Technical Summary:
- Extended the trip-draft status contract with `confirmed_fields`, `inferred_fields`, and `open_questions` so the planner can persist which details are firm, which remain soft, and which follow-up questions still need answers.
- Updated the LangGraph bootstrap node prompt and fallback reply builder so ambiguous turns now bias toward human-readable clarification questions instead of raw missing-field names, while still proposing a provisional trip direction when enough signal exists.
- Added targeted backend verification coverage for the new clarification behavior and updated frontend mock/type contracts to match the richer trip-draft status shape.

Plain-English Summary:
- The planner now keeps better track of what it really knows versus what it is only guessing.
- When a user is vague, Wandrix should sound more like a careful travel agent: it can start sketching the trip direction, keep uncertain details soft, and ask cleaner follow-up questions instead of dumping technical field names.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/schemas/trip_draft.py`
- `backend/tests/test_planner_bootstrap.py`
- `backend/tests/test_trip_draft_schema.py`
- `frontend/src/types/trip-draft.ts`
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Registered The Wandrix Automation In Codex's Global Automation Folder

Technical Summary:
- Copied the Wandrix automation config into `C:\\Users\\kvija\\.codex\\automations\\half-hourly-planner-improvements\\automation.toml`, matching the location already used by the working ADTPG automation.
- This complements the repo-local automation file so the Codex app can discover the automation from its global automation registry as well.

Plain-English Summary:
- The automation is no longer only sitting inside the Wandrix repo.
- I also registered it in the same Codex-wide automation folder that your other visible automation already uses, which gives the app a much better chance of showing it in the Automations tab.

Files / Areas Touched:
- `C:\\Users\\kvija\\.codex\\automations\\half-hourly-planner-improvements\\automation.toml`

## 2026-04-19 - Added The Missing Codex Environment File For Wandrix

Technical Summary:
- Added `.codex/environments/environment.toml` so the Wandrix workspace now has the same Codex environment structure as the ADTPG project that already shows automations correctly in the app.
- This should help the Codex app recognize Wandrix as a fully indexed local workspace instead of only seeing the automation file in isolation.

Plain-English Summary:
- I added the missing workspace metadata file that the other working project already had.
- If the automation tab was ignoring Wandrix because the workspace did not look fully registered, this should improve that.

Files / Areas Touched:
- `.codex/environments/environment.toml`

## 2026-04-19 - Aligned Wandrix Automation Metadata With Existing Codex Pattern

Technical Summary:
- Updated the Wandrix automation config to include `created_at` and `updated_at` metadata fields so its shape matches the existing Codex automation file already working in the ADTPG project.
- This change is intended to improve automation discovery in the Codex app automation index without changing the automation behavior itself.

Plain-English Summary:
- I adjusted the Wandrix automation file to look more like the one that already shows up correctly in your other project.
- If the Codex app was skipping it because the file looked incomplete, this should make it easier for the app to detect.

Files / Areas Touched:
- `.codex/automations/half-hourly-planner-improvements/automation.toml`

## 2026-04-19 - Added The Wandrix Half-Hourly Automation Draft

Technical Summary:
- Added a built-in Codex automation config under `.codex/automations/half-hourly-planner-improvements/automation.toml`.
- Set the automation to run every 30 minutes using a cron-style RRULE and included an explicit self-skip rule if another run is already in progress.
- Encoded the key Wandrix constraints into the prompt: chat-first planning, no deterministic parsing, board updates from chat-driven draft state, Chrome DevTools MCP live testing, random scenario coverage, performance checks, changelog updates, and push-on-meaningful-change to `automation-runs`.
- Pointed the automation toward the planner roadmap and `/board-preview` as the target board design direction.

Plain-English Summary:
- We now have a real Wandrix automation draft instead of just talking about it.
- The automation is set up to wake up every 30 minutes, avoid overlapping itself, work on the planner in small safe steps, test the app live, and push meaningful progress to the `automation-runs` branch.
- It is also explicitly told not to drift back into deterministic parsing and to keep improving the conversational travel-agent experience first.

Files / Areas Touched:
- `.codex/automations/half-hourly-planner-improvements/automation.toml`

## 2026-04-19 - Added Minimal Itinerary Scrollbars And Travel-Type Icons

Technical Summary:
- Added a dedicated minimal scrollbar style for the itinerary panel so the internal scroll feels lighter and less intrusive than the default workspace scroll.
- Introduced small timeline item icons for flights, hotels, meals, weather, transfers, and activities directly inside each itinerary row.
- Kept the itinerary structure compact so the live board reads more like a styled travel plan than a generic card list.

Plain-English Summary:
- The itinerary should feel cleaner now because its scrollbar is much less noticeable.
- Each itinerary item also has a small travel icon, so flights and other trip moments are easier to scan quickly.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/app/globals.css`

## 2026-04-19 - Replaced The Old Right Rail With Travel Modules And A Scrollable Itinerary

Technical Summary:
- Removed the leftover right-rail panels for trip status, recent changes, and trip snapshot.
- Kept the board focused on travel-specific content by dedicating the right support column to flights, weather, stay details, and highlights.
- Reworked the itinerary into a scrollable day-grouped layout instead of page expansion, closer to an editorial travel timeline.

Plain-English Summary:
- The old dashboard-style side panels are gone.
- The board now uses that space for actual trip planning content, and the itinerary scrolls inside its own section instead of stretching the whole page.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Rebuilt The Itinerary Section Into A Planner Split Layout

Technical Summary:
- Reworked the board view under the hero into a two-column planning layout with itinerary flow on the left and live support modules on the right.
- Added an expand/collapse control for the itinerary so longer trip flows can be revealed without forcing the board into a permanently long stack.
- Moved flights, weather, stay details, and highlights into a dedicated right-side support column beside the itinerary flow.

Plain-English Summary:
- The itinerary area should make more sense now.
- The trip flow lives on the left, and the supporting travel details like flights and weather sit on the right where they are easier to scan.
- You can also expand the itinerary when the planner has more items to show.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Removed The Hero Tags And Simplified The Remaining Details

Technical Summary:
- Removed the remaining style tags from the hero summary area.
- Replaced the larger boxed date and party cards with a simpler inline detail treatment so they occupy less space and feel less congested.
- Removed the unused hero styles prop after simplifying the summary block.

Plain-English Summary:
- The top-right hero details are cleaner now.
- The tags are gone, and the date and party info no longer sit inside oversized boxes that made the area feel cramped.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Removed The Trip Tone Card From The Hero

Technical Summary:
- Removed the trip-tone detail card from the hero summary block while leaving the lighter supporting style chips underneath.
- Kept the route and party details as the main structured summary items beside the destination image.

Plain-English Summary:
- The hero summary is cleaner now because the extra trip-tone card is gone.
- The top of the board should feel less busy while still keeping the style tags available lower down.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Simplified The Hero Summary Block

Technical Summary:
- Reduced the hero height so the board starts with a lighter visual footprint.
- Removed helper text from the hero detail area, dropped the budget card entirely, and switched the travel window to a shorter date-range format.
- Kept the route, party, and trip-tone details, but made the summary block more compact so it supports the board instead of dominating it.

Plain-English Summary:
- The hero is smaller now and the details beside it are much simpler.
- Dates are shown in a short format, the party section is cleaner, and the budget is gone so the top of the board feels less crowded.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Removed The Inner Board Container To Free More Width

Technical Summary:
- Removed the centered max-width wrapper from the live trip board content area.
- Reduced the outer board padding slightly so the hero and supporting sections can use more of the available workspace width.

Plain-English Summary:
- The board was still sitting inside an extra container, which made it feel narrower than it needed to be.
- I removed that extra limit so the hero and the rest of the board can stretch out more naturally.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Increased The Board Share After The Hero Detail Pass

Technical Summary:
- Rebalanced the `/chat` and `/board-preview` workspace grids so the right-side board regains more horizontal share.
- Increased the board column both in the normal desktop layout and in the collapsed-sidebar layout, keeping the chat column slimmer so the board stays visually dominant.

Plain-English Summary:
- The board got too small in the last pass, so I gave it more space again.
- This keeps the cleaner hero details while making the overall board feel larger and more important in the layout.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Refined The Hero Trip Details Into A Real Summary Block

Technical Summary:
- Reworked the detail area beside the board hero so it no longer uses four equal stat tiles.
- Added a stronger route summary card, then grouped the supporting details into smaller icon-led cards for dates, party size, trip tone, and budget.
- Moved the trip styles into supporting chips so the panel reads more like one travel summary and less like a generic dashboard stat grid.

Plain-English Summary:
- The information beside the destination image should feel more polished now.
- Instead of looking like four random boxes, it now reads as a proper trip summary with the route first and the rest of the trip details supporting it.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Added A Collapsible Chat Sidebar

Technical Summary:
- Added a collapsible state to the shared chat sidebar and reused it in both the real `/chat` workspace and the `/board-preview` sandbox.
- Persisted the sidebar state in local storage so collapsing it during review or planning stays sticky between pages.
- Introduced a compact collapsed sidebar mode with icon actions and trip monograms, and widened the board share of the layout when the sidebar is collapsed.

Plain-English Summary:
- You can now collapse the left sidebar while chatting to give the board more space.
- The collapsed state carries over between the real chat page and the preview page, so it feels like one consistent workspace instead of a one-off trick.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Relaxed The Board Layout And Quieted The Preview Shell

Technical Summary:
- Reduced the chat-column share again in both the real `/chat` workspace and the `/board-preview` shell so the board can take more visual priority.
- Rebuilt the preview shell header into a compact scenario switcher and simplified the mocked conversation blocks so the board is not competing with a large fake chat layout during design review.
- Relaxed the board internals by using a later breakpoint for split module layouts and the right-side rail, lowering heading intensity, and replacing heavier panel treatments with calmer bordered surfaces.

Plain-English Summary:
- The board should feel more open now instead of squeezed between too many competing sections.
- I also made the preview page quieter, so it is easier to judge the board itself rather than being distracted by an overly busy fake chat area.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Slimmed The Chat Column To Give The Board More Room

Technical Summary:
- Reduced the middle chat-column share in both the real `/chat` workspace grid and the `/board-preview` shell so the right-side board gets more horizontal room.
- Tightened the assistant message container widths in the real chat surface and in the preview shell so the center column feels visually slimmer instead of only changing the parent grid math.
- Kept the sidebar width unchanged, so the adjustment is focused on the relationship between the conversation column and the live board.

Plain-English Summary:
- The chat area is a bit smaller now, and the board has more room to breathe.
- This should make the right side feel less cramped and help the board look more intentional instead of squeezed beside an oversized chat column.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`

## 2026-04-19 - Board Preview Now Shows Sidebar And Chat Context

Technical Summary:
- Reworked the `/board-preview` sandbox so it no longer shows the board in isolation.
- Wrapped the sample board in the real three-column product proportions: the shared chat sidebar on the left, a mocked middle conversation column, and the live board on the right.
- Added sample recent trips and a lightweight mocked conversation so the board can be judged against the actual chat-shell width and layout constraints.

Plain-English Summary:
- The preview page should make a lot more sense now because you can see the board with the sidebar and chat around it.
- This gives a much more honest view of how wide the board really is inside the product and makes it easier to judge whether the hero and layout feel right.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-sandbox.tsx`

## 2026-04-19 - Board Hero Made Smaller And Swapped To Live Destination Imagery

Technical Summary:
- Reworked the trip-board hero section so it fits the narrower chat-side board better, using a more compact split layout instead of the previous oversized full-bleed banner treatment.
- Replaced the washed visual treatment with a visible live destination image source and simplified the hero typography so it reads more clearly during design review.
- Kept the supporting trip stats in the hero, but tightened them into a smaller card grid that is easier to judge in the actual `/chat` layout.

Plain-English Summary:
- The top of the board should make more sense now.
- It is smaller, clearer, and uses a real visible destination image so you can judge the direction properly instead of trying to imagine it through a tinted background.
- I also toned down the hero typography so it does not feel as overdesigned while we keep refining the board.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Board Restyled Toward Editorial Travel Layout

Technical Summary:
- Rebuilt the live trip board component around an editorial layout inspired by the Stitch travel-board reference instead of the earlier stacked inspection panel.
- Added a wide hero destination banner, a left-led itinerary flow, compact logistics modules, and a cleaner right-side rail for trip status, recent changes, and trip snapshot details.
- Kept the board/selections split, but reframed it visually so the itinerary view feels like the main artifact and the choices view feels like a supporting planning surface.

Plain-English Summary:
- The board should feel much more like a polished travel planner now and much less like a debug panel.
- It now has a stronger visual hierarchy: big destination at the top, itinerary flow as the main story, and smaller side modules for status and supporting trip details.
- The goal was not to copy the Stitch design exactly, but to get much closer to that level of visual quality and structure.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`

## 2026-04-19 - Added A Dedicated Planner Improvement Plan

Technical Summary:
- Added a new planning document that organizes Wandrix improvements into clear phases before recurring Codex automation is introduced.
- Separated safe automation work from higher-risk work that still needs human judgment.
- Defined the recommended first automation backlog around planner intelligence, then personalization, then structured planning polish.
- Linked the new planning document from the README so it becomes part of the repo's working documentation set.

Plain-English Summary:
- We now have a proper improvement roadmap for Wandrix instead of a loose list of ideas.
- This gives future automation a clear mission and keeps it focused on the right things in the right order.
- The plan says we should make the planner smarter first, then more personal, and only after that spend more time on polish and export work.

Files / Areas Touched:
- `docs/planner-improvement-plan.md`
- `README.md`

## 2026-04-19 - Board Preview Lab And Per-Trip Chat History Restore

Technical Summary:
- Added a new authenticated `/board-preview` route with a client-side sandbox that renders the live trip board against several realistic sample trip drafts for fast visual iteration.
- Introduced per-trip local chat history persistence in the assistant-ui layer by seeding `useLocalRuntime` with saved thread messages and syncing the current thread back into local storage as the conversation changes.
- Added a small restoration state so switching back into an existing trip no longer mounts the chat runtime before its saved message history is ready.
- Updated route documentation to include the new board-preview lab page.

Plain-English Summary:
- There is now a dedicated page where you can review the right-side trip board with sample travel scenarios, without needing to talk to the planner first.
- I also fixed the main reason saved chats looked empty: the chat thread now restores the most recent local message history for each trip when you reopen it.
- This makes it much easier to iterate on the board design and to come back to an in-progress trip without the chat looking blank.

Files / Areas Touched:
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-sandbox.tsx`
- `frontend/src/app/board-preview/page.tsx`
- `README.md`

## 2026-04-19 - Locked The Repo Against Deterministic Planner Parsing

Technical Summary:
- Removed the last regex-based parsing utility from the backend flight provider adapter and replaced it with straightforward format handling that does not depend on planner-side regex extraction.
- Updated the repo agent rules and backend coding rules so deterministic planner parsing is no longer described as an acceptable temporary fallback.
- Updated the future-improvements roadmap so planner intelligence work now points only toward stronger structured LLM behavior and clarification flows instead of any return to regex or keyword parsing.

Plain-English Summary:
- Wandrix is now more consistent about this rule: it should not go back to guessing trip details with regex or keyword parsing.
- I also updated the written project rules so future work does not quietly bring that behavior back.

Files / Areas Touched:
- `backend/app/services/providers/flights.py`
- `AGENTS.md`
- `docs/backend-coding-rules.md`
- `docs/future-improvements.md`

## 2026-04-19 - Removed Generated Planner Placeholder Module Data

Technical Summary:
- Removed the bootstrap node's generated placeholder outputs for flights, hotels, weather, and activities.
- Updated module-output building so those sections now rely on live provider enrichment or previously saved structured data instead of backend-invented filler content.
- Removed unused helper functions that only existed to support fabricated itinerary blocks and placeholder scheduling.

Plain-English Summary:
- The planner is now more honest about what it really knows.
- Instead of inventing fake flight blocks, hotel stays, weather cards, or activity ideas just to fill the board, Wandrix now shows real provider data when available and otherwise leaves those sections open until better information exists.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-19 - Profile Page and Dialog-Based Onboarding

Technical Summary:
- Created a dedicated profile page component (`profile-page.tsx`) that always shows a clean settings view with avatar, name, email, and editable travel defaults — no longer conditionally showing the onboarding setup flow.
- Created a multi-step onboarding dialog component (`onboarding-dialog.tsx`) with a wizard flow (Welcome → Profile → Home base → Preferences → Location) that opens automatically only when a user signs up via `?onboarding=1` query parameter.
- Updated the auth-shell signup redirect to route new users to `/chat?onboarding=1` instead of `/profile`, so onboarding happens as a dialog overlay on the chat page.
- Simplified the user account popover to show a single "Profile & travel defaults" link instead of two separate links.
- The old `profile-onboarding.tsx` setup/settings dual-mode component is no longer used by the profile page route.

Plain-English Summary:
- Clicking "Profile" in the navbar now opens a proper profile page showing your avatar, name, email, and travel defaults — not the onboarding wizard.
- Onboarding only happens once, right after signup, as a friendly step-by-step dialog overlay on the chat page. Users can skip it and come back to set things up from their profile later.
- The profile page always looks the same whether you're a new or returning user.

Files / Areas Touched:
- `frontend/src/components/profile/profile-page.tsx` (new)
- `frontend/src/components/profile/onboarding-dialog.tsx` (new)
- `frontend/src/app/profile/page.tsx`
- `frontend/src/app/chat/page.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`

## 2026-04-19 - Account Menu Cleanup And One-Time Account Setup Flow

Technical Summary:
- Replaced the inline account popover with a cleaner dropdown menu built on shared Radix dropdown primitives, while keeping the signed-in name and avatar visible in the top navigation.
- Changed the account menu so `Edit profile` now routes to the dedicated `/profile` page instead of opening an inline editor inside the header control.
- Reworked the `/profile` experience into two modes: first-run account setup when required fields are still missing, and a normal profile/defaults edit page after setup is complete.
- Updated signup copy and routing language so the flow now talks about account setup instead of planner onboarding, and refreshed route documentation to match.

Plain-English Summary:
- The account control in the header is cleaner now and behaves more like a normal product menu.
- Editing your profile now happens on its own page instead of inside a cramped dropdown.
- First-time users still get guided through the basic setup once, but after that the same page behaves like a regular profile settings page instead of repeating onboarding forever.

Files / Areas Touched:
- `frontend/src/components/animate-ui/components/radix/dropdown-menu.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/profile/profile-onboarding.tsx`
- `frontend/src/app/profile/page.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `frontend/package.json`
- `frontend/package-lock.json`
- `README.md`

## 2026-04-19 - Chat Board Redesigned Into Live Board And Selections Views

Technical Summary:
- Rebuilt the right-side chat board into a fuller visual planning surface with a destination hero, form-like trip setup fields, a grouped timeline, flight and hotel panels, activity highlights, and weather cards.
- Added a second board tab for `Selections`, using current draft state and missing fields to present pending user decisions and active planning signals in a clearer UI.
- Removed the old bottom `Prompt the board directly` panel from the chat workspace so the live board can use the full height and act as the main right-hand planning surface.

Plain-English Summary:
- The right side of chat should now feel much more like a real trip board instead of a debug panel.
- It has a proper trip overview, timeline-style flow, travel details, and a separate place for choices the agent may need from the user.
- I also removed the old extra prompt panel at the bottom so the board has room to breathe.

Files / Areas Touched:
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`

## 2026-04-19 - Chat Now Reads Saved Profile Context

Technical Summary:
- Extended the conversation request contract so the frontend can send saved profile/default context into the backend turn processor.
- Added profile context to the LangGraph state and prompt construction so the planner can treat saved defaults as soft guidance during extraction and reply generation.
- Updated the assistant welcome state to read saved profile values from local storage and use them for a more personal greeting and smarter starter suggestions.

Plain-English Summary:
- The chat now knows more about the user before the first message.
- Wandrix can greet the traveler more personally and start from saved defaults like home airport or currency instead of acting like every conversation is completely blank.
- Those defaults are still soft context only, not hard rules for the trip.

Files / Areas Touched:
- `backend/app/schemas/conversation.py`
- `backend/app/graph/state.py`
- `backend/app/graph/nodes/bootstrap.py`
- `backend/app/services/conversation_service.py`
- `frontend/src/types/conversation.ts`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`

## 2026-04-19 - Profile Page Expanded Into Full Inline Settings Form

Technical Summary:
- Rebuilt the live `/profile` route into a detailed inline settings page instead of relying on separate edit dialogs for each section.
- Added fuller profile data capture fields including first name, last name, home address details, home airport, currency, preferences, and location-assistance controls.
- Kept Supabase metadata updates for core identity fields while continuing to store broader profile/default values locally for the current product stage.
- Simplified the account menu label back to `Profile` so it matches the new page's broader role.

Plain-English Summary:
- The profile page now feels like a real settings page instead of a collection of popups.
- You can enter more complete information there, including your name and home address details, without opening little dialogs for everything.
- The menu label is simpler now too, so `Profile` takes you to the full profile page.

Files / Areas Touched:
- `frontend/src/components/profile/profile-page.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `README.md`

## 2026-04-19 - Account Trigger Surface Flattened Into Navbar

Technical Summary:
- Removed the white background from the account trigger so it now sits on a transparent surface inside the navbar.
- Kept the interaction affordance through hover-only tint and border feedback instead of a persistent chip-style background.

Plain-English Summary:
- The account control should look less boxy now.
- Instead of sitting on a white pill-like background, it blends into the navbar until you hover it.

Files / Areas Touched:
- `frontend/src/components/auth/user-account-popover.tsx`

## 2026-04-19 - Navbar Tint And Cleaner Account Trigger Surface

Technical Summary:
- Removed the blue-tinted background treatment from the account trigger so the control sits on a neutral surface again.
- Added subtle shared navbar tint tokens in the global theme and applied them to the top navigation background.
- Kept the accent language present in the header without letting the account component carry the full color burden.

Plain-English Summary:
- The account control should look cleaner now because it no longer has that blue background behind it.
- The navbar itself has a very light theme tint now, so the top of the app feels less plain without becoming loud.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`

## 2026-04-19 - Account Control Re-Aligned With App Accent Colors

Technical Summary:
- Removed the temporary account-specific red accent tokens from the global theme.
- Reworked the account trigger so it now uses the shared accent-soft surface and the same accent gradient language already used by primary buttons.
- Kept the account control visually distinct without introducing a separate color system that could drift from the rest of the product.

Plain-English Summary:
- The account control now matches the app better.
- Instead of using a separate red look, it now feels like part of the same Wandrix button/color family you already see elsewhere in the interface.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `frontend/src/components/auth/user-account-popover.tsx`

## 2026-04-19 - Removed Heuristic Trip Extraction From The Planner Path

Technical Summary:
- Removed the deterministic regex and keyword extraction branch from the LangGraph bootstrap node so trip understanding now flows through structured LLM output instead of mixed parsing strategies.
- Simplified the turn bootstrap so it starts from the persisted trip configuration, applies validated model updates, and no longer mutates trip fields through local regex matches.
- Rewrote the non-LLM fallback response so Wandrix now asks for clarification instead of pretending it safely updated fields from an ambiguous message.

Plain-English Summary:
- The planner is no longer using hidden text-matching rules to guess route, budget, traveler counts, or modules.
- That means Wandrix should be less brittle and less likely to silently lock the wrong details just because a message happened to match a pattern.
- If the model cannot confidently move the trip forward, the assistant will now ask for clearer detail instead of acting like it understood more than it did.

Files / Areas Touched:
- `backend/app/graph/nodes/bootstrap.py`

## 2026-04-19 - Account Menu Positioning And Hover Polish

Technical Summary:
- Adjusted the account dropdown menu alignment so it anchors more naturally from the account control instead of feeling offset to the wrong side.
- Improved the trigger and item hover states with clearer surface and border feedback.
- Renamed the main account action from `Edit profile` to `Profile` to keep the menu copy simpler.
- Removed the duplicated email line from the header trigger so the compact account control only shows the user's name, while the dropdown still carries the fuller account context.

Plain-English Summary:
- The account menu should now feel more neatly attached to the avatar/name control.
- Hover states are cleaner and easier to read.
- The menu wording is simpler, so `Profile` now takes you to the profile page.
- The top bar also looks less repetitive now because the email is no longer repeated outside the dropdown.

Files / Areas Touched:
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/animate-ui/components/radix/dropdown-menu.tsx`

## 2026-04-18 - Sidebar Session Loading Stabilized And Brochure Terminology Clarified

Technical Summary:
- Hardened backend Supabase token verification by making the auth check's outbound HTTPX call ignore environment proxy settings, which resolved the hanging `GET /api/v1/trips` path during local browser bootstrapping.
- Extended the trip list contract with `brochure_ready` so the frontend can distinguish all persisted trips from brochure-ready outcomes.
- Updated the chat sidebar footer to point to brochure-ready trips specifically, and rewrote the trip library wording/filtering so "brochure" terminology now refers to finished brochure-style outputs instead of the full trip history.
- Revalidated the backend with a compile check, revalidated the frontend with ESLint and a production Next.js build, and confirmed the fix in Chrome DevTools by reloading `/chat` until the sidebar trip requests completed successfully.

Plain-English Summary:
- The reason you sometimes saw no sessions at all was that the backend trip-list request was hanging during auth verification, so the chat page never received any session data to render.
- That path is now stable again, and I verified in the browser that recent sessions load back into the sidebar.
- I also cleaned up the wording so "Brochures" now means the finished brochure-style trips, while the session list on the left remains the live chat history.

Files / Areas Touched:
- `backend/app/core/auth.py`
- `backend/app/schemas/trip.py`
- `backend/app/services/trip_service.py`
- `frontend/src/types/trip.ts`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/trips/trip-library.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Chat Boot Flow Reuses Latest Trip Instead Of Always Creating One

Technical Summary:
- Updated the `/chat` workspace boot flow so it loads the latest saved trip by default when there is no explicit `trip` query parameter, instead of always creating a brand-new trip record on page entry.
- Kept explicit new-session behavior intact by continuing to create a fresh trip only when the `new` query flag is present or when the user has no saved trips yet.
- Increased the recent-trip fetch window used by the chat workspace sidebar boot path so the left rail has more prior sessions available to display.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The app was creating a new blank trip too often, which made it feel like your previous sessions were not loading properly in the sidebar.
- Now the chat page reopens your latest real trip unless you explicitly start a new one, so the sidebar history should behave much more like you expect.

Files / Areas Touched:
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Sidebar: Restore New Trip Button, Saved Trips & Show More

Technical Summary:
- Restored the full-width accent "New Trip" button at the top of the sidebar (compact `h-9` variant).
- Added `visibleCount` state and `INITIAL_VISIBLE`/`LOAD_MORE_COUNT` constants (both 5) to progressively reveal trip items instead of rendering all at once.
- Added a "Show more" button with `ChevronDown` icon that appears only when there are hidden items.
- Search resets `visibleCount` back to `INITIAL_VISIBLE` on every keystroke.
- Renamed footer link from "All trips" to "Saved Trips" with the `BookOpen` icon.

Plain-English Summary:
- The sidebar now shows the "New Trip" button again, only displays 5 trips at a time with a "Show more" option, and has a clear "Saved Trips" link at the bottom.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Minimal Sidebar Layout Redesign

Technical Summary:
- Replaced the large accent-colored "New Trip" button with a compact icon-only `+` button in the header row.
- Removed the verbose "Recent chats" section header and description; replaced with a clean uppercase "Trips" label.
- Added a search icon inside the search input for better affordance; tightened input padding.
- Simplified trip list items: removed the wrapping `<div>`, reduced to single `<button>` per item, collapsed three metadata lines into one, tightened vertical spacing (`space-y-0.5`, `py-2`).
- Replaced hardcoded Slate dot colors with theme-aware `--sidebar-shell-border` / `--sidebar-muted-text` tokens.
- Added a persistent "All trips" footer link with a top border separator, replacing the inline "Saved" link.
- All colors still reference existing `--sidebar-*` CSS custom properties.

Plain-English Summary:
- The sidebar now looks much cleaner and more minimal — a small plus icon instead of a big blue button, a compact search bar with an icon, tighter trip cards, and a subtle footer link to the full trip library.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Removed Duplicate Sidebar Theme Controls

Technical Summary:
- Removed the left-sidebar footer controls for accent and light/dark mode so theme switching is owned only by the shared top navigation.
- Deleted the now-unused sidebar imports and kept the rest of the recent-chat rail layout unchanged.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The sidebar no longer shows the extra theme and color controls.
- Theme switching now only lives in the top navbar, which keeps the UI cleaner and avoids duplicate controls.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Middle Chat Column Matched More Closely To Legacy Workspace

Technical Summary:
- Refined the assistant-driven middle chat column so it follows the old ADTPG conversation shell more literally while keeping the current assistant-ui and backend conversation bridge intact.
- Added shared chat-shell tokens and scrollbar styling in `globals.css`, applied the workspace shell to the `/chat` page, and aligned the middle column container to the imported chat surface instead of the earlier generic shell colors.
- Removed the extra Wandrix-specific chat header/status block, tightened the empty-state layout, preserved the legacy-style message bubble treatment, and switched the composer to assistant-ui's real cancel control instead of the temporary placeholder button.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The center chat area should now feel much closer to the old app instead of still looking like a newer Wandrix panel.
- I kept all the current chat functionality working, but made the visuals and structure read more like the scrapped project you wanted copied.
- The biggest changes were removing the extra top chrome, tightening the starter state, and making the message/composer area behave like one continuous chat pane.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `frontend/src/app/chat/page.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Recent Chat Row Styling Matched To Legacy Shelf

Technical Summary:
- Restyled the chat sidebar's recent-session rows to follow the older embedded conversation-shelf pattern more literally.
- Replaced the custom Wandrix list treatment with compact rounded rows, active-state surface highlighting, a leading status dot, smaller title/meta typography, and simplified metadata lines.
- Preserved the current trip-based navigation and search behavior while switching the presentation to the legacy row style.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The recent chats in the sidebar should now look much closer to the old app's list style.
- This was a visual refinement only; the same sessions and trip-opening behavior still work underneath.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Integrated Three-Section Chat Workspace Shell

Technical Summary:
- Refactored the `/chat` workspace layout to use a continuous three-column page shell for sidebar, conversation, and trip-board areas instead of padded floating panels.
- Removed the outer rounded card treatment from the left rail, assistant column, and trip-board column so the workspace reads as shared page sections separated by borders.
- Simplified the sidebar structure further by flattening recent-session presentation into a more list-like rail and keeping saved-trip access inline with the recent-chat header.
- Preserved existing planner functionality, including `new` query resets, `trip` query session selection, backend chat wiring, draft updates, and the right-rail package form.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The chat workspace now behaves more like one real page split into three sections, instead of three separate rounded boxes.
- The sidebar is now part of the page itself, and the middle and right areas follow the same structure.
- The planner behavior underneath is still the same; this was a layout and styling pass, not a feature rewrite.

Files / Areas Touched:
- `frontend/src/app/chat/page.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Sidebar Simplification And Recent Chat List Alignment

Technical Summary:
- Removed the extra left-rail navigation items for Home, Flights, Hotels, and Activities from the chat workspace sidebar.
- Flattened the sidebar structure by removing the separate saved-trips card and folding saved-trip access into the recent-chat header actions.
- Restyled the recent session items from boxed cards into a tighter list treatment while preserving the existing `trip` query navigation, search filtering, and new-chat reset behavior.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The chat sidebar is cleaner now and no longer shows the extra menu items you wanted removed.
- Saved trips are still accessible, but they are no longer in their own chunky panel.
- The recent chats should now feel much closer to the old list-style sidebar while still using Wandrix's current functionality.

Files / Areas Touched:
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Left Sidebar Visual Port For Chat Workspace

Technical Summary:
- Reworked the Wandrix chat workspace sidebar to follow the older ADTPG left-rail styling more closely, including the neutral shell surface, menu links, prominent top action, saved-trips card, recent-trip list styling, and footer controls.
- Kept the current Wandrix sidebar behavior intact by preserving the existing `new` query reset flow, `trip` query selection flow, recent-trip search filtering, and saved-trips route wiring.
- Added the sidebar design tokens needed to support the imported shell/surface/active states in both light and dark mode.
- Reused the newly added theme and accent pickers in the sidebar footer so the left rail behaves more like the old product without introducing separate state paths.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The left sidebar in the chat workspace now looks much closer to the old project instead of the earlier plain panel.
- I kept the current Wandrix functionality underneath it, so selecting trips, starting a new chat, and opening saved trips should still work the same way.
- This was a styling and structure port for the sidebar, not a rewrite of the planner logic.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Fixed Theme Toggle Token Wiring

Technical Summary:
- Replaced the frontend dark theme token override from a `prefers-color-scheme` media query with a `.dark` class override in `globals.css`.
- Aligned the global token system with the existing client-side theme toggle and layout boot script, both of which already control the `dark` class on the root element.
- This makes manual light/dark switching deterministic instead of depending on the operating system preference after page load.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- Light mode and dark mode should now actually switch when you use the navbar toggle.
- The bug was that the toggle changed the class, but the app colors were still listening to the OS theme rule instead of that class.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-18 - Literal Home Page Port And Theme Controls

Technical Summary:
- Replaced the Wandrix landing page implementation with a near-literal port of the ADTPG home page structure, including the centered hero layout, CTA treatment, feature cards, Lucide icons, and animated beam background behavior.
- Added a reusable `BackgroundBeamsWithCollision` UI component backed by the `motion` package so the landing page can match the old animated background treatment instead of relying on approximate local gradients.
- Added client-side theme initialization in the root layout plus reusable navbar controls for light/dark mode and accent palette switching, using localStorage-backed state and CSS variable updates.
- Updated shared theme tokens so the imported accent picker can drive `--accent`, `--accent2`, `--accent-foreground`, and the dark-mode class correctly across the app shell.
- Added the required frontend dependencies for the ported UI pieces and revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The home page now follows the old ADTPG version much more directly instead of just borrowing pieces from it.
- The app also now has the theme toggle and accent picker you asked for, so light/dark mode and color themes can be changed from the navbar.
- This pass was about making the imported frontend feel like the old project again, not just “similar.”

Files / Areas Touched:
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/page.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/src/components/ui/background-beams-with-collision.tsx`
- `frontend/src/components/ui/theme-toggle.tsx`
- `frontend/src/components/ui/accent-picker.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Literal Navbar White Surface Alignment

Technical Summary:
- Reworked the shared top navigation classes to follow the ADTPG reference more literally, including a white `bg-background` header surface, reference-style nav-link states, and removal of the tinted glass pill wrapper around the desktop nav.
- Updated the signed-in navbar controls to sit on the same neutral surface language instead of the earlier translucent blue-tinted treatment.
- Removed the home and auth page atmospheric beam overlays and glass-card styling so the navbar now sits over a plain white page surface instead of inheriting color from the content underneath.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The navbar should now actually read as white, like the reference, instead of a tinted overlay.
- I also removed the extra page effects that were making the whole top of the app feel different from the old project.
- This was a visual alignment pass, not a routing or auth logic change.

Files / Areas Touched:
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/components/auth/sign-out-button.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `CHANGELOG.md`

## 2026-04-18 - Removed Warm Tint From Full-Page Surfaces

Technical Summary:
- Removed the remaining yellow-warm color mixing from the shared landing and auth full-page background treatments in `globals.css`.
- Updated the hero atmosphere gradients, animated beam columns, beam flares, and gradient text treatment to stay in the blue-and-white palette instead of blending toward gold.
- Kept the page structure unchanged while making the overall surface read cooler and closer to the reference navbar color family.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The page-wide brownish cast should now be gone.
- The big background effects now stay cool and blue instead of warming the whole screen.
- This was a color cleanup only, not a layout change.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-18 - Navbar Palette Alignment With ADTPG Reference

Technical Summary:
- Replaced the imported brown-toned global surface tokens with the blue, white, neutral, and dark-mode values used by the ADTPG reference navbar theme.
- Kept the previously ported navbar, landing, and auth structure intact, but updated the shared `background`, `panel`, `glass`, `accent`, and muted tokens so those screens now inherit the same core palette as the reference.
- Adjusted the hero background blend to stay bright and neutral instead of warming the page with the old brown-derived base colors.
- Revalidated the frontend with ESLint and a production Next.js build.

Plain-English Summary:
- The weird brown cast is gone.
- The imported screens now use the same blue-and-white color direction as the old reference navbar instead of the warmer palette that slipped in during the first port.
- I did not use the `uncodixfy` skill for this pass.

Files / Areas Touched:
- `frontend/src/app/globals.css`
- `CHANGELOG.md`

## 2026-04-18 - Legacy Landing, Navbar, And Login Visual Port

Technical Summary:
- Reworked the shared frontend top navigation to borrow the scrapped ADTPG visual language while keeping Wandrix's current server-authenticated links and sign-out flow intact.
- Rebuilt the home page around the older project's hero, glass-panel, and beam-style presentation, but kept Wandrix's current conversation-first product messaging and route wiring.
- Restyled the `/auth` experience to match the previous login-page aesthetic while preserving the existing combined sign-in and sign-up Supabase flow.
- Added a `/login` route alias that redirects into `/auth`, and extended shared global styling tokens to support the imported branding, glass surfaces, and atmospheric backgrounds.
- Verified the frontend with ESLint and a production Next.js build after the port.

Plain-English Summary:
- The app now looks much closer to the styling from your older ADTPG frontend on the navbar, landing page, and login experience.
- I kept Wandrix's newer structure and auth wiring underneath, so this is a visual transplant rather than a rollback of the newer app architecture.
- There is also now a `/login` path for convenience, even though the real auth screen still lives at `/auth`.

Files / Areas Touched:
- `frontend/src/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/page.tsx`
- `frontend/src/app/login/page.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/components/app/brand-wordmark.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `frontend/src/components/auth/sign-out-button.tsx`
- `CHANGELOG.md`

## 2026-04-19 - Account Popover And Post-Signup Onboarding Flow

Technical Summary:
- Replaced the top-level Profile navigation item with an account popover in the header that shows the user's name beside an avatar chip and keeps sign-out inside the same control.
- Added a client-side account popover built with Radix Popover and Motion, with inline profile editing and a direct link into planner-default onboarding.
- Updated signup flow so successful signups and email-confirmation redirects lead into onboarding before chat, rather than treating onboarding as a permanent top-level destination.
- Kept `/profile` as the onboarding route, but reframed it as a first-run and account-settings flow rather than a primary navigation page.

Plain-English Summary:
- The app now handles account access the way you described: through an avatar-and-name menu in the top bar instead of a separate Profile tab.
- New users are guided into onboarding after signup so Wandrix can learn their soft defaults before planning starts.

Files / Areas Touched:
- `frontend/package.json`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/auth/auth-shell.tsx`
- `frontend/src/app/profile/page.tsx`
- `frontend/src/components/profile/profile-onboarding.tsx`
- `README.md`

## 2026-04-19 - Profile Onboarding Flow

Technical Summary:
- Added a new authenticated `/profile` route that serves as the onboarding and soft-defaults setup surface for Wandrix.
- Built a checklist-style onboarding flow with per-step dialogs for display name, home airport and currency, travel preferences, location assistance, and the transition into chat.
- Added lightweight reusable frontend primitives for dialog, button, input, label, and class-name composition so the onboarding flow can use the requested dialog-driven pattern without depending on missing external UI files.
- Updated navigation and route docs so profile setup is part of the visible product flow.

Plain-English Summary:
- Wandrix now has a real onboarding page where a signed-in user can set the personal defaults the chat should use as soft guidance.
- The assistant can now be prepared to greet people more personally and start with better assumptions, while still keeping chat as the main place where actual trip planning happens.

Files / Areas Touched:
- `frontend/src/app/profile/page.tsx`
- `frontend/src/components/profile/profile-onboarding.tsx`
- `frontend/src/components/animate-ui/components/radix/dialog.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/label.tsx`
- `frontend/src/lib/utils.ts`
- `frontend/src/components/app/app-top-nav.tsx`
- `README.md`

## 2026-04-19 - Chat-First Planning Rule

Technical Summary:
- Updated repo documentation to explicitly define `/chat` as the primary planning workspace for Wandrix.
- Reframed flights, hotels, and activities routes in the README and UI copy as supporting reference views rather than parallel planning surfaces.
- Updated module workspace messaging so the product language stays aligned with the conversation-first architecture.

Plain-English Summary:
- The project now clearly treats chat as the main place where trip planning happens.
- The flights, hotels, and activities pages are now described as supporting views instead of separate planning tools.

Files / Areas Touched:
- `AGENTS.md`
- `docs/future-improvements.md`
- `README.md`
- `frontend/src/components/modules/trip-module-workspace.tsx`

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

## 2026-04-18 - LLM-First Planner Rule

Technical Summary:
- Updated the repo rules to make LLM-first, schema-validated trip understanding the intended long-term planner direction.
- Added explicit guidance that deterministic extraction and heuristic parsing may exist as temporary fallback only, and should be reduced over time instead of expanded.
- Added matching guidance to the future improvements roadmap so later sessions keep steering away from brittle regex-style planner behavior.

Plain-English Summary:
- The project rules now clearly say we should not keep building the planner around hardcoded parsing rules.
- Heuristics can stay as short-term backup, but the real direction is a smarter AI-first planner that handles ambiguity better.

Files / Areas Touched:
- `AGENTS.md`
- `docs/backend-coding-rules.md`
- `docs/future-improvements.md`

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
