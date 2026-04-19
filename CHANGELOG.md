# Changelog

All meaningful changes must be appended here.

Each entry should include:
- Date
- Title
- Technical Summary
- Plain-English Summary
- Files / Areas Touched

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
