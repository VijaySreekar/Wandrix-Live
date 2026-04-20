# Changelog

All meaningful changes must be appended here.

Each entry should include:
- Date
- Title
- Technical Summary
- Plain-English Summary
- Files / Areas Touched

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
