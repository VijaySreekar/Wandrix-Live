from app.graph.planner.details_collection import (
    build_details_checklist_sections,
    get_required_steps,
    get_visible_steps,
    has_origin_signal_for_details,
)
from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.turn_models import DestinationSuggestionCandidate, TripTurnUpdate
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    DestinationSuggestionCard,
    PlanningModeChoiceCard,
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
    brief_confirmed: bool,
) -> TripSuggestionBoardState:
    current_board = current.suggestion_board.model_copy(deep=True)
    action = (
        ConversationBoardAction.model_validate(board_action) if board_action else None
    )

    if action and action.type == "own_choice" and not configuration.to_location:
        return TripSuggestionBoardState(
            mode="helper",
            title="Tell me the destination you already have in mind.",
            subtitle="Once you send a specific place in chat, I will move straight to the next real planning choice.",
            own_choice_prompt=None,
        )

    if configuration.to_location:
        if brief_confirmed and current.planning_mode_status == "not_selected":
            return _build_planning_mode_choice_state()
        details_collection_state = _build_details_collection_state(
            current=current,
            configuration=configuration,
            phase=phase,
            resolved_location_context=resolved_location_context,
            action=action,
            brief_confirmed=brief_confirmed,
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
        current=current,
        current_board=current_board,
        llm_suggestions=llm_update.destination_suggestions,
        action=action,
    )

    if _should_show_destination_suggestions(
        configuration=configuration,
        llm_update=llm_update,
        action=action,
        next_cards=next_cards,
    ):
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
    brief_confirmed: bool,
) -> TripSuggestionBoardState | None:
    if brief_confirmed:
        return None

    if not configuration.to_location or not has_origin_signal_for_details(
        configuration,
        resolved_location_context,
    ):
        return None

    have_details, need_details = build_details_checklist_sections(
        configuration=configuration,
        resolved_location_context=resolved_location_context,
    )
    all_required_details_present = len(need_details) == 0

    return TripSuggestionBoardState(
        mode="details_collection",
        title="Review the trip details"
        if all_required_details_present
        else "Fill in the rest of the trip details",
        subtitle=_build_details_subtitle(
            configuration,
            phase,
            all_required_details_present=all_required_details_present,
        ),
        have_details=have_details,
        need_details=need_details,
        visible_steps=get_visible_steps(configuration),
        required_steps=get_required_steps(configuration),
        details_form=_build_details_form_state(
            configuration,
            resolved_location_context,
        ),
        confirm_cta_label="Confirm trip details",
        own_choice_prompt=None,
    )


def _build_planning_mode_choice_state() -> TripSuggestionBoardState:
    return TripSuggestionBoardState(
        mode="planning_mode_choice",
        title="How should Wandrix plan this first draft?",
        subtitle=(
            "Quick Plan is ready now and will build a draft itinerary you can refine in chat. "
            "Advanced Planning will come later with deeper step-by-step confirmation."
        ),
        planning_mode_cards=[
            PlanningModeChoiceCard(
                id="quick",
                title="Quick Plan",
                description="Generate a full first-pass itinerary right away from the brief you already confirmed.",
                bullets=[
                    "Builds a draft itinerary immediately",
                    "Uses the trip details and saved preferences softly",
                    "Keeps everything editable in chat afterwards",
                ],
                status="available",
                badge="Available now",
                cta_label="Generate quick draft",
            ),
            PlanningModeChoiceCard(
                id="advanced",
                title="Advanced Planning",
                description="A slower guided mode that will confirm more decisions before shaping the itinerary.",
                bullets=[
                    "More step-by-step confirmations",
                    "More deliberate tradeoff handling",
                    "Still in development for now",
                ],
                status="in_development",
                badge="In development",
                cta_label="Coming soon",
            ),
        ],
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
    active_modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]

    if configuration.to_location and not (
        configuration.start_date or configuration.travel_window
    ):
        cards.append(
            PlannerDecisionCard(
                title=f"Choose the timing shape for {configuration.to_location}",
                description="A rough travel window is the next useful choice, and it matters more than exact dates right now.",
                options=[
                    "Spring city break",
                    "Early summer escape",
                    "Autumn weekend",
                    "I'm flexible",
                ],
            )
        )

    if configuration.to_location and (
        configuration.start_date or configuration.travel_window
    ) and not configuration.from_location:
        cards.append(
            PlannerDecisionCard(
                title="Set the departure point",
                description="The planner can get more practical once it knows where you would leave from.",
                options=[
                    "Use my usual airport",
                    "Choose another city",
                    "I'm not sure yet",
                ],
            )
        )

    if configuration.to_location and (
        configuration.start_date or configuration.travel_window
    ) and "activities" in active_modules and not configuration.activity_styles:
        cards.append(
            PlannerDecisionCard(
                title=f"Choose the feel for {configuration.to_location}",
                description="These are the strongest trip directions to decide between before I start shaping the itinerary.",
                options=[
                    "Food-led neighbourhood weekend",
                    "Classic highlights city break",
                    "Relaxed slower pace",
                    "Outdoors and day trips",
                ],
            )
        )

    return cards[:2]


def _build_details_subtitle(
    configuration: TripConfiguration,
    phase: str,
    *,
    all_required_details_present: bool,
) -> str:
    if all_required_details_present:
        return "Everything important is filled in. Review it on the board if you want to tweak anything, or confirm in chat and Wandrix can move ahead."

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
def _resolve_destination_cards(
    *,
    current: TripConversationState,
    current_board: TripSuggestionBoardState,
    llm_suggestions: list[DestinationSuggestionCandidate],
    action: ConversationBoardAction | None,
) -> list[DestinationSuggestionCard]:
    if action and action.type == "own_choice":
        return []

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
        cards = _filter_rejected_destination_cards(cards, current)
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


def _filter_rejected_destination_cards(
    cards: list[DestinationSuggestionCard],
    current: TripConversationState,
) -> list[DestinationSuggestionCard]:
    rejected_destination_keys = {
        key
        for option in current.memory.rejected_options
        if option.kind == "destination"
        for key in _destination_option_keys(option.value)
    }
    seen_destination_keys: set[str] = set()
    filtered: list[DestinationSuggestionCard] = []

    for card in cards:
        card_keys = _destination_option_keys(
            f"{card.destination_name}, {card.country_or_region}"
        )
        if rejected_destination_keys.intersection(card_keys):
            continue

        primary_key = _normalize_destination_value(card.destination_name)
        if primary_key in seen_destination_keys:
            continue

        seen_destination_keys.add(primary_key)
        filtered.append(card)

    return filtered


def _destination_option_keys(value: str) -> set[str]:
    normalized = _normalize_destination_value(value)
    if not normalized:
        return set()

    keys = {normalized}
    primary = normalized.split(",")[0].strip()
    if primary:
        keys.add(primary)
    return keys


def _normalize_destination_value(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _should_show_destination_suggestions(
    *,
    configuration: TripConfiguration,
    llm_update: TripTurnUpdate,
    action: ConversationBoardAction | None,
    next_cards: list[DestinationSuggestionCard],
) -> bool:
    if configuration.to_location:
        return False
    if action and action.type == "own_choice":
        return False
    if llm_update.to_location:
        return False
    return bool(next_cards)
