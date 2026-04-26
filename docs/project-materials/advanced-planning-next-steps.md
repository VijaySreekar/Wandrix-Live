# Advanced Planning Next Steps

This file captures the next product step after the current Advanced Planning flow:
- shared intake
- working-date resolution
- anchor choice
- stay strategy selection
- hotel workspace
- working hotel selection

It exists separately from `docs/project-materials/future-improvements.md` so the larger roadmap can stay stable while this narrower execution plan evolves.

## Core Decision

The next priority is not another isolated hotel UI pass.

The next priority is to make `Advanced Planning continue properly after stay is done`.

Right now, `stay` is the first real deep anchor.
That is good progress, but the product should not feel like:
- choose one anchor
- finish that branch
- stall

It should feel like:
- choose an anchor
- complete a meaningful working decision
- return to the remaining anchors with better context
- recommend the strongest next planning move

## What Should Happen After A Working Hotel Is Selected

### 1. Mark `stay` as completed

- the board should stop treating stay as the only active branch
- stay should remain visible as completed context, not disappear

### 2. Return to the remaining anchors

- show the remaining Advanced anchors again:
  - `flight`
  - `trip_style`
  - `activities`
- recommend the strongest next one based on what we now know

### 3. Use the selected hotel as real planning context

- selected stay area should influence activity ranking
- selected hotel should influence local movement and pacing
- route practicality should be judged against the current hotel base
- weather-aware and evening-aware suggestions should now be hotel-aware too

### 4. Build the next real deep anchor

- the most natural next branch after `stay` is `activities`
- this should become the second real deep Advanced Planning path

## Why `Activities` Should Likely Come Next

- dates are already more concrete
- stay context is already selected
- activity clustering becomes much more meaningful now
- this is where the itinerary starts feeling genuinely curated

The `activities` branch should eventually handle:
- must-do anchors vs optional ideas
- day clustering around the selected stay
- pacing-aware suggestions
- event-aware structure later
- the difference between `essential`, `nice to have`, and `backup`

## Add Review And Conflict Logic Across Anchors

Advanced Planning should become revisable across connected decisions.

That means:
- a selected stay should be allowed to come under review later
- a selected hotel should be allowed to come under review later
- later activities or route decisions should be able to strain earlier choices
- Wandrix should explain the tension instead of silently replacing anything

Examples:
- the user picks a quiet hotel, then later prioritizes nightlife-heavy activities across the city
- the user picks a central stay, then later adds a day-trip-heavy structure that makes another base more practical
- the user picks a hotel, then later locks in a timing pattern that weakens its value

When that happens, Wandrix should:
- keep the earlier selection visible
- mark it as `needs review` or `strained`
- explain why in chat
- show the same warning on the board
- suggest better replacements instead of silently overwriting the old choice

Core product rule:
- Advanced Planning decisions are connected working decisions, not isolated one-way steps

## Practical Next Build Order

1. `Anchor progression after stay completion`
- once a hotel is selected, return to the remaining anchors instead of stalling in the stay branch

2. `Use selected hotel as downstream planning context`
- hotel and stay choice should start materially affecting later recommendations

3. `Build activities as the next deep anchor`
- make activities the second real step-by-step Advanced Planning branch

4. `Add cross-anchor review and conflict behavior`
- let later decisions challenge earlier ones in a visible, explainable way

## Why This Order Is Right

- it builds on what is already implemented
- it makes Advanced Planning feel continuous instead of fragmented
- it moves the product toward a real agentic planner rather than a series of disconnected selection screens
