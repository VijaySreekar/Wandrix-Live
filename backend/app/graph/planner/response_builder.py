from app.schemas.trip_conversation import TripConversationState, TripFieldKey
from app.schemas.trip_planning import TripConfiguration


def build_assistant_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    fallback_text: str | None,
) -> str:
    if fallback_text and fallback_text.strip():
        return fallback_text.strip()

    route_summary = (
        f"{configuration.from_location or 'your origin'} to "
        f"{configuration.to_location or 'your destination'}"
    )
    open_questions = [
        question.question.rstrip("?")
        for question in conversation.open_questions
        if question.status == "open"
    ]
    inferred_fields = [
        field
        for field, memory in conversation.memory.field_memory.items()
        if memory.source != "user_explicit"
    ]

    if conversation.phase == "opening":
        return (
            "I'm ready to shape this with you. "
            "Tell me where you want to go, roughly when, and where you'd leave from, "
            "and I'll keep the early draft soft until the trip direction is clear."
        )

    if conversation.phase in {"collecting_requirements", "shaping_trip"}:
        summary = _build_trip_shape_summary(configuration)
        inferred_summary = _build_inferred_summary(inferred_fields)
        follow_up = " ".join(f"{question}?" for question in open_questions[:2])
        return f"{summary} {inferred_summary} {follow_up}".strip()

    if conversation.phase == "enriching_modules":
        return (
            f"I've got enough shape to start planning around {route_summary}. "
            "I'll keep using soft assumptions where needed, pull in the relevant modules carefully, "
            "and call out anything that still needs a decision."
        )

    return (
        f"The trip is now coherent enough to review around {route_summary}. "
        "I can keep refining the choices with you or turn this into a clearer trip summary next."
    )


def _build_trip_shape_summary(configuration: TripConfiguration) -> str:
    parts: list[str] = []
    if configuration.to_location:
        parts.append(f"a trip centered on {configuration.to_location}")
    if configuration.activity_styles:
        parts.append(f"with a {', '.join(configuration.activity_styles[:2])} feel")
    if configuration.travel_window:
        parts.append(f"around {configuration.travel_window}")
    if configuration.trip_length:
        parts.append(f"for {configuration.trip_length}")

    if not parts:
        return "I don't want to lock the wrong details too early."

    return f"I can already start shaping this as {' '.join(parts)}."


def _build_inferred_summary(inferred_fields: list[TripFieldKey]) -> str:
    labels = [_field_label(field) for field in inferred_fields[:2]]
    if not labels:
        return "I'm keeping anything uncertain soft instead of pretending it's confirmed."
    if len(labels) == 1:
        return f"I'm still treating {labels[0]} as provisional."
    return f"I'm still treating {labels[0]} and {labels[1]} as provisional."


def _field_label(field: TripFieldKey) -> str:
    return {
        "from_location": "your departure point",
        "to_location": "the destination",
        "start_date": "the travel window",
        "end_date": "the trip length",
        "travel_window": "the rough travel timing",
        "trip_length": "the rough trip length",
        "budget_gbp": "the budget posture",
        "adults": "the traveler count",
        "children": "the child traveler count",
        "activity_styles": "the trip style",
        "selected_modules": "the active planning modules",
    }[field]
