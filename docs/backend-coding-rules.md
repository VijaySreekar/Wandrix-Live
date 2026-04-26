# Backend Coding Rules

These rules apply to the FastAPI backend in `backend/`.

## Purpose

The backend is responsible for travel package generation, orchestration of AI and third-party services, validation, and persistence. Keep it predictable, typed, and easy to extend.

## Architecture Rules

1. Keep routes thin.
Routes should handle HTTP concerns only: parsing input, calling services, and returning responses.

2. Put business logic in `app/services/`.
Trip generation, pricing logic, destination scoring, and itinerary assembly belong in services, not route files.

3. Put request and response models in `app/schemas/`.
Every non-trivial endpoint should use explicit Pydantic models for input and output.

4. Keep external integrations in `app/integrations/`.
AI model clients, maps APIs, hotel APIs, and flight providers should never be called directly from routes.

5. Keep configuration in `app/core/`.
Environment loading, app setup, CORS, logging, and shared settings belong there.

6. Add repositories only for persistence concerns.
Database reads and writes should live in `app/repositories/`, separate from business rules.

## API Design Rules

1. Use versioned API routes.
New product endpoints should live under `/api/v1/...`.

2. Return typed responses.
Do not return loose dictionaries from new feature endpoints when a schema is appropriate.

3. Validate early.
Dates, traveler counts, budget values, and required travel inputs must be validated at schema boundaries.

4. Keep naming consistent.
Use clear resource names like `packages`, `itineraries`, `destinations`, and `bookings`.

5. Prefer explicit errors.
Return helpful, user-safe error messages and avoid leaking stack traces or provider internals.

## AI and Travel Domain Rules

1. Keep prompt orchestration out of routes.
Prompt building and AI flow control belong in services and `app/integrations/llm/`.

2. Treat model output as untrusted input.
Validate and normalize AI responses before using them in downstream logic or returning them to the frontend.

3. Separate orchestration from provider calls.
`services/` should decide what to generate; `integrations/llm/` should handle the actual model request.

4. Do not use deterministic extraction for planner understanding.
Planner updates should come from LLM-first structured extraction, validation, and clarification instead of regex or keyword parsing.

5. Prefer clarification over brittle guessing.
If a user message is ambiguous, the planner should ask a follow-up question or keep the field inferred, rather than hard-locking a value from a weak heuristic.

6. Keep travel assumptions explicit.
Currencies, durations, traveler counts, and regional assumptions should be visible in code, not hidden in magic values.

## Code Style Rules

1. Use type hints everywhere practical.
Functions, service inputs, service outputs, and internal helpers should be typed.

2. Prefer small modules with one clear responsibility.
If a file starts mixing routing, prompt construction, pricing, and formatting, split it.

3. Do not let backend files grow into giant all-in-one modules.
When a service, graph node, schema file, or route file becomes too long or starts carrying multiple responsibilities, split it before adding more behavior.

4. Prefer pure helpers for domain logic.
Pricing calculations, scoring logic, and itinerary formatting should be easy to test without spinning up FastAPI.

5. Avoid large utility dumping grounds.
Only put code in `utils/` when it is truly generic and not part of a clearer domain layer.

6. Keep comments rare and high-value.
Explain non-obvious decisions, not obvious syntax.

## Testing Rules

1. Add tests for new service behavior.
Business logic changes should be covered at the service layer first.

2. Add endpoint tests for important API contracts.
If an endpoint shape matters to the frontend, test it.

3. Prefer fast tests.
Mock external providers and AI clients rather than calling real services in routine test runs.

4. Cover failure paths.
Invalid dates, malformed AI output, missing configuration, and provider failures should be tested.

## Change Rules

1. Do not bypass the architecture for speed.
Short-term hacks in route files become long-term maintenance problems.

2. Extend existing layers before inventing new ones.
If a feature fits `services/`, `schemas/`, or `integrations/`, use them.

3. Keep backwards compatibility in mind.
When changing response shapes used by the frontend, coordinate the frontend update in the same change.

4. Append meaningful backend changes to `CHANGELOG.md`.
Each entry must include both technical detail and a plain-English explanation.

5. Do not add heuristic parsing to new planner work.
Do not add more regex and keyword rules as the default way to understand user intent unless there is a strong short-term reason and a clear plan to replace them.
