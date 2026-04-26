# Chat Page Snapshot - 2026-04-19

This folder preserves the exact `/chat` implementation state that was active on 2026-04-19 before later UI changes.

Purpose:
- keep a recoverable reference for the current chat layout
- preserve the exact source files that define the page shell, sidebar, assistant panel, board, header, and supporting chat-page visuals

Notes:
- this is a source snapshot, not a forked runtime route
- the copied files under `files/` are for reference and recovery
- the live product should continue evolving in the main `frontend/src/...` paths

Saved from:
- route: `/chat`
- branch at save time: `automation-runs`

Primary files preserved:
- `frontend/src/app/chat/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/components/app/app-top-nav.tsx`
- `frontend/src/components/app/app-nav-links.tsx`
- `frontend/src/components/auth/user-account-popover.tsx`
- `frontend/src/components/chat/chat-sidebar.tsx`
- `frontend/src/components/assistant/travel-planner-assistant.tsx`
- `frontend/src/components/package/travel-package-workspace.tsx`
- `frontend/src/components/package/trip-board-preview.tsx`
- `frontend/src/components/package/trip-board-cards.tsx`
- `frontend/src/components/profile/onboarding-dialog.tsx`
- `frontend/src/components/animate-ui/components/radix/dropdown-menu.tsx`
