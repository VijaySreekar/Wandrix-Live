from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import TripConfiguration


def build_timing_choice_response(
    *,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    greeting_name: str | None,
) -> str:
    greeting_prefix = f"Hey {greeting_name}, " if greeting_name else ""
    destination = configuration.to_location or "this trip"
    open_questions = [
        question.question.rstrip("?")
        for question in conversation.open_questions
        if question.status == "open" and question.step == "timing"
    ]

    if configuration.travel_window and not configuration.trip_length:
        timing_line = (
            f"I have {configuration.travel_window} for {destination}. "
            "The useful missing piece is how long to make it."
        )
    elif configuration.trip_length and not configuration.travel_window:
        timing_line = (
            f"I have {configuration.trip_length} for {destination}. "
            "The useful missing piece is the month, season, or general window."
        )
    else:
        timing_line = (
            f"I have {destination} as the destination. "
            "Next I just need the timing shape."
        )

    question_line = (
        f" {open_questions[0]}?"
        if open_questions
        else " A rough month or season plus a rough length is enough for now."
    )
    example_line = (
        "You can use the board, or type it naturally, like "
        "\"early October for a long weekend\" or \"June 3 to June 8.\""
    )

    return f"{greeting_prefix}{timing_line}{question_line} {example_line}"
