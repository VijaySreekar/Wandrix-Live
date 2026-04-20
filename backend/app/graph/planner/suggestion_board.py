from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.turn_models import DestinationSuggestionCandidate, TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    DestinationSuggestionCard,
    PlannerChecklistItem,
    PlannerDecisionCard,
    TripDetailsCollectionFormState,
    TripConversationState,
    TripSuggestionBoardState,
)
from app.schemas.trip_planning import TripConfiguration


OWN_CHOICE_PROMPT = "Tell me the destination you already have in mind."


def build_suggestion_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
    phase: str,
    llm_update: TripTurnUpdate,
    resolved_location_context: ResolvedPlannerLocationContext | None,
    board_action: dict,
) -> TripSuggestionBoardState:
    current_board = current.suggestion_board.model_copy(deep=True)
    action = (
        ConversationBoardAction.model_validate(board_action) if board_action else None
    )

    if configuration.to_location:
        if _details_collection_is_hidden(current, action):
            return TripSuggestionBoardState(
                mode="helper",
                title="Trip details confirmed.",
                subtitle="Keep shaping the trip in chat. This board can come back later when there is a more visual planning step to show.",
                own_choice_prompt=None,
            )
        details_collection_state = _build_details_collection_state(
            current=current,
            configuration=configuration,
            phase=phase,
            resolved_location_context=resolved_location_context,
            action=action,
        )
        if details_collection_state:
            return details_collection_state
        if current.decision_cards:
            return TripSuggestionBoardState(
                mode="decision_cards",
                source_context=None,
                title="Next trip decisions",
                subtitle="Choose the next detail to keep shaping this trip.",
                own_choice_prompt=None,
            )
        return TripSuggestionBoardState(
            mode="helper",
            title="The destination is set.",
            subtitle="Keep shaping the trip in chat and the next planning decisions can appear here.",
            own_choice_prompt=None,
        )

    next_cards = _resolve_destination_cards(
        current_board=current_board,
        llm_suggestions=llm_update.destination_suggestions,
        action=action,
    )

    if next_cards:
        title = (
            llm_update.destination_suggestion_title
            or current_board.title
            or "Here are a few strong destination directions."
        )
        subtitle = (
            llm_update.destination_suggestion_subtitle
            or current_board.subtitle
            or "Pick one to explore further, or tell me your own destination in chat."
        )
        source_context = (
            llm_update.location_source_summary
            or resolved_location_context.message_context
            if resolved_location_context
            else current_board.source_context
        )
        return TripSuggestionBoardState(
            mode="destination_suggestions",
            source_context=source_context,
            title=title,
            subtitle=subtitle,
            cards=next_cards[:4],
            own_choice_prompt=OWN_CHOICE_PROMPT,
        )

    if current.decision_cards:
        return TripSuggestionBoardState(
            mode="decision_cards",
            title="Next trip decisions",
            subtitle="These are the next choices that will sharpen the trip.",
            own_choice_prompt=None,
        )

    return TripSuggestionBoardState(
        mode="helper",
        title="Use the chat to shape the trip first.",
        subtitle="Once there is a stronger direction, this area can help with visual choices.",
        own_choice_prompt=None,
    )


def _build_details_collection_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
    phase: str,
    resolved_location_context: ResolvedPlannerLocationContext | None,
    action: ConversationBoardAction | None,
) -> TripSuggestionBoardState | None:
    has_origin_signal = bool(
        configuration.from_location
        or (resolved_location_context and resolved_location_context.summary)
    )
    if not configuration.to_location or not has_origin_signal:
        return None

    highlighted_details, missing_details = _build_details_checklist(
        configuration=configuration,
        resolved_location_context=resolved_location_context,
    )

    return TripSuggestionBoardState(
        mode="details_collection",
        title=(
            "Confirm the trip brief"
            if phase == "awaiting_confirmation"
            else "Fill in the rest of the trip details"
        ),
        subtitle=_build_details_subtitle(configuration, phase),
        highlighted_details=highlighted_details,
        missing_details=missing_details,
        details_form=_build_details_form_state(
            configuration,
            resolved_location_context,
        ),
        confirm_cta_label=(
            "Confirm this trip brief"
            if phase == "awaiting_confirmation"
            else "Confirm trip details"
        ),
        own_choice_prompt=None,
    )


def build_destination_mentioned_options(
    suggestions: list[DestinationSuggestionCandidate],
):
    from app.graph.planner.turn_models import ConversationOptionCandidate

    return [
        ConversationOptionCandidate(
            kind="destination",
            value=f"{suggestion.destination_name}, {suggestion.country_or_region}",
        )
        for suggestion in suggestions
    ]


def build_default_decision_cards(configuration: TripConfiguration) -> list[PlannerDecisionCard]:
    cards: list[PlannerDecisionCard] = []

    if configuration.to_location and not (
        configuration.start_date or configuration.travel_window
    ):
        cards.append(
            PlannerDecisionCard(
                title="Pick the timing direction",
                description="A rough travel window is the next useful planning choice.",
                options=["Next month", "Summer", "Autumn", "I’m flexible"],
            )
        )

    if configuration.to_location and (
        configuration.start_date or configuration.travel_window
    ) and not configuration.from_location:
        cards.append(
            PlannerDecisionCard(
                title="Set the departure point",
                description="The planner can get more practical once it knows where you would leave from.",
                options=["Use my home airport", "Choose another city", "I’m not sure yet"],
            )
        )

    return cards[:2]


def _build_details_subtitle(configuration: TripConfiguration, phase: str) -> str:
    if phase == "awaiting_confirmation":
        return "Everything important is in place. You can confirm this full brief on the board, or correct anything in chat before Wandrix moves on."

    active_modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    if active_modules == ["activities"]:
        return "You can keep this focused on activities, or adjust the scope before confirming the rest."
    if active_modules == ["weather"]:
        return "Timing matters most for this weather-focused plan, so use the board only if it helps you move faster."
    if active_modules == ["hotels"]:
        return "Set the stay details here if you want to narrow the trip around hotels first."
    if active_modules == ["flights"]:
        return "Set the travel basics here and I can keep the next steps flight-first."
    return "You can keep typing naturally in chat, or use the board to confirm the remaining details in one go."


def _build_details_checklist(
    *,
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None,
) -> tuple[list[PlannerChecklistItem], list[PlannerChecklistItem]]:
    route_value = " -> ".join(
        part
        for part in [
            configuration.from_location
            or (
                resolved_location_context.summary
                if resolved_location_context
                else None
            ),
            configuration.to_location,
        ]
        if part
    )
    checklist = [
        _build_checklist_item(
            "from_location",
            "From",
            configuration.from_location
            or (
                resolved_location_context.summary
                if resolved_location_context
                else None
            ),
        ),
        _build_checklist_item("to_location", "To", configuration.to_location),
        _build_checklist_item("route", "Route", route_value),
        _build_checklist_item(
            "timing",
            "Timing",
            configuration.travel_window
            or _format_date_value(configuration.start_date, configuration.end_date),
        ),
        _build_checklist_item("trip_length", "Trip length", configuration.trip_length),
        _build_checklist_item(
            "travelers",
            "Travellers",
            _format_travellers(
                configuration.travelers.adults,
                configuration.travelers.children,
            ),
        ),
        _build_checklist_item(
            "trip_style",
            "Trip style",
            ", ".join(configuration.activity_styles) if configuration.activity_styles else None,
        ),
        _build_checklist_item(
            "budget",
            "Budget",
            _format_budget_value(configuration),
        ),
        _build_checklist_item(
            "modules",
            "Module scope",
            _format_module_scope(configuration),
        ),
    ]
    highlighted = [item for item in checklist if item.status == "known"]
    missing = [item for item in checklist if item.status == "needed"]
    return highlighted, missing


def _build_checklist_item(
    item_id: str,
    label: str,
    value: str | None,
) -> PlannerChecklistItem:
    return PlannerChecklistItem(
        id=item_id,
        label=label,
        status="known" if value else "needed",
        value=value,
    )


def _build_details_form_state(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None,
) -> TripDetailsCollectionFormState:
    return TripDetailsCollectionFormState(
        from_location=configuration.from_location
        or (
            resolved_location_context.summary
            if resolved_location_context
            else None
        ),
        to_location=configuration.to_location,
        selected_modules=configuration.selected_modules.model_copy(deep=True),
        travel_window=configuration.travel_window,
        trip_length=configuration.trip_length,
        start_date=configuration.start_date,
        end_date=configuration.end_date,
        adults=configuration.travelers.adults,
        children=configuration.travelers.children,
        activity_styles=list(configuration.activity_styles),
        budget_posture=configuration.budget_posture,
        budget_gbp=configuration.budget_gbp,
    )


def _details_collection_is_hidden(
    current: TripConversationState,
    action: ConversationBoardAction | None,
) -> bool:
    if action and action.type == "confirm_trip_brief":
        return True

    return any(
        event.title.lower() == "trip brief confirmed"
        for event in current.memory.decision_history
    )


def _format_date_value(start_date, end_date) -> str | None:
    if start_date and end_date:
        return f"{start_date.isoformat()} to {end_date.isoformat()}"
    if start_date:
        return start_date.isoformat()
    if end_date:
        return end_date.isoformat()
    return None


def _format_travellers(adults: int | None, children: int | None) -> str | None:
    parts: list[str] = []
    if adults is not None:
        parts.append(f"{adults} adult{'s' if adults != 1 else ''}")
    if children is not None:
        parts.append(f"{children} child{'ren' if children != 1 else ''}")
    return " and ".join(parts) if parts else None


def _format_budget_value(configuration: TripConfiguration) -> str | None:
    parts = [
        configuration.budget_posture.replace("_", "-")
        if configuration.budget_posture
        else None,
        f"GBP {configuration.budget_gbp:.0f}"
        if configuration.budget_gbp is not None
        else None,
    ]
    summary = ", ".join(part for part in parts if part)
    return summary or None


def _format_module_scope(configuration: TripConfiguration) -> str | None:
    modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    return ", ".join(modules) if modules else None


def _resolve_destination_cards(
    *,
    current_board: TripSuggestionBoardState,
    llm_suggestions: list[DestinationSuggestionCandidate],
    action: ConversationBoardAction | None,
) -> list[DestinationSuggestionCard]:
    if llm_suggestions:
        cards = [
            DestinationSuggestionCard(
                id=suggestion.id,
                destination_name=suggestion.destination_name,
                country_or_region=suggestion.country_or_region,
                image_url=suggestion.image_url,
                short_reason=suggestion.short_reason,
                practicality_label=suggestion.practicality_label,
                selection_status="suggested",
            )
            for suggestion in llm_suggestions
        ]
    else:
        cards = current_board.cards

    if not cards:
        return []

    if action and action.type == "select_destination_suggestion":
        updated_cards: list[DestinationSuggestionCard] = []
        for card in cards:
            is_selected = (
                action.suggestion_id == card.id
                or (
                    action.destination_name
                    and card.destination_name.lower() == action.destination_name.lower()
                )
            )
            updated_cards.append(
                card.model_copy(
                    update={
                        "selection_status": "leading" if is_selected else "suggested"
                    }
                )
            )
        return updated_cards

    return cards
