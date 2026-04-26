from app.graph.planner.details_collection import (
    compute_scope_missing_fields,
    get_visible_steps,
)
from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.schemas.trip_conversation import (
    ConversationFieldMemory,
    TripDetailsFieldMeta,
    TripDetailsStepKey,
    TripFieldKey,
)
from app.schemas.trip_planning import TripConfiguration


def build_details_field_meta(
    field_memory: dict[TripFieldKey, ConversationFieldMemory],
) -> dict[TripFieldKey, TripDetailsFieldMeta]:
    return {
        field: TripDetailsFieldMeta(
            field=field,
            source=memory.source,
            confidence_level=memory.confidence_level,
            label=_field_source_label(memory),
        )
        for field, memory in field_memory.items()
    }


def get_suggested_details_step(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
    *,
    selected_modules_explicit: bool = False,
) -> TripDetailsStepKey:
    missing_fields = compute_scope_missing_fields(
        configuration,
        resolved_location_context=resolved_location_context,
        allow_flexible_origin=True,
        allow_flexible_travelers=True,
        selected_modules_explicit=selected_modules_explicit,
    )
    priority: list[tuple[TripDetailsStepKey, set[str]]] = [
        ("route", {"to_location", "from_location"}),
        ("timing", {"start_date", "end_date"}),
        ("travellers", {"adults"}),
        ("vibe", {"activity_styles"}),
        ("budget", {"budget_posture"}),
        ("modules", {"selected_modules"}),
    ]
    visible_step_list = get_visible_steps(configuration)
    visible_steps = set(visible_step_list)
    missing = set(missing_fields)
    for step, fields in priority:
        if step in visible_steps and missing.intersection(fields):
            return step
    return visible_step_list[0] if visible_step_list else "modules"


def _field_source_label(memory: ConversationFieldMemory) -> str:
    if memory.source == "board_action":
        return "Confirmed"
    if memory.source == "user_explicit":
        return "You said"
    if memory.source == "profile_default":
        return "Profile"
    return "Inferred"
