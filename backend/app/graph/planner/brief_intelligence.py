from app.graph.planner.turn_models import TripTurnUpdate
from app.integrations.llm.client import create_chat_model
from app.schemas.trip_conversation import TripConversationState, TripFieldKey
from app.schemas.trip_draft import TripDraftStatus
from app.schemas.trip_planning import TripConfiguration


TRIP_BRIEF_FIELDS: tuple[TripFieldKey, ...] = (
    "from_location",
    "from_location_flexible",
    "to_location",
    "start_date",
    "end_date",
    "travel_window",
    "trip_length",
    "weather_preference",
    "budget_posture",
    "budget_amount",
    "budget_currency",
    "budget_gbp",
    "adults",
    "children",
    "travelers_flexible",
    "activity_styles",
    "custom_style",
    "selected_modules",
)


def review_trip_brief_intelligence(
    *,
    user_input: str,
    configuration: TripConfiguration,
    title: str,
    status: TripDraftStatus,
    conversation: TripConversationState,
    profile_context: dict,
    current_location_context: dict,
    board_action: dict,
    raw_messages: list[dict],
    llm_update: TripTurnUpdate,
) -> TripTurnUpdate:
    if not _should_review_brief(
        user_input=user_input,
        configuration=configuration,
        conversation=conversation,
        board_action=board_action,
        raw_messages=raw_messages,
        llm_update=llm_update,
    ):
        return llm_update

    prompt = f"""
You are Wandrix's trip brief intelligence reviewer.

Return a TripTurnUpdate that conservatively enriches the proposed structured update.

Rules:
- This is LLM-first structured understanding. Do not use regex, keyword matching, or deterministic extraction.
- Preserve the proposed TripTurnUpdate unless conversation context clearly supports a missing brief field.
- Only fill a field when it is supported by the recent conversation or saved structured memory.
- Do not invent traveller counts, budget amounts, origins, exact dates, or modules.
- If the user said a currency such as GBP, EUR, or USD, set budget_currency to that 3-letter code without inventing budget_amount.
- If a budget amount is explicitly given, use budget_amount and budget_currency. Set budget_gbp only as a legacy mirror when the amount is explicitly GBP.
- If earlier conversation mentioned a trip style like relaxed, food-led, culture, luxury, family, romantic, outdoors, adventure, or nightlife, preserve it in activity_styles when it fits the intake vocabulary.
- If earlier conversation mentioned a duration like long weekend or five-ish days, preserve it in trip_length unless exact dates were already confirmed.
- If earlier conversation mentioned a rough window like around June 15th, preserve it as travel_window unless the user gave a full exact date range.
- For each field you add or preserve as newly touched, add confirmed_fields or inferred_fields, plus field_confidences and field_sources.
- Use user_explicit for clearly stated user facts, user_inferred for strong contextual reads, profile_default only for profile suggestions, and assistant_derived only for assistant-side derived planning context.
- Prefer inferred_fields over confirmed_fields whenever the field is useful but not fully locked.
- Do not set confirmed_trip_brief.
- Do not rewrite assistant_response.

Current draft title:
{title}

Current configuration:
{configuration.model_dump(mode="json")}

Current planner status:
{status.model_dump(mode="json")}

Current conversation state:
{conversation.model_dump(mode="json")}

Saved profile context:
{profile_context}

Current location context:
{current_location_context}

Latest board action:
{board_action}

Recent raw messages:
{raw_messages[-8:]}

Latest user message:
{user_input}

Proposed TripTurnUpdate:
{llm_update.model_dump(mode="json")}
""".strip()

    try:
        model = create_chat_model(temperature=0.1)
        structured_model = model.with_structured_output(
            TripTurnUpdate,
            method="json_schema",
        )
        reviewed_update = structured_model.invoke(
            [
                (
                    "system",
                    "Enrich Wandrix trip brief fields from conversation context.",
                ),
                ("human", prompt),
            ]
        )
    except Exception:
        return llm_update

    return _merge_brief_review(
        base=llm_update,
        reviewed=reviewed_update,
        configuration=configuration,
    )


def _should_review_brief(
    *,
    user_input: str,
    configuration: TripConfiguration,
    conversation: TripConversationState,
    board_action: dict,
    raw_messages: list[dict],
    llm_update: TripTurnUpdate,
) -> bool:
    if board_action or not user_input.strip():
        return False
    if conversation.suggestion_board.mode in {
        "planning_mode_choice",
        "quick_plan_review",
    }:
        return False
    if len(raw_messages) < 2:
        return False
    return bool(configuration.to_location or llm_update.to_location)


def _merge_brief_review(
    *,
    base: TripTurnUpdate,
    reviewed: TripTurnUpdate,
    configuration: TripConfiguration,
) -> TripTurnUpdate:
    merged = base.model_copy(deep=True)
    touched_fields = set(reviewed.confirmed_fields) | set(reviewed.inferred_fields)

    for field in TRIP_BRIEF_FIELDS:
        if field not in touched_fields:
            continue
        value = _get_update_value(reviewed, field)
        if not _value_has_signal(value):
            continue
        if _value_has_signal(_get_update_value(merged, field)):
            continue
        if _value_has_signal(_get_configuration_value(configuration, field)):
            continue
        _set_update_value(merged, field, value)
        _copy_field_status(merged=merged, reviewed=reviewed, field=field)

    _dedupe_field_lists(merged)
    return merged


def _copy_field_status(
    *,
    merged: TripTurnUpdate,
    reviewed: TripTurnUpdate,
    field: TripFieldKey,
) -> None:
    if field in reviewed.confirmed_fields and field not in merged.confirmed_fields:
        merged.confirmed_fields.append(field)
    elif field in reviewed.inferred_fields and field not in merged.inferred_fields:
        merged.inferred_fields.append(field)

    for confidence in reviewed.field_confidences:
        if confidence.field == field and not any(
            item.field == field for item in merged.field_confidences
        ):
            merged.field_confidences.append(confidence)
            break

    for source in reviewed.field_sources:
        if source.field == field and not any(
            item.field == field for item in merged.field_sources
        ):
            merged.field_sources.append(source)
            break


def _dedupe_field_lists(update: TripTurnUpdate) -> None:
    update.confirmed_fields = list(dict.fromkeys(update.confirmed_fields))
    update.inferred_fields = [
        field
        for field in dict.fromkeys(update.inferred_fields)
        if field not in update.confirmed_fields
    ]


def _get_update_value(update: TripTurnUpdate, field: TripFieldKey):
    if field == "selected_modules":
        if update.selected_modules == update.__class__().selected_modules:
            return None
        return update.selected_modules
    return getattr(update, field)


def _set_update_value(update: TripTurnUpdate, field: TripFieldKey, value) -> None:
    if field == "selected_modules":
        update.selected_modules = value
        return
    setattr(update, field, value)


def _get_configuration_value(configuration: TripConfiguration, field: TripFieldKey):
    if field == "adults":
        return configuration.travelers.adults
    if field == "children":
        return configuration.travelers.children
    if field == "selected_modules":
        default_modules = TripConfiguration().selected_modules
        return (
            configuration.selected_modules
            if configuration.selected_modules != default_modules
            else None
        )
    return getattr(configuration, field)


def _value_has_signal(value) -> bool:
    if value is None:
        return False
    if value == "":
        return False
    if value == []:
        return False
    if value == {}:
        return False
    return True
