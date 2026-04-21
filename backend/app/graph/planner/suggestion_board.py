from app.graph.planner.details_collection import (
    build_details_checklist_sections,
    get_required_steps,
    get_visible_steps,
    has_flexible_origin,
    has_origin_signal_for_details,
)
from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.graph.planner.turn_models import (
    ConversationOptionCandidate,
    DestinationSuggestionCandidate,
    TripTurnUpdate,
)
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    AdvancedAnchorChoiceCard,
    DestinationSuggestionCard,
    PlannerAdvancedAnchor,
    PlanningModeChoiceCard,
    PlannerAdvancedStep,
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
    advanced_step: PlannerAdvancedStep | None = None,
    advanced_anchor: PlannerAdvancedAnchor | None = None,
    planning_mode_choice_required: bool = False,
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

    if planning_mode_choice_required and current.planning_mode is None:
        return _build_planning_mode_choice_state(
            configuration=configuration,
            brief_confirmed=brief_confirmed,
        )

    if (
        current.planning_mode == "advanced"
        and advanced_step == "choose_anchor"
        and brief_confirmed
    ):
        return _build_advanced_anchor_choice_state(configuration=configuration)

    if (
        current.planning_mode == "advanced"
        and advanced_step == "anchor_flow"
        and advanced_anchor is not None
    ):
        return _build_advanced_anchor_selected_state(
            configuration=configuration,
            advanced_anchor=advanced_anchor,
        )

    if configuration.to_location:
        if brief_confirmed and current.planning_mode_status == "not_selected":
            return _build_planning_mode_choice_state(
                configuration=configuration,
                brief_confirmed=brief_confirmed,
            )
        details_collection_state = _build_details_collection_state(
            current=current,
            configuration=configuration,
            phase=phase,
            resolved_location_context=resolved_location_context,
            action=action,
            brief_confirmed=brief_confirmed,
            planning_mode=current.planning_mode,
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

    unresolved_destinations = _resolve_unconfirmed_destination_options(
        current=current,
        llm_update=llm_update,
    )
    if not configuration.to_location and len(unresolved_destinations) >= 2:
        return TripSuggestionBoardState(
            mode="helper",
            title=_build_unresolved_destination_title(unresolved_destinations),
            subtitle=(
                "Both options are still in play. Pick one in chat when you are ready, or tell me to keep comparing them without locking the destination yet."
            ),
            own_choice_prompt=None,
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
    planning_mode: str | None,
) -> TripSuggestionBoardState | None:
    if brief_confirmed:
        return None

    if not configuration.to_location:
        return None

    require_origin_signal = planning_mode != "advanced"
    if require_origin_signal and not has_origin_signal_for_details(
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
        else (
            "Build the Advanced Planning brief"
            if planning_mode == "advanced"
            else "Fill in the rest of the trip details"
        ),
        subtitle=_build_details_subtitle(
            configuration,
            phase,
            planning_mode=planning_mode,
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


def _build_planning_mode_choice_state(
    *,
    configuration: TripConfiguration,
    brief_confirmed: bool,
) -> TripSuggestionBoardState:
    if brief_confirmed:
        title = "How should Wandrix plan this trip?"
        subtitle = (
            "The trip brief is ready. Choose Quick Plan for a fast draft itinerary, "
            "or Advanced Plan to keep this guided and step by step."
        )
    else:
        destination = configuration.to_location or "this trip"
        title = "Choose the planning mode"
        subtitle = (
            f"I've kept {destination} as the working direction so far. "
            "Before I proceed, choose Quick Plan for a fast draft or Advanced Plan for a more guided flow."
        )

    return TripSuggestionBoardState(
        mode="planning_mode_choice",
        title=title,
        subtitle=subtitle,
        planning_mode_cards=[
            PlanningModeChoiceCard(
                id="quick",
                title="Quick Plan",
                description=(
                    "Use the shared trip details, then generate the first draft itinerary as soon as the brief is ready."
                ),
                bullets=[
                    "Fastest path to a first itinerary draft",
                    "Still uses the trip details and saved preferences softly",
                    "Keeps everything editable in chat afterwards",
                ],
                status="available",
                badge="Available now",
                cta_label="Use Quick Plan",
            ),
            PlanningModeChoiceCard(
                id="advanced",
                title="Advanced Planning",
                description=(
                    "Use the same shared trip details first, then keep planning in a more guided, step-by-step mode."
                ),
                bullets=[
                    "Keeps planning more deliberate after the brief is ready",
                    "Better fit for tradeoffs and step-by-step selection",
                    "Starts from the same shared intake as Quick Plan",
                ],
                status="available",
                badge="Guided mode",
                cta_label="Use Advanced Plan",
            ),
        ],
        own_choice_prompt=None,
    )


def _build_advanced_anchor_choice_state(
    *,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    recommended_anchor = _recommend_advanced_anchor(configuration=configuration)
    return TripSuggestionBoardState(
        mode="advanced_anchor_choice",
        title="Choose what should lead the trip first",
        subtitle=(
            f"The brief for {destination} is strong enough now. "
            "Pick the first Advanced Planning anchor. Wandrix recommends one starting point, but you can choose any of the four."
        ),
        advanced_anchor_cards=_build_advanced_anchor_cards(recommended_anchor),
        own_choice_prompt=None,
    )


def _build_advanced_anchor_selected_state(
    *,
    configuration: TripConfiguration,
    advanced_anchor: PlannerAdvancedAnchor,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    anchor_title = _advanced_anchor_title(advanced_anchor)
    return TripSuggestionBoardState(
        mode="advanced_next_step",
        title=f"{anchor_title} will lead this trip first",
        subtitle=(
            f"Advanced Planning is now centered on {anchor_title.lower()} for {destination}. "
            "The next step is building the first deeper flow around that choice."
        ),
        own_choice_prompt=None,
    )


def _build_advanced_anchor_cards(
    recommended_anchor: PlannerAdvancedAnchor,
) -> list[AdvancedAnchorChoiceCard]:
    return [
        AdvancedAnchorChoiceCard(
            id="flight",
            title="Flight",
            description="Start with routing, departure practicality, and schedule shape before the rest of the trip.",
            bullets=[
                "Best for short breaks or route-sensitive trips",
                "Useful when departure certainty matters most",
                "Helps shape arrival and departure day pacing early",
            ],
            recommended=recommended_anchor == "flight",
            badge="Recommended" if recommended_anchor == "flight" else None,
            cta_label="Start with flights",
        ),
        AdvancedAnchorChoiceCard(
            id="stay",
            title="Stay",
            description="Choose the stay area or hotel direction first so the rest of the trip can build around it.",
            bullets=[
                "Best when neighbourhood choice shapes the trip",
                "Useful for city breaks and walkability tradeoffs",
                "Helps later activity ranking feel more coherent",
            ],
            recommended=recommended_anchor == "stay",
            badge="Recommended" if recommended_anchor == "stay" else None,
            cta_label="Start with stay",
        ),
        AdvancedAnchorChoiceCard(
            id="trip_style",
            title="Trip Style",
            description="Set the pacing and tone first, then let Wandrix shape the rest around that feel.",
            bullets=[
                "Best when you know the vibe but not the exact structure",
                "Useful for slower vs packed pacing decisions",
                "Influences both stay fit and activity ranking",
            ],
            recommended=recommended_anchor == "trip_style",
            badge="Recommended" if recommended_anchor == "trip_style" else None,
            cta_label="Start with trip style",
        ),
        AdvancedAnchorChoiceCard(
            id="activities",
            title="Activities",
            description="Lead with the concrete things you want to do, then shape timing and stay around those anchors.",
            bullets=[
                "Best when must-do experiences drive the trip",
                "Useful for events, museum-heavy trips, or food-led routes",
                "Lets the itinerary cluster around real anchors first",
            ],
            recommended=recommended_anchor == "activities",
            badge="Recommended" if recommended_anchor == "activities" else None,
            cta_label="Start with activities",
        ),
    ]


def _recommend_advanced_anchor(
    *,
    configuration: TripConfiguration,
) -> PlannerAdvancedAnchor:
    active_modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    trip_length_text = (configuration.trip_length or "").lower()
    has_short_trip_signal = any(
        signal in trip_length_text for signal in ["weekend", "3 day", "3-night", "3 night"]
    )
    route_is_soft = not configuration.from_location
    route_is_explicitly_flexible = has_flexible_origin(configuration)
    hotels_active = "hotels" in active_modules
    flights_active = "flights" in active_modules
    activities_active = "activities" in active_modules

    if activities_active and configuration.activity_styles:
        return "activities"
    if activities_active and configuration.custom_style:
        return "trip_style"
    if flights_active and not route_is_explicitly_flexible and (route_is_soft or has_short_trip_signal):
        return "flight"
    if hotels_active and not flights_active:
        return "stay"
    if hotels_active and not activities_active:
        return "stay"
    if activities_active:
        return "trip_style"
    return "stay"


def _advanced_anchor_title(anchor: PlannerAdvancedAnchor) -> str:
    return {
        "flight": "Flight",
        "stay": "Stay",
        "trip_style": "Trip Style",
        "activities": "Activities",
    }[anchor]


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
    ) and not configuration.from_location and not configuration.from_location_flexible:
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
    ) and "activities" in active_modules and not configuration.activity_styles and not configuration.custom_style:
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
    planning_mode: str | None,
    all_required_details_present: bool,
) -> str:
    if all_required_details_present:
        if planning_mode == "advanced":
            return "The core brief is almost ready. Review it here if you want to tweak anything, or confirm in chat and Wandrix can move into the first Advanced Planning anchor."
        return "Everything important is filled in. Review it on the board if you want to tweak anything, or confirm in chat and Wandrix can move ahead."

    active_modules = [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]
    if planning_mode == "advanced":
        if active_modules == ["activities"]:
            return (
                "Advanced Planning is staying focused on activities for now. "
                "Use the board to tighten destination, timing, travellers, and trip style, and leave flights or hotels for later if that is how you want to sequence the trip."
            )
        flexible_departure_line = (
            " Departure can still stay flexible for now if flights are in scope but you are not ready to lock the route yet."
            if configuration.selected_modules.flights and configuration.from_location_flexible
            else ""
        )
        return (
            "Advanced Planning works best once the trip brief is fuller. "
            "Use the board to lock the next trip details step by step before choosing the first planning anchor."
            f"{flexible_departure_line}"
        )
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
        from_location_flexible=configuration.from_location_flexible,
        to_location=configuration.to_location,
        selected_modules=configuration.selected_modules.model_copy(deep=True),
        travel_window=configuration.travel_window,
        trip_length=configuration.trip_length,
        weather_preference=configuration.weather_preference,
        start_date=configuration.start_date,
        end_date=configuration.end_date,
        adults=configuration.travelers.adults,
        children=configuration.travelers.children,
        travelers_flexible=configuration.travelers_flexible,
        activity_styles=list(configuration.activity_styles),
        custom_style=configuration.custom_style,
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


def _resolve_unconfirmed_destination_options(
    *,
    current: TripConversationState,
    llm_update: TripTurnUpdate,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    rejected_keys = {
        key
        for option in current.memory.rejected_options
        if option.kind == "destination"
        for key in _destination_option_keys(option.value)
    }

    candidates = [
        *llm_update.mentioned_options,
        *[
            ConversationOptionCandidate(kind=option.kind, value=option.value)
            for option in current.memory.mentioned_options
        ],
    ]

    for candidate in candidates:
        if candidate.kind != "destination":
            continue
        option_keys = _destination_option_keys(candidate.value)
        if option_keys.intersection(rejected_keys):
            continue
        normalized = _normalize_destination_value(candidate.value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(candidate.value.strip())

    return values[:3]


def _build_unresolved_destination_title(options: list[str]) -> str:
    if len(options) == 2:
        return f"{options[0]} and {options[1]} are both still in play"
    return f"{', '.join(options[:-1])}, and {options[-1]} are still in play"
