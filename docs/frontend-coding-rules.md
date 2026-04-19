# Frontend Coding Rules

These rules apply to the Next.js frontend in `frontend/`.

## Purpose

The frontend should turn travel planning into a clear product flow: input trip details, generate packages, compare options, and refine results. Keep the UI structured, typed, and easy to evolve.

## Architecture Rules

1. Keep route files focused on page composition.
Files in `src/app/` should mainly assemble page sections and route-level layout.

2. Put reusable product UI in `src/components/`.
Shared primitives go in `components/ui/`. Travel-package-specific UI goes in folders like `components/package/`.

3. Keep backend calls in `src/lib/api/`.
Do not scatter raw `fetch` calls across pages and components.

4. Keep shared request and response types in `src/types/`.
Frontend types should mirror backend contracts closely enough to keep integration explicit.

5. Create new feature folders when the product grows.
For example: `components/destination/`, `components/booking/`, `components/profile/`.

## Next.js Rules

1. Default to Server Components.
Only add `"use client"` when interactivity, state, or browser APIs require it.

2. Keep client boundaries small.
Wrap only the interactive part of the page in a client component instead of making the whole route client-side.

3. Use the app router conventions cleanly.
Pages, layouts, loading states, and error states should follow Next.js file conventions rather than custom workarounds.

4. Respect current Next.js behavior.
Check local docs or project conventions before using patterns that may have changed across versions.

## UI Rules

1. Build intentional interfaces.
Avoid generic dashboard filler and keep each screen tied to a clear user task.

2. Prefer composition over giant components.
Break pages into sections like form, results, itinerary cards, pricing panels, and recommendation lists.

3. Do not let frontend files become oversized.
If a page or component keeps growing, split it into subcomponents, hooks, helpers, or typed view models before adding more UI logic.

4. Keep forms predictable.
Trip-input forms should normalize values before submission and surface useful validation feedback.

5. Maintain accessibility.
Use semantic elements, labels, focus states, readable contrast, and keyboard-friendly interactions.

6. Reuse visual primitives.
If the same card, badge, or panel pattern appears twice, consider moving it into `components/ui/`.

## Data and State Rules

1. Keep server communication centralized.
API calls should go through `lib/api/` helpers, not inline in multiple components.

2. Keep state close to where it is used.
Local page or feature state should stay inside the relevant component unless multiple routes truly need it.

3. Prefer explicit loading and error states.
Every async package-generation flow should show what is happening and what failed.

4. Normalize backend data at the boundary.
If the backend response needs shaping for presentation, do that close to the API layer or feature entry point.

5. Do not invent duplicate truth.
If the backend owns itinerary structure, do not redefine a conflicting frontend-only version.

## Styling Rules

1. Preserve the product's visual language.
New screens should feel like Wandrix, not like disconnected templates.

2. Use Tailwind intentionally.
Prefer readable class groupings and extracted components over huge unreadable blobs of utility classes.

3. Fonts and colors should come from shared global tokens first.
Do not hardcode one-off colors and font choices in feature components when a shared token should exist.

4. Keep styles close to the component unless they are truly shared.

5. Design for desktop and mobile together.
Do not treat responsive behavior as a cleanup step.

## Change Rules

1. New product work should usually touch all three of these when needed:
`components/`, `lib/api/`, and `types/`.

2. Do not put backend contract knowledge only in UI markup.
If an endpoint changes, update the shared type and API helper as part of the same change.

3. Keep the homepage light and move complex workflows into dedicated routes.
The main package generator belongs in its own route, not in an ever-growing landing page.

4. Favor maintainability over clever abstractions.
Simple, explicit React code is better than indirection that hides product behavior.

5. Append meaningful frontend changes to `CHANGELOG.md`.
Each entry must include both technical detail and a plain-English explanation.
