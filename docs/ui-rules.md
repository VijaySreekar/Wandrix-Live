# UI Rules

## Product Experience

The UI must support a conversation-first travel planning flow.

The expected product shape is:
- left: conversation workspace
- right: live trip board
- final: brochure-style trip presentation

## Styling Rules

1. Fonts must come from shared global configuration.
Do not choose one-off fonts inside components.

2. Colors must come from shared global tokens.
Do not hardcode feature colors directly in components unless a temporary exception is explicitly documented.

3. `globals.css` is the primary place for shared design tokens.
If the design system changes, update tokens there first.

4. Prefer CSS variables and tokenized Tailwind usage over repeated literal values.

5. Do not turn the product into a generic SaaS dashboard.
The experience should feel like premium travel planning.

## Layout Rules

1. The conversation panel should remain readable and focused.

2. The trip board should be structured, scannable, and persistent.

3. The brochure should feel editorial and polished, not like a raw debug page.

4. Mobile and desktop should both be considered from the start.

## Component Rules

1. Reuse shared UI primitives where possible.

2. Keep product-specific rendering in feature folders.

3. Keep board rendering driven by structured trip draft data.

4. Avoid hardcoding content assumptions that belong in schemas or services.

## Change Rules

1. Any meaningful visual system change should be documented in `CHANGELOG.md`.

2. If a new token is added, note it in the changelog entry.

