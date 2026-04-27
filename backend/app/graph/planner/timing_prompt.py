TIMING_UNDERSTANDING_RULES = """
- Use travel_window for rough timing like "late September".
- Use trip_length for rough duration like "4 or 5 nights".
- Use weather_preference for desired conditions like warm, sunny, mild, cool, snowy, dry, or similar weather-led preferences when the user expresses them.
- Do not store non-timing placeholders as timing facts. If the user says "length TBD", "length undecided", "not sure how many days", "timing open", or "no month picked yet", leave that timing field empty and ask for it.
- If a board-composed message gives rough timing, parse it exactly like normal chat; the board is only helping the user phrase timing, not committing structured data for you.
- If a board-composed message gives exact dates, return start_date and end_date and mark those exact timing fields confirmed.
- If the user gives seasonal, holiday, relative-month, or soft timing language like "early October", "around Easter", "sometime in spring", or "late September", keep that in travel_window unless they gave exact calendar dates.
- If the user gives rough duration language like "long weekend", "five-ish days", "about a week", or "4 or 5 nights", keep that in trip_length unless they gave exact fixed dates.
- Only use exact start_date or end_date when the user gave fixed dates.
- Do not auto-convert rough timing into exact dates just to be helpful.
- The dedicated timing_choice board owns early timing intake. Once both a rough window and rough length are known, do not create decision_cards that ask the user to choose the timing shape again or pin exact dates unless the user's latest message specifically makes exact dates the next planning decision.
- If the user clearly cares about the weather outcome of the trip, keep that preference structured in weather_preference instead of leaving it buried only in assistant_response text.
- Do not invent a weather preference if the user did not indicate one.
""".strip()


TIMING_AMBIGUITY_EXAMPLES = """
- User: "Maybe a long weekend in late September."
  Good result: use travel_window and trip_length, not exact calendar dates.
- User: "Maybe early October for five-ish days."
  Good result: keep `travel_window` as early October and `trip_length` as five-ish days instead of inventing fixed dates.
- User: "I want this to feel warm and sunny."
  Good result: keep that in `weather_preference` without pretending the exact dates are already chosen.
""".strip()
