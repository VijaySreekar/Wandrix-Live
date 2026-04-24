from pydantic import BaseModel, Field

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
from app.integrations.llm.client import create_chat_model
from app.schemas.conversation import ConversationBoardAction
from app.schemas.trip_conversation import (
    AdvancedStayOptionCard,
    AdvancedStayHotelOptionCard,
    AdvancedStayHotelFilters,
    AdvancedAnchorChoiceCard,
    DestinationSuggestionCard,
    PlannerHotelResultsStatus,
    PlannerHotelSortOrder,
    PlannerHotelStyleTag,
    PlannerAdvancedAnchor,
    PlannerTripPace,
    PlannerTripDirectionAccent,
    PlannerTripDirectionPrimary,
    PlannerChecklistItem,
    PlanningModeChoiceCard,
    PlannerAdvancedStep,
    PlannerDecisionCard,
    TripDetailsCollectionFormState,
    TripConversationState,
    TripSuggestionBoardState,
)
from app.schemas.trip_planning import HotelStayDetail, TripConfiguration


OWN_CHOICE_PROMPT = "Tell me the destination you already have in mind."
HOTEL_WORKSPACE_PAGE_SIZE = 6


class _HotelCopyCandidate(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    summary: str = Field(..., min_length=1, max_length=240)
    why_it_fits: str = Field(..., min_length=1, max_length=220)
    tradeoffs: list[str] = Field(default_factory=list, max_length=3)


class _HotelCopyBundle(BaseModel):
    cards: list[_HotelCopyCandidate] = Field(default_factory=list, max_length=12)


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
        and advanced_step == "resolve_dates"
        and brief_confirmed
    ):
        return _build_advanced_date_resolution_state(current=current, configuration=configuration)

    if (
        current.planning_mode == "advanced"
        and advanced_step == "review"
        and brief_confirmed
    ):
        return _build_advanced_review_board_state(
            current=current,
            configuration=configuration,
        )

    if (
        current.planning_mode == "advanced"
        and advanced_step == "anchor_flow"
        and brief_confirmed
        and not (action and action.type == "revise_advanced_review_section")
        and _advanced_review_is_ready_for_board(
            current=current,
            configuration=configuration,
        )
    ):
        return _build_advanced_review_board_state(
            current=current,
            configuration=configuration,
        )

    if (
        current.planning_mode == "advanced"
        and advanced_step == "choose_anchor"
        and brief_confirmed
    ):
        return _build_advanced_anchor_choice_state(
            configuration=configuration,
            current=current,
        )

    if (
        current.planning_mode == "advanced"
        and advanced_step == "anchor_flow"
        and advanced_anchor is not None
    ):
        if advanced_anchor == "activities":
            stay_planning = current.stay_planning
            if (
                stay_planning.selection_status == "needs_review"
                or stay_planning.compatibility_status in {"strained", "conflicted"}
                or (
                    stay_planning.selected_hotel_id
                    and (
                        stay_planning.hotel_selection_status == "needs_review"
                        or stay_planning.hotel_compatibility_status
                        in {"strained", "conflicted"}
                    )
                )
            ):
                return _build_advanced_stay_board_state(
                    current=current,
                    configuration=configuration,
                )
            if current.activity_planning.completion_status == "completed":
                return _build_advanced_activities_completed_state(
                    current=current,
                    configuration=configuration,
                )
            return _build_advanced_activities_board_state(current=current, configuration=configuration)
        if advanced_anchor == "flight":
            if current.flight_planning.selection_status in {"completed", "kept_open"}:
                return _build_advanced_flights_completed_state(
                    current=current,
                    configuration=configuration,
                )
            return _build_advanced_flights_board_state(
                current=current,
                configuration=configuration,
            )
        if advanced_anchor == "trip_style":
            if current.trip_style_planning.substep == "completed":
                return _build_advanced_trip_style_completed_state(
                    current=current,
                    configuration=configuration,
                )
            if current.trip_style_planning.substep == "pace":
                return _build_advanced_trip_style_pace_board_state(
                    current=current,
                    configuration=configuration,
                )
            if current.trip_style_planning.substep == "tradeoffs":
                return _build_advanced_trip_style_tradeoffs_board_state(
                    current=current,
                    configuration=configuration,
                )
            return _build_advanced_trip_style_board_state(
                current=current,
                configuration=configuration,
            )
        if advanced_anchor == "stay":
            return _build_advanced_stay_board_state(
                current=current,
                configuration=configuration,
            )
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


def _build_advanced_date_resolution_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    date_resolution = current.advanced_date_resolution
    route_line = (
        "Departure can still stay flexible for now."
        if configuration.from_location_flexible
        else None
    )
    subtitle = (
        f"The brief for {destination} is almost ready. "
        "Before we choose the first Advanced Planning anchor, lock a working trip window so the next decisions are more grounded."
    )
    if route_line:
        subtitle = f"{subtitle} {route_line}"

    return TripSuggestionBoardState(
        mode="advanced_date_resolution",
        title="Choose a working trip window",
        subtitle=subtitle,
        have_details=[
            PlannerChecklistItem(
                id="destination",
                label="Destination",
                status="known",
                value=destination,
            ),
            PlannerChecklistItem(
                id="route",
                label="Route",
                status="known",
                value=(
                    f"{configuration.from_location} to {destination}"
                    if configuration.from_location
                    else "Departure can still stay flexible"
                    if configuration.from_location_flexible
                    else f"To {destination}"
                ),
            ),
        ],
        date_option_cards=date_resolution.recommended_date_options[:3],
        selected_date_option_id=date_resolution.selected_date_option_id,
        selected_start_date=date_resolution.selected_start_date,
        selected_end_date=date_resolution.selected_end_date,
        date_selection_status=date_resolution.selection_status,
        date_selection_rationale=date_resolution.selection_rationale,
        date_requires_confirmation=date_resolution.requires_confirmation,
        source_timing_text=date_resolution.source_timing_text,
        source_trip_length_text=date_resolution.source_trip_length_text,
        own_choice_prompt=None,
    )


def _build_advanced_anchor_choice_state(
    *,
    configuration: TripConfiguration,
    current: TripConversationState,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    completed_anchors = _resolve_completed_advanced_anchors(current=current)
    recommended_anchor = _recommend_advanced_anchor(
        configuration=configuration,
        completed_anchors=completed_anchors,
    )
    return TripSuggestionBoardState(
        mode="advanced_anchor_choice",
        title="Choose what to shape first",
        subtitle=(
            f"The brief for {destination} is strong enough now. "
            "Pick the first part of the trip to shape in more depth. Wandrix recommends one starting point, but you can choose any of the four."
        ),
        advanced_anchor_cards=_build_advanced_anchor_cards(
            recommended_anchor,
            completed_anchors=completed_anchors,
        ),
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
        title=f"{anchor_title} will shape this trip first",
        subtitle=(
            f"Advanced Planning is now centered on {anchor_title.lower()} for {destination}. "
            "The next step is turning that into the first deeper planning pass."
        ),
        own_choice_prompt=None,
    )


def _build_advanced_trip_style_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    trip_style_planning = current.trip_style_planning
    selected_primary = trip_style_planning.selected_primary_direction
    selected_accent = trip_style_planning.selected_accent

    subtitle = (
        f"Choose the main character for {destination} before we open activities in depth. "
        "The primary direction decides what Wandrix should push to the top, and the optional accent changes how those picks should feel."
    )
    if selected_primary:
        subtitle = (
            f"{destination} is currently leaning {_trip_direction_primary_label(selected_primary)}"
            f"{f' with a {_trip_direction_accent_label(selected_accent)} accent' if selected_accent else ''}. "
            "You can keep refining that here, then confirm it when the trip character feels right."
        )

    return TripSuggestionBoardState(
        mode="advanced_trip_style_direction",
        title="Set The Trip Character",
        subtitle=subtitle,
        trip_style_recommended_primaries=trip_style_planning.recommended_primary_directions,
        trip_style_recommended_accents=trip_style_planning.recommended_accents,
        selected_trip_style_primary=selected_primary,
        selected_trip_style_accent=selected_accent,
        trip_style_selection_status=trip_style_planning.selection_status,
        trip_style_substep=trip_style_planning.substep,
        trip_style_workspace_summary=trip_style_planning.workspace_summary,
        trip_style_selection_rationale=trip_style_planning.selection_rationale,
        trip_style_downstream_influence_summary=trip_style_planning.downstream_influence_summary,
        trip_style_completion_summary=trip_style_planning.completion_summary,
        own_choice_prompt=None,
    )


def _build_advanced_trip_style_pace_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    trip_style_planning = current.trip_style_planning
    selected_primary = trip_style_planning.selected_primary_direction
    selected_accent = trip_style_planning.selected_accent
    direction_label = (
        _trip_direction_primary_label(selected_primary)
        if selected_primary
        else "balanced"
    )
    accent_line = (
        f" with a {_trip_direction_accent_label(selected_accent)} accent"
        if selected_accent
        else ""
    )
    return TripSuggestionBoardState(
        mode="advanced_trip_style_pace",
        title="Set The Day Pace",
        subtitle=(
            f"The trip character is already {direction_label}{accent_line}. "
            f"Now choose how full the days in {destination} should feel before Activities opens."
        ),
        trip_style_recommended_primaries=trip_style_planning.recommended_primary_directions,
        trip_style_recommended_accents=trip_style_planning.recommended_accents,
        selected_trip_style_primary=selected_primary,
        selected_trip_style_accent=selected_accent,
        trip_style_selection_status=trip_style_planning.selection_status,
        trip_style_substep=trip_style_planning.substep,
        trip_style_workspace_summary=trip_style_planning.workspace_summary,
        trip_style_selection_rationale=trip_style_planning.selection_rationale,
        trip_style_downstream_influence_summary=trip_style_planning.downstream_influence_summary,
        trip_style_recommended_paces=trip_style_planning.recommended_paces,
        selected_trip_style_pace=trip_style_planning.selected_pace,
        trip_style_pace_status=trip_style_planning.pace_status,
        trip_style_pace_rationale=trip_style_planning.pace_rationale,
        trip_style_pace_downstream_influence_summary=(
            trip_style_planning.pace_downstream_influence_summary
        ),
        trip_style_completion_summary=trip_style_planning.completion_summary,
        own_choice_prompt=None,
    )


def _build_advanced_trip_style_tradeoffs_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    trip_style_planning = current.trip_style_planning
    selected_primary = trip_style_planning.selected_primary_direction
    selected_accent = trip_style_planning.selected_accent
    direction_label = (
        _trip_direction_primary_label(selected_primary)
        if selected_primary
        else "balanced"
    )
    accent_line = (
        f" with a {_trip_direction_accent_label(selected_accent)} accent"
        if selected_accent
        else ""
    )
    pace_line = (
        f" at a {_trip_pace_label(trip_style_planning.selected_pace).lower()} pace"
        if trip_style_planning.selected_pace
        else ""
    )
    return TripSuggestionBoardState(
        mode="advanced_trip_style_tradeoffs",
        title="Set The Final Tie-Breakers",
        subtitle=(
            f"{destination} is already shaped as {direction_label}{accent_line}{pace_line}. "
            "Now choose how Wandrix should break close calls when strong activity options compete."
        ),
        trip_style_recommended_primaries=trip_style_planning.recommended_primary_directions,
        trip_style_recommended_accents=trip_style_planning.recommended_accents,
        selected_trip_style_primary=selected_primary,
        selected_trip_style_accent=selected_accent,
        trip_style_selection_status=trip_style_planning.selection_status,
        trip_style_substep=trip_style_planning.substep,
        trip_style_workspace_summary=trip_style_planning.workspace_summary,
        trip_style_selection_rationale=trip_style_planning.selection_rationale,
        trip_style_downstream_influence_summary=trip_style_planning.downstream_influence_summary,
        trip_style_recommended_paces=trip_style_planning.recommended_paces,
        selected_trip_style_pace=trip_style_planning.selected_pace,
        trip_style_pace_status=trip_style_planning.pace_status,
        trip_style_pace_rationale=trip_style_planning.pace_rationale,
        trip_style_pace_downstream_influence_summary=(
            trip_style_planning.pace_downstream_influence_summary
        ),
        trip_style_recommended_tradeoff_cards=trip_style_planning.recommended_tradeoff_cards,
        selected_trip_style_tradeoffs=trip_style_planning.selected_tradeoffs,
        trip_style_tradeoff_status=trip_style_planning.tradeoff_status,
        trip_style_tradeoff_rationale=trip_style_planning.tradeoff_rationale,
        trip_style_tradeoff_downstream_influence_summary=(
            trip_style_planning.tradeoff_downstream_influence_summary
        ),
        trip_style_completion_summary=trip_style_planning.completion_summary,
        own_choice_prompt=None,
    )


def _build_advanced_trip_style_completed_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    completed_anchors = _resolve_completed_advanced_anchors(current=current)
    recommended_anchor = _recommend_advanced_anchor_after_trip_style(
        configuration=configuration,
        current=current,
    )
    completion_summary = (
        current.trip_style_planning.completion_summary
        or "The trip character is now clear enough to shape the next branch."
    )
    recommended_anchor_title = _advanced_anchor_title(recommended_anchor)
    return TripSuggestionBoardState(
        mode="advanced_anchor_choice",
        title="What should we plan next?",
        subtitle=(
            f"{completion_summary.rstrip('.')} "
            f"Wandrix recommends {recommended_anchor_title.lower()} as the next best move."
        ),
        advanced_anchor_cards=_build_advanced_anchor_cards(
            recommended_anchor,
            completed_anchors=completed_anchors,
        ),
        own_choice_prompt=None,
    )


def _build_advanced_flights_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    flight_planning = current.flight_planning
    subtitle = (
        flight_planning.workspace_summary
        or f"Choose the working outbound and return flight shape Wandrix should build around for {destination}."
    )
    if flight_planning.results_status == "blocked" and flight_planning.missing_requirements:
        subtitle = (
            f"Flight planning is waiting on {', '.join(flight_planning.missing_requirements)}. "
            "Once that is known, Wandrix can compare working outbound and return options."
        )
    return TripSuggestionBoardState(
        mode="advanced_flights_workspace",
        title="Choose Working Flights",
        subtitle=_limit_board_subtitle(subtitle),
        have_details=_build_flight_have_details(configuration),
        need_details=_build_flight_need_details(flight_planning.missing_requirements),
        flight_strategy_cards=flight_planning.strategy_cards,
        outbound_flight_options=flight_planning.outbound_options,
        return_flight_options=flight_planning.return_options,
        selected_flight_strategy=flight_planning.selected_strategy,
        selected_outbound_flight_id=flight_planning.selected_outbound_flight_id,
        selected_return_flight_id=flight_planning.selected_return_flight_id,
        selected_outbound_flight=flight_planning.selected_outbound_flight,
        selected_return_flight=flight_planning.selected_return_flight,
        flight_selection_status=flight_planning.selection_status,
        flight_results_status=flight_planning.results_status,
        flight_missing_requirements=flight_planning.missing_requirements,
        flight_workspace_summary=flight_planning.workspace_summary,
        flight_selection_summary=flight_planning.selection_summary,
        flight_downstream_notes=flight_planning.downstream_notes,
        flight_arrival_day_impact_summary=flight_planning.arrival_day_impact_summary,
        flight_departure_day_impact_summary=flight_planning.departure_day_impact_summary,
        flight_timing_review_notes=flight_planning.timing_review_notes,
        flight_completion_summary=flight_planning.completion_summary,
        weather_results_status=current.weather_planning.results_status,
        weather_workspace_summary=current.weather_planning.workspace_summary,
        weather_day_impact_summaries=current.weather_planning.day_impact_summaries,
        weather_activity_influence_notes=current.weather_planning.activity_influence_notes,
        own_choice_prompt=None,
    )


def _build_flight_have_details(
    configuration: TripConfiguration,
) -> list[PlannerChecklistItem]:
    items: list[PlannerChecklistItem] = []
    if configuration.from_location:
        items.append(
            PlannerChecklistItem(
                id="flight_origin",
                label="Origin",
                status="known",
                value=configuration.from_location,
            )
        )
    if configuration.to_location:
        items.append(
            PlannerChecklistItem(
                id="flight_destination",
                label="Destination",
                status="known",
                value=configuration.to_location,
            )
        )
    if configuration.start_date:
        items.append(
            PlannerChecklistItem(
                id="flight_departure_date",
                label="Departure",
                status="known",
                value=configuration.start_date.isoformat(),
            )
        )
    if configuration.end_date:
        items.append(
            PlannerChecklistItem(
                id="flight_return_date",
                label="Return",
                status="known",
                value=configuration.end_date.isoformat(),
            )
        )
    if configuration.travelers.adults:
        items.append(
            PlannerChecklistItem(
                id="flight_travelers",
                label="Travelers",
                status="known",
                value=f"{configuration.travelers.adults} adult{'s' if configuration.travelers.adults != 1 else ''}",
            )
        )
    elif configuration.travelers_flexible:
        items.append(
            PlannerChecklistItem(
                id="flight_travelers_flexible",
                label="Travelers",
                status="known",
                value="Flexible for now",
            )
        )
    return items


def _build_flight_need_details(
    missing_requirements: list[str],
) -> list[PlannerChecklistItem]:
    return [
        PlannerChecklistItem(
            id=f"flight_missing_{index}",
            label=requirement.capitalize(),
            status="needed",
            value=None,
        )
        for index, requirement in enumerate(missing_requirements, start=1)
    ]


def _build_advanced_flights_completed_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    completed_anchors = _resolve_completed_advanced_anchors(current=current)
    recommended_anchor = _recommend_advanced_anchor_after_flights(
        configuration=configuration,
        current=current,
    )
    completion_summary = (
        current.flight_planning.completion_summary
        or "Flights now have enough working shape for downstream planning."
    )
    recommended_anchor_title = _advanced_anchor_title(recommended_anchor)
    return TripSuggestionBoardState(
        mode="advanced_anchor_choice",
        title="What should we plan next?",
        subtitle=(
            f"{completion_summary.rstrip('.')} "
            f"Wandrix recommends {recommended_anchor_title.lower()} as the next best move."
        ),
        advanced_anchor_cards=_build_advanced_anchor_cards(
            recommended_anchor,
            completed_anchors=completed_anchors,
        ),
        own_choice_prompt=None,
    )


def _build_advanced_activities_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    activity_planning = current.activity_planning
    stay_label = current.stay_planning.selected_hotel_name or current.stay_planning.selected_stay_direction
    pace_label = (
        _trip_pace_label(current.trip_style_planning.selected_pace)
        if current.trip_style_planning.pace_status == "completed"
        else None
    )
    lead_event = next(
        (
            candidate
            for candidate in activity_planning.visible_candidates
            if candidate.kind == "event" and candidate.start_at is not None
        ),
        None,
    )
    subtitle = (
        f"Wandrix is narrowing {destination} down to the moments that feel most worth building around. "
        "Use the board to show what should lead the trip, what should stay in the mix, and what does not belong."
    )
    if stay_label:
        subtitle = (
            f"Wandrix is narrowing {destination} down to the moments that feel most worth building around, using {stay_label} as extra context where it helps. "
            "Use the board to show what should lead the trip, what should stay in the mix, and what does not belong."
        )
    if any(candidate.kind == "event" for candidate in activity_planning.recommended_candidates):
        subtitle += " Live events are mixed in when they genuinely fit the trip window."
    if pace_label:
        subtitle += f" The confirmed {pace_label.lower()} pace is shaping how many flexible ideas get placed into each day."
    if current.trip_style_planning.tradeoff_status == "completed":
        subtitle += " Trip Style tradeoffs now break close calls."
    if lead_event and activity_planning.visible_candidates:
        if activity_planning.visible_candidates[0].id == lead_event.id:
            subtitle = (
                f"{lead_event.title} is currently the strongest time-specific moment in {destination}, "
                "so Wandrix is shaping the shortlist around it. Keep it if it belongs at the heart of the trip, or leave it out and the rest of the shortlist will rebalance."
            )

    return TripSuggestionBoardState(
        mode="advanced_activities_workspace",
        title="Pick The Experiences That Matter Most",
        subtitle=_limit_board_subtitle(subtitle),
        activity_candidates=activity_planning.recommended_candidates,
        essential_ids=activity_planning.essential_ids,
        maybe_ids=activity_planning.maybe_ids,
        passed_ids=activity_planning.passed_ids,
        selected_event_ids=activity_planning.selected_event_ids,
        reserved_candidate_ids=activity_planning.reserved_candidate_ids,
        activity_workspace_summary=activity_planning.workspace_summary,
        activity_day_plans=activity_planning.day_plans,
        unscheduled_activity_candidate_ids=activity_planning.unscheduled_candidate_ids,
        activity_schedule_summary=activity_planning.schedule_summary,
        activity_schedule_notes=activity_planning.schedule_notes,
        activity_schedule_status=activity_planning.schedule_status,
        weather_results_status=current.weather_planning.results_status,
        weather_workspace_summary=current.weather_planning.workspace_summary,
        weather_day_impact_summaries=current.weather_planning.day_impact_summaries,
        weather_activity_influence_notes=current.weather_planning.activity_influence_notes,
        own_choice_prompt=None,
    )


def _limit_board_subtitle(value: str) -> str:
    if len(value) <= 320:
        return value
    return f"{value[:316].rstrip()}..."


def _build_advanced_activities_completed_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    completed_anchors = _resolve_completed_advanced_anchors(current=current)
    recommended_anchor = _recommend_advanced_anchor_after_activities(
        configuration=configuration,
        current=current,
    )
    completion_summary = (
        current.activity_planning.completion_summary
        or "The main experiences are now in place, so the trip can move forward."
    )
    recommended_anchor_title = _advanced_anchor_title(recommended_anchor)
    return TripSuggestionBoardState(
        mode="advanced_anchor_choice",
        title="What should we plan next?",
        subtitle=(
            f"{completion_summary.rstrip('.')} "
            "The board is back to the remaining planning choices now that this part of the trip feels settled. "
            f"Wandrix now recommends {recommended_anchor_title.lower()} as the next best move."
        ),
        advanced_anchor_cards=_build_advanced_anchor_cards(
            recommended_anchor,
            completed_anchors=completed_anchors,
        ),
        own_choice_prompt=None,
    )


def _build_advanced_review_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    review = current.advanced_review_planning
    destination = configuration.to_location or "this trip"
    title = "Review The Working Trip"
    subtitle = (
        review.workspace_summary
        or f"{destination} is ready for a calm check across the current planning choices."
    )
    return TripSuggestionBoardState(
        mode="advanced_review_workspace",
        title=title,
        subtitle=_limit_board_subtitle(subtitle),
        advanced_review_readiness_status=review.readiness_status,
        advanced_review_summary=review.workspace_summary,
        advanced_review_completed_summary=review.completed_summary,
        advanced_review_open_summary=review.open_summary,
        advanced_review_section_cards=review.section_cards,
        advanced_review_notes=review.review_notes,
        advanced_review_decision_signals=review.decision_signals,
        planner_conflicts=current.planner_conflicts,
        own_choice_prompt=None,
    )


def _recommend_advanced_anchor_after_activities(
    *,
    configuration: TripConfiguration,
    current: TripConversationState,
) -> PlannerAdvancedAnchor:
    completed_anchors = {"activities"}
    if current.stay_planning.selected_hotel_id:
        completed_anchors.add("stay")
    if current.trip_style_planning.substep == "completed":
        completed_anchors.add("trip_style")

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

    ranked_candidates: list[PlannerAdvancedAnchor] = []
    if activities_active and configuration.custom_style:
        ranked_candidates.append("trip_style")
    if flights_active and not route_is_explicitly_flexible and (route_is_soft or has_short_trip_signal):
        ranked_candidates.append("flight")
    if hotels_active and "stay" not in completed_anchors:
        ranked_candidates.append("stay")
    ranked_candidates.extend(["stay", "trip_style", "flight", "activities"])

    for candidate in ranked_candidates:
        if candidate not in completed_anchors:
            return candidate
    return "trip_style"


def _recommend_advanced_anchor_after_flights(
    *,
    configuration: TripConfiguration,
    current: TripConversationState,
) -> PlannerAdvancedAnchor:
    completed_anchors = {"flight"}
    if current.stay_planning.selected_hotel_id:
        completed_anchors.add("stay")
    if current.trip_style_planning.substep == "completed":
        completed_anchors.add("trip_style")
    if current.activity_planning.completion_status == "completed":
        completed_anchors.add("activities")

    if configuration.selected_modules.activities and "trip_style" not in completed_anchors:
        return "trip_style"
    if configuration.selected_modules.activities and "activities" not in completed_anchors:
        return "activities"
    if configuration.selected_modules.hotels and "stay" not in completed_anchors:
        return "stay"
    return _recommend_advanced_anchor(
        configuration=configuration,
        completed_anchors=completed_anchors,
    )


def _recommend_advanced_anchor_after_trip_style(
    *,
    configuration: TripConfiguration,
    current: TripConversationState,
) -> PlannerAdvancedAnchor:
    completed_anchors = {"trip_style"}
    if current.stay_planning.selected_hotel_id:
        completed_anchors.add("stay")
    if current.activity_planning.completion_status == "completed":
        completed_anchors.add("activities")

    if configuration.selected_modules.activities and "activities" not in completed_anchors:
        return "activities"
    if configuration.selected_modules.hotels and "stay" not in completed_anchors:
        return "stay"
    if configuration.selected_modules.flights and not has_flexible_origin(configuration):
        return "flight"
    return _recommend_advanced_anchor(
        configuration=configuration,
        completed_anchors=completed_anchors,
    )


def build_advanced_stay_options(
    *,
    configuration: TripConfiguration,
    segment_id: str,
) -> list[AdvancedStayOptionCard]:
    destination = configuration.to_location or "this trip"
    custom_style = (configuration.custom_style or "").lower()
    activity_styles = set(configuration.activity_styles)
    recommended_option_id = _recommend_stay_option_id(configuration)
    split_stay_signal = _has_explicit_split_stay_signal(configuration)
    if split_stay_signal and recommended_option_id == "stay_connected_hub":
        recommended_option_id = "stay_split_strategy"

    options = [
        AdvancedStayOptionCard(
            id="stay_central_base",
            segment_id=segment_id,
            strategy_type="single_base",
            title=f"Central base for {destination}",
            summary=(
                f"Stay in the most walkable part of {destination} so first-time highlights, easy dinners, and shorter transfer days stay simple."
            ),
            area_label="Most central neighbourhoods",
            best_for=[
                "Short trips that need easy orientation",
                "Mixing classic sights with flexible evenings",
                "Keeping arrival and departure days lighter",
            ],
            tradeoffs=[
                "Usually busier and a little pricier",
                "Less local calm at the start and end of the day",
            ],
            recommended=recommended_option_id == "stay_central_base",
            badge="Recommended" if recommended_option_id == "stay_central_base" else None,
            cta_label="Build around this base",
        ),
        AdvancedStayOptionCard(
            id="stay_food_forward",
            segment_id=segment_id,
            strategy_type="single_base",
            title="Food-forward neighbourhood base",
            summary=(
                f"Base the trip in a dining-led part of {destination} so the neighbourhood itself helps carry the evenings and slower wandering hours."
            ),
            area_label="Dining-led neighbourhoods",
            best_for=[
                "Food-led trips and slower evening plans",
                "Travellers who want the area itself to feel like part of the trip",
                "Building days around markets, cafes, and dinner reservations",
            ],
            tradeoffs=[
                "Can sit farther from classic first-time sights",
                "Evening energy may make the area feel busier",
            ],
            recommended=recommended_option_id == "stay_food_forward",
            badge="Recommended" if recommended_option_id == "stay_food_forward" else None,
            cta_label="Build around this base",
        ),
        AdvancedStayOptionCard(
            id="stay_quiet_local",
            segment_id=segment_id,
            strategy_type="single_base",
            title="Quieter local base",
            summary=(
                f"Choose a calmer local area so the trip starts and ends more gently, then travel in for the bigger anchor moments across {destination}."
            ),
            area_label="Calmer residential pockets",
            best_for=[
                "Relaxed pacing and easier mornings",
                "Longer stays where local rhythm matters",
                "Trips that value quieter nights over constant centrality",
            ],
            tradeoffs=[
                "Daily travel can need more planning",
                "Less spontaneous access to late evenings or headline sights",
            ],
            recommended=recommended_option_id == "stay_quiet_local",
            badge="Recommended" if recommended_option_id == "stay_quiet_local" else None,
            cta_label="Build around this base",
        ),
        AdvancedStayOptionCard(
            id="stay_split_strategy" if split_stay_signal else "stay_connected_hub",
            segment_id=segment_id,
            strategy_type="split_stay" if split_stay_signal else "single_base",
            title=(
                "Split the stay across two bases"
                if split_stay_signal
                else "Transit-connected hub base"
            ),
            summary=(
                f"Use two shorter bases across {destination} so different parts of the trip get their own better fit."
                if split_stay_signal
                else f"Use a well-connected base so Wandrix can keep day structure flexible even before every activity anchor in {destination} is locked."
            ),
            area_label=(
                "Two complementary areas"
                if split_stay_signal
                else "Transit-connected hub"
            ),
            best_for=[
                "Trips already leaning toward more than one area"
                if split_stay_signal
                else "Trips mixing several neighbourhoods or day trips",
                "Keeping options open while structure is still forming",
                "Arrival or departure days that need practical routing",
            ],
            tradeoffs=[
                "More packing and transition friction"
                if split_stay_signal
                else "The area can feel more practical than atmospheric",
                "The trip needs enough structure to justify it"
                if split_stay_signal
                else "You may travel out for the most characterful parts of the trip",
            ],
            recommended=recommended_option_id
            == ("stay_split_strategy" if split_stay_signal else "stay_connected_hub"),
            badge=(
                "Recommended"
                if recommended_option_id
                == ("stay_split_strategy" if split_stay_signal else "stay_connected_hub")
                else (
                    "Only if the trip really splits"
                    if split_stay_signal and "split" not in custom_style
                    else None
                )
            ),
            cta_label="Build around this base",
        ),
    ]

    if activity_styles or custom_style:
        for option in options:
            if option.id == "stay_food_forward" and (
                "food" in activity_styles or "food" in custom_style or "market" in custom_style
            ):
                option.best_for = [
                    "Food-led pacing with stronger evening texture",
                    *option.best_for[:2],
                ][:3]
            if option.id == "stay_quiet_local" and (
                "relaxed" in activity_styles
                or "romantic" in activity_styles
                or "luxury" in activity_styles
                or "slow" in custom_style
            ):
                option.best_for = [
                    "Trips that want a calmer daily rhythm",
                    *option.best_for[:2],
                ][:3]

    return options[:4]


def build_advanced_stay_hotel_options(
    *,
    configuration: TripConfiguration,
    selected_stay_option: AdvancedStayOptionCard,
    hotels: list[HotelStayDetail],
) -> list[AdvancedStayHotelOptionCard]:
    if not hotels:
        return []

    hotel_contexts: list[dict] = []
    for hotel in hotels:
        area_label = _normalize_hotel_area_label(hotel)
        style_tags = _derive_hotel_style_tags(
            hotel=hotel,
            area_label=area_label,
            selected_stay_option=selected_stay_option,
        )
        hotel_contexts.append(
            {
                "hotel": hotel,
                "area_label": area_label,
                "style_tags": style_tags,
                "fit_score": _hotel_fit_score(
                    hotel=hotel,
                    selected_stay_option=selected_stay_option,
                ),
            }
        )

    ranked_contexts = sorted(
        hotel_contexts,
        key=lambda item: (
            -item["fit_score"],
            item["hotel"].nightly_rate_amount
            if item["hotel"].nightly_rate_amount is not None
            else 10_000,
            item["hotel"].hotel_name.lower(),
        ),
    )

    llm_copy_by_id = _generate_hotel_card_copy(
        configuration=configuration,
        selected_stay_option=selected_stay_option,
        hotel_contexts=ranked_contexts[:4],
    )
    missing_visible_contexts = [
        context
        for context in ranked_contexts[:4]
        if context["hotel"].id not in llm_copy_by_id
    ]
    for context in missing_visible_contexts:
        retry_copy = _generate_single_hotel_card_copy(
            configuration=configuration,
            selected_stay_option=selected_stay_option,
            hotel_context=context,
        )
        if retry_copy:
            llm_copy_by_id[retry_copy.id] = retry_copy

    cards: list[AdvancedStayHotelOptionCard] = []
    for context in hotel_contexts:
        hotel = context["hotel"]
        area_label = context["area_label"]
        style_tags = context["style_tags"]
        score = context["fit_score"]
        llm_copy = llm_copy_by_id.get(hotel.id)
        cards.append(
            AdvancedStayHotelOptionCard(
                id=hotel.id,
                hotel_name=hotel.hotel_name,
                area=area_label or _fallback_stay_area_label(selected_stay_option),
                image_url=hotel.image_url,
                address=hotel.address,
                source_url=hotel.source_url,
                source_label=hotel.source_label,
                summary=llm_copy.summary
                if llm_copy
                else _build_hotel_summary(
                    hotel=hotel,
                    selected_stay_option=selected_stay_option,
                ),
                why_it_fits=llm_copy.why_it_fits
                if llm_copy
                else _build_hotel_fit_reason(
                    hotel=hotel,
                    selected_stay_option=selected_stay_option,
                ),
                tradeoffs=llm_copy.tradeoffs
                if llm_copy and llm_copy.tradeoffs
                else _build_hotel_tradeoffs(
                    hotel=hotel,
                    selected_stay_option=selected_stay_option,
                    style_tags=style_tags,
                ),
                style_tags=style_tags,
                fit_score=min(score * 10, 100),
                price_signal=_infer_hotel_price_signal(
                    hotel,
                    configuration=configuration,
                ),
                nightly_rate_amount=hotel.nightly_rate_amount,
                nightly_rate_currency=hotel.nightly_rate_currency,
                nightly_tax_amount=hotel.nightly_tax_amount,
                rate_provider_name=hotel.rate_provider_name,
                rate_note=_build_hotel_rate_note(hotel),
                check_in=hotel.check_in,
                check_out=hotel.check_out,
                recommended=False,
                cta_label="Use this hotel",
            )
        )

    return _sort_hotel_cards(cards, "best_fit")


def build_advanced_stay_hotel_workspace(
    *,
    configuration: TripConfiguration,
    selected_stay_option: AdvancedStayOptionCard,
    hotel_cards: list[AdvancedStayHotelOptionCard],
    filters: AdvancedStayHotelFilters,
    sort_order: PlannerHotelSortOrder,
    page: int,
    selected_hotel_id: str | None,
) -> dict:
    exact_dates_ready = bool(configuration.start_date and configuration.end_date)
    available_areas = _collect_available_hotel_areas(hotel_cards)
    available_styles = _collect_available_hotel_styles(hotel_cards)
    page_size = 4
    selected_card = next(
        (card for card in hotel_cards if card.id == selected_hotel_id),
        None,
    )
    sorted_cards = _sort_hotel_cards(hotel_cards, "best_fit")
    curated_cards = sorted_cards[:4]
    recommended_card_id = curated_cards[0].id if curated_cards else None

    if not exact_dates_ready:
        visible_cards = [
            card.model_copy(
                update={
                    "recommended": card.id == recommended_card_id,
                    "outside_active_filters": False,
                }
            )
            for card in curated_cards
        ]
        return {
            "hotel_cards": visible_cards,
            "hotel_results_status": "blocked",
            "hotel_results_summary": (
                "Hotel fit can still be discussed, but exact hotel comparison needs fixed dates first."
            ),
            "hotel_page": 1,
            "hotel_page_size": page_size,
            "hotel_total_results": len(visible_cards),
            "hotel_total_pages": 1,
            "available_hotel_areas": available_areas,
            "available_hotel_styles": available_styles,
            "selected_hotel_card": selected_card,
        }

    visible_cards = [
        card.model_copy(
            update={
                "recommended": card.id == recommended_card_id,
                "outside_active_filters": False,
            }
        )
        for card in curated_cards
    ]
    visible_count = len(visible_cards)
    if visible_count == 0 and not selected_card:
        summary = (
            "I couldn't shape a strong hotel set inside this stay direction yet."
        )
        results_status: PlannerHotelResultsStatus = "empty"
    else:
        count_phrase = (
            f"Here are {visible_count} hotel recommendations"
            if visible_count
            else "The selected hotel is still saved"
        )
        summary = f"{count_phrase} inside {selected_stay_option.title.lower()}."
        results_status = "ready"

    return {
        "hotel_cards": visible_cards,
        "hotel_results_status": results_status,
        "hotel_results_summary": summary,
        "hotel_page": 1,
        "hotel_page_size": page_size,
        "hotel_total_results": len(visible_cards),
        "hotel_total_pages": 1,
        "available_hotel_areas": available_areas,
        "available_hotel_styles": available_styles,
        "selected_hotel_card": selected_card,
    }


def _build_advanced_anchor_cards(
    recommended_anchor: PlannerAdvancedAnchor,
    *,
    completed_anchors: set[PlannerAdvancedAnchor] | None = None,
) -> list[AdvancedAnchorChoiceCard]:
    completed_anchors = completed_anchors or set()
    cards = [
        AdvancedAnchorChoiceCard(
            id="flight",
            title="Flight",
            description="Start with routing, departure practicality, and schedule shape before the rest of the trip.",
            bullets=[
                "Best for short breaks or route-sensitive trips",
                "Useful when departure certainty matters most",
                "Helps shape arrival and departure day pacing early",
            ],
            status="completed" if "flight" in completed_anchors else "available",
            recommended="flight" not in completed_anchors and recommended_anchor == "flight",
            badge="Completed"
            if "flight" in completed_anchors
            else "Recommended"
            if recommended_anchor == "flight"
            else None,
            cta_label="Completed" if "flight" in completed_anchors else "Start with flights",
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
            status="completed" if "stay" in completed_anchors else "available",
            recommended="stay" not in completed_anchors and recommended_anchor == "stay",
            badge="Completed"
            if "stay" in completed_anchors
            else "Recommended"
            if recommended_anchor == "stay"
            else None,
            cta_label="Completed" if "stay" in completed_anchors else "Start with stay",
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
            status="completed"
            if "trip_style" in completed_anchors
            else "available",
            recommended="trip_style" not in completed_anchors
            and recommended_anchor == "trip_style",
            badge="Completed"
            if "trip_style" in completed_anchors
            else "Recommended"
            if recommended_anchor == "trip_style"
            else None,
            cta_label="Completed"
            if "trip_style" in completed_anchors
            else "Start with trip style",
        ),
        AdvancedAnchorChoiceCard(
            id="activities",
            title="Activities",
            description="Start with the experiences that matter most, then let timing and stay adjust around them.",
            bullets=[
                "Best when must-do moments should shape the trip",
                "Useful for events, museum-heavy trips, or food-led routes",
                "Lets the days come together around real priorities first",
            ],
            status="completed"
            if "activities" in completed_anchors
            else "available",
            recommended="activities" not in completed_anchors
            and recommended_anchor == "activities",
            badge="Completed"
            if "activities" in completed_anchors
            else "Recommended"
            if recommended_anchor == "activities"
            else None,
            cta_label="Completed"
            if "activities" in completed_anchors
            else "Start with experiences",
        ),
    ]
    available_cards = [card for card in cards if card.status == "available"]
    completed_cards = [card for card in cards if card.status == "completed"]
    return [*available_cards, *completed_cards]


def _recommend_advanced_anchor(
    *,
    configuration: TripConfiguration,
    completed_anchors: set[PlannerAdvancedAnchor] | None = None,
) -> PlannerAdvancedAnchor:
    completed_anchors = completed_anchors or set()
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

    ranked_candidates: list[PlannerAdvancedAnchor] = []
    if activities_active and configuration.activity_styles:
        ranked_candidates.append("activities")
    if activities_active and configuration.custom_style:
        ranked_candidates.append("trip_style")
    if activities_active:
        ranked_candidates.append("trip_style")
    if flights_active and not route_is_explicitly_flexible and (route_is_soft or has_short_trip_signal):
        ranked_candidates.append("flight")
    if hotels_active and not flights_active:
        ranked_candidates.append("stay")
    if hotels_active and not activities_active:
        ranked_candidates.append("stay")
    ranked_candidates.extend(["stay", "activities", "trip_style", "flight"])

    for candidate in ranked_candidates:
        if candidate not in completed_anchors:
            return candidate
    return "activities"


def _resolve_completed_advanced_anchors(
    *,
    current: TripConversationState,
) -> set[PlannerAdvancedAnchor]:
    completed: set[PlannerAdvancedAnchor] = set()
    stay_planning = current.stay_planning
    activity_planning = current.activity_planning
    if stay_planning.selected_hotel_id:
        completed.add("stay")
    if current.trip_style_planning.substep == "completed":
        completed.add("trip_style")
    if activity_planning.completion_status == "completed":
        completed.add("activities")
    if current.flight_planning.selection_status in {"completed", "kept_open"}:
        completed.add("flight")
    return completed


def _advanced_review_is_ready_for_board(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> bool:
    required: set[PlannerAdvancedAnchor] = set()
    if configuration.selected_modules.flights:
        required.add("flight")
    if configuration.selected_modules.hotels:
        required.add("stay")
    if configuration.selected_modules.activities:
        required.update({"trip_style", "activities"})
    if not required:
        return False
    return required.issubset(_resolve_completed_advanced_anchors(current=current))


def _build_advanced_stay_board_state(
    *,
    current: TripConversationState,
    configuration: TripConfiguration,
) -> TripSuggestionBoardState:
    destination = configuration.to_location or "this trip"
    stay_planning = current.stay_planning
    stay_cards = stay_planning.recommended_stay_options[:4]
    selected_card = next(
        (
            card
            for card in stay_cards
            if card.id == stay_planning.selected_stay_option_id
        ),
        None,
    )

    common_fields = {
        "stay_cards": stay_cards,
        "hotel_cards": stay_planning.recommended_hotels[:8],
        "selected_stay_option_id": stay_planning.selected_stay_option_id,
        "stay_selection_status": stay_planning.selection_status,
        "stay_selection_rationale": stay_planning.selection_rationale,
        "stay_selection_assumptions": stay_planning.selection_assumptions,
        "stay_compatibility_status": stay_planning.compatibility_status,
        "stay_compatibility_notes": stay_planning.compatibility_notes,
        "selected_hotel_id": stay_planning.selected_hotel_id,
        "selected_hotel_name": stay_planning.selected_hotel_name,
        "hotel_selection_status": stay_planning.hotel_selection_status,
        "hotel_selection_rationale": stay_planning.hotel_selection_rationale,
        "hotel_selection_assumptions": stay_planning.hotel_selection_assumptions,
        "hotel_compatibility_status": stay_planning.hotel_compatibility_status,
        "hotel_compatibility_notes": stay_planning.hotel_compatibility_notes,
        "hotel_filters": stay_planning.hotel_filters,
        "hotel_sort_order": stay_planning.hotel_sort_order,
        "hotel_results_status": stay_planning.hotel_results_status,
        "hotel_results_summary": stay_planning.hotel_results_summary,
        "hotel_page": stay_planning.hotel_page,
        "hotel_page_size": stay_planning.hotel_page_size,
        "hotel_total_results": stay_planning.hotel_total_results,
        "hotel_total_pages": stay_planning.hotel_total_pages,
        "available_hotel_areas": stay_planning.available_hotel_areas,
        "available_hotel_styles": stay_planning.available_hotel_styles,
        "selected_hotel_card": stay_planning.selected_hotel_card,
    }

    if stay_planning.selection_status == "needs_review" or stay_planning.compatibility_status in {
        "strained",
        "conflicted",
    }:
        review_lead = next(
            (
                card.title
                for card in stay_cards
                if card.recommended and card.id != stay_planning.selected_stay_option_id
            ),
            None,
        )
        title = "This base needs a second look"
        subtitle = (
            stay_planning.compatibility_notes[0]
            if stay_planning.compatibility_notes
            else (
                f"The selected stay direction for {destination} is still saved, but newer planning evidence means it should be reviewed before Wandrix goes deeper."
            )
        )
        if review_lead:
            subtitle = f"{subtitle.rstrip('.')} Wandrix has re-ranked the stay directions, led now by {review_lead}."
        return TripSuggestionBoardState(
            mode="advanced_stay_review",
            title=title,
            subtitle=subtitle,
            own_choice_prompt=None,
            **common_fields,
        )

    if selected_card:
        if (
            stay_planning.hotel_selection_status == "needs_review"
            or stay_planning.hotel_compatibility_status in {"strained", "conflicted"}
        ) and stay_planning.selected_hotel_id:
            review_hotel_lead = next(
                (
                    hotel.hotel_name
                    for hotel in stay_planning.recommended_hotels
                    if hotel.recommended and hotel.id != stay_planning.selected_hotel_id
                ),
                None,
            )
            return TripSuggestionBoardState(
                mode="advanced_stay_hotel_review",
                title=f"{selected_card.title} still leads, but the hotel needs a second look",
                subtitle=(
                    (
                        f"{stay_planning.hotel_compatibility_notes[0].rstrip('.')} "
                        f"Wandrix has re-ranked the hotel options, led now by {review_hotel_lead}."
                    )
                    if stay_planning.hotel_compatibility_notes and review_hotel_lead
                    else stay_planning.hotel_compatibility_notes[0]
                    if stay_planning.hotel_compatibility_notes
                    else (
                        f"The selected hotel inside {selected_card.title.lower()} should be reviewed before Wandrix keeps building deeper around it."
                    )
                ),
                own_choice_prompt=None,
                **common_fields,
            )

        if stay_planning.selected_hotel_id:
            completed_anchors = {"stay"}
            recommended_anchor = _recommend_advanced_anchor(
                configuration=configuration,
                completed_anchors=completed_anchors,
            )
            return TripSuggestionBoardState(
                mode="advanced_anchor_choice",
                title="What should we plan next?",
                subtitle=(
                    f"{stay_planning.selected_hotel_name or 'The hotel'} is now the working hotel inside {selected_card.title.lower()}. "
                    "Stay is in place, so pick the next planning anchor and I'll keep building from there."
                ),
                advanced_anchor_cards=_build_advanced_anchor_cards(
                    recommended_anchor,
                    completed_anchors=completed_anchors,
                ),
                own_choice_prompt=None,
            )

        if stay_planning.recommended_hotels or stay_planning.hotel_results_status in {"blocked", "empty"}:
            workspace_subtitle = (
                "Hotel fit can still be discussed here, but exact hotel comparison needs fixed dates first."
                if stay_planning.hotel_results_status == "blocked"
                else (
                    stay_planning.hotel_results_summary
                    or "Use the workspace to narrow the live hotel shortlist inside this stay direction."
                )
            )
            return TripSuggestionBoardState(
                mode="advanced_stay_hotel_choice",
                title=f"Hotel options inside {selected_card.title.lower()}",
                subtitle=(
                    f"{workspace_subtitle} These are working hotel options, not booked stays."
                ),
                own_choice_prompt=None,
                **common_fields,
            )

        return TripSuggestionBoardState(
            mode="advanced_stay_selected",
            title=f"{selected_card.title} is the working stay direction",
            subtitle=(
                f"Wandrix is now building around this stay strategy for {destination}. "
                "It stays revisable if activities, flights, or trip style later pull the trip in a different direction."
            ),
            own_choice_prompt=None,
            **common_fields,
        )

    return TripSuggestionBoardState(
        mode="advanced_stay_choice",
        title="Choose the stay direction to build around",
        subtitle=(
            f"These four stay strategies are working options for {destination}. "
            "Pick the one Wandrix should build around first. This is a planning direction, not a hotel lock, and it can be reviewed later."
        ),
        own_choice_prompt=None,
        **common_fields,
    )


def _recommend_stay_option_id(configuration: TripConfiguration) -> str:
    trip_length_text = (configuration.trip_length or "").lower()
    custom_style = (configuration.custom_style or "").lower()
    activity_styles = set(configuration.activity_styles)

    if "food" in activity_styles or "food" in custom_style or "market" in custom_style:
        return "stay_food_forward"
    if (
        "relaxed" in activity_styles
        or "romantic" in activity_styles
        or "luxury" in activity_styles
        or "slow" in custom_style
    ):
        return "stay_quiet_local"
    if any(signal in trip_length_text for signal in ["weekend", "3 day", "3-night", "3 night"]):
        return "stay_central_base"
    return "stay_connected_hub"


def _has_explicit_split_stay_signal(configuration: TripConfiguration) -> bool:
    custom_style = (configuration.custom_style or "").lower()
    trip_length = (configuration.trip_length or "").lower()
    explicit_signals = [
        "split stay",
        "split-stay",
        "split the stay",
        "two base",
        "two-base",
        "two bases",
        "multi base",
        "multi-base",
    ]
    return any(signal in custom_style or signal in trip_length for signal in explicit_signals)


def _advanced_anchor_title(anchor: PlannerAdvancedAnchor) -> str:
    return {
        "flight": "Flight",
        "stay": "Stay",
        "trip_style": "Trip Style",
        "activities": "Activities",
    }[anchor]


def _trip_direction_primary_label(primary: PlannerTripDirectionPrimary) -> str:
    return {
        "food_led": "food-led",
        "culture_led": "culture-led",
        "nightlife_led": "nightlife-led",
        "outdoors_led": "outdoors-led",
        "balanced": "balanced",
    }[primary]


def _trip_direction_accent_label(accent: PlannerTripDirectionAccent) -> str:
    return {
        "local": "local",
        "classic": "classic",
        "polished": "polished",
        "romantic": "romantic",
        "relaxed": "relaxed",
    }[accent]


def _trip_pace_label(pace: PlannerTripPace) -> str:
    return {
        "slow": "Slow",
        "balanced": "Balanced",
        "full": "Full",
    }[pace]


def _hotel_fit_score(
    *,
    hotel: HotelStayDetail,
    selected_stay_option: AdvancedStayOptionCard,
) -> int:
    haystack = " ".join(
        [hotel.hotel_name, hotel.area or "", *hotel.notes]
    ).lower()
    option_id = selected_stay_option.id
    score = 0

    if option_id == "stay_central_base":
        score += _keyword_score(haystack, ["central", "downtown", "center", "old town"])
    elif option_id == "stay_food_forward":
        score += _keyword_score(
            haystack,
            ["food", "market", "dining", "restaurant", "gion", "pontocho"],
        )
    elif option_id == "stay_quiet_local":
        score += _keyword_score(
            haystack,
            ["quiet", "calm", "residential", "local", "peaceful"],
        )
    else:
        score += _keyword_score(
            haystack,
            ["station", "transport", "connected", "hub", "access"],
        )

    if hotel.area:
        score += 2
    if any("tripadvisor:" in note.lower() for note in hotel.notes):
        score += 1
    return score


def _derive_hotel_style_tags(
    *,
    hotel: HotelStayDetail,
    area_label: str | None,
    selected_stay_option: AdvancedStayOptionCard,
) -> list[PlannerHotelStyleTag]:
    haystack = " ".join(
        [
            hotel.hotel_name,
            area_label or "",
            hotel.area or "",
            hotel.address or "",
            *hotel.notes,
        ]
    ).lower()
    tags: list[PlannerHotelStyleTag] = []

    def add(tag: PlannerHotelStyleTag) -> None:
        if tag not in tags:
            tags.append(tag)

    if any(
        keyword in haystack
        for keyword in [
            "quiet",
            "calm",
            "residential",
            "peaceful",
            "higashiyama",
            "retreat",
            "garden",
            "temple",
            "tou",
        ]
    ):
        add("calm")
    if any(
        keyword in haystack
        for keyword in [
            "central",
            "center",
            "downtown",
            "old town",
            "nakagyo",
            "kawaramachi",
            "sanjo",
            "cross hotel",
        ]
    ):
        add("central")
    if any(
        keyword in haystack
        for keyword in [
            "design",
            "boutique",
            "stylish",
            "minimal",
            "ace hotel",
            "atelier",
            "gallery",
        ]
    ):
        add("design")
    if any(
        keyword in haystack
        for keyword in [
            "luxury",
            "five-star",
            "five star",
            "hyatt",
            "ritz",
            "regency",
            "four seasons",
        ]
    ):
        add("luxury")
    if any(
        keyword in haystack
        for keyword in [
            "food",
            "market",
            "restaurant",
            "gion",
            "pontocho",
            "nishiki",
            "kawaramachi",
            "sanjo",
        ]
    ):
        add("food_access")
    if any(
        keyword in haystack
        for keyword in [
            "station",
            "practical",
            "connected",
            "access",
            "hub",
            "shimogyo",
            "transit",
            "business",
            "airport",
        ]
    ):
        add("practical")
    if any(
        keyword in haystack
        for keyword in [
            "machiya",
            "traditional",
            "ryokan",
            "heritage",
            "historic",
            "higashiyama",
            "gion",
        ]
    ):
        add("traditional")
    if any(
        keyword in haystack
        for keyword in [
            "nightlife",
            "late-night",
            "late night",
            "bar",
            "cocktail",
            "pontocho",
            "kawaramachi",
            "gion",
        ]
    ):
        add("nightlife")
    if any(
        keyword in haystack
        for keyword in [
            "walkable",
            "walk",
            "steps from",
            "short walk",
            "central",
            "sanjo",
            "downtown",
        ]
    ):
        add("walkable")
    if any(
        keyword in haystack
        for keyword in [
            "value",
            "affordable",
            "budget",
            "deal",
            "smart value",
        ]
    ):
        add("value")
    if hotel.nightly_rate_amount is not None and hotel.nightly_rate_amount < 160:
        add("value")

    strategy_to_default_tag: dict[str, PlannerHotelStyleTag] = {
        "stay_food_forward": "food_access",
        "stay_quiet_local": "calm",
        "stay_central_base": "central",
        "stay_connected_hub": "practical",
    }
    default_tag = strategy_to_default_tag.get(selected_stay_option.id)
    if default_tag:
        add(default_tag)

    return tags[:5]


def _normalize_hotel_area_label(hotel: HotelStayDetail) -> str | None:
    for candidate in [hotel.area, hotel.address]:
        normalized = _extract_ward_label(candidate)
        if normalized:
            return normalized

    for candidate in [hotel.area, hotel.address]:
        district = _extract_known_district_label(candidate)
        if district:
            return district

    if hotel.area and "prefecture" not in hotel.area.lower():
        return hotel.area

    return hotel.area or _extract_area_from_notes(hotel.notes)


def _extract_ward_label(value: str | None) -> str | None:
    if not value:
        return None

    normalized = " ".join(value.replace("/", " ").split())
    for chunk in [part.strip() for part in normalized.split(",")]:
        lower = chunk.lower()
        if lower.endswith("-ku") or " ward" in lower:
            return chunk
    return None


def _extract_area_from_notes(notes: list[str]) -> str | None:
    for note in notes:
        if note.lower().startswith("area fit:"):
            return note.split(":", 1)[1].strip().title()
    return None


def _extract_known_district_label(value: str | None) -> str | None:
    if not value:
        return None

    district_map = {
        "gion": "Gion",
        "pontocho": "Pontocho",
        "nakagyo": "Nakagyo-ku",
        "shimogyo": "Shimogyo-ku",
        "higashiyama": "Higashiyama-ku",
        "karasuma": "Karasuma",
        "kawaramachi": "Kawaramachi",
        "kyoto station": "Kyoto Station",
        "kiyomizu": "Kiyomizu / Higashiyama",
        "arashiyama": "Arashiyama",
    }

    lower_value = value.lower()
    for needle, label in district_map.items():
        if needle in lower_value:
            return label
    return None


def _fallback_stay_area_label(selected_stay_option: AdvancedStayOptionCard) -> str | None:
    return (
        selected_stay_option.area_label
        or (selected_stay_option.areas[0] if selected_stay_option.areas else None)
    )


def _collect_available_hotel_areas(
    hotel_cards: list[AdvancedStayHotelOptionCard],
) -> list[str]:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for card in hotel_cards:
        area = (card.area or "").strip()
        normalized = area.lower()
        if not area:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
        labels.setdefault(normalized, area)
    return [
        labels[key]
        for key in sorted(
            counts.keys(),
            key=lambda key: (-counts[key], labels[key].lower()),
        )
    ][:16]


def _collect_available_hotel_styles(
    hotel_cards: list[AdvancedStayHotelOptionCard],
) -> list[PlannerHotelStyleTag]:
    counts: dict[PlannerHotelStyleTag, int] = {}
    for card in hotel_cards:
        for tag in card.style_tags:
            counts[tag] = counts.get(tag, 0) + 1
    preferred_order: list[PlannerHotelStyleTag] = [
        "central",
        "walkable",
        "food_access",
        "calm",
        "practical",
        "traditional",
        "design",
        "nightlife",
        "value",
        "luxury",
    ]
    return [
        tag
        for tag in sorted(
            counts.keys(),
            key=lambda tag: (
                -counts[tag],
                preferred_order.index(tag) if tag in preferred_order else len(preferred_order),
            ),
        )
    ][:10]


def _hotel_card_matches_filters(
    card: AdvancedStayHotelOptionCard,
    filters: AdvancedStayHotelFilters,
) -> bool:
    if (
        filters.max_nightly_rate is not None
        and card.nightly_rate_amount is not None
        and card.nightly_rate_amount > filters.max_nightly_rate
    ):
        return False

    if filters.area_filter and (card.area or "").strip().lower() != filters.area_filter.strip().lower():
        return False

    if filters.style_filter and filters.style_filter not in card.style_tags:
        return False

    return True


def _sort_hotel_cards(
    hotel_cards: list[AdvancedStayHotelOptionCard],
    sort_order: PlannerHotelSortOrder,
) -> list[AdvancedStayHotelOptionCard]:
    def price_key(card: AdvancedStayHotelOptionCard) -> float:
        return card.nightly_rate_amount if card.nightly_rate_amount is not None else float("inf")

    if sort_order == "lowest_price":
        return sorted(
            hotel_cards,
            key=lambda card: (
                card.nightly_rate_amount is None,
                price_key(card),
                -card.fit_score,
                card.hotel_name.lower(),
            ),
        )

    if sort_order == "highest_price":
        return sorted(
            hotel_cards,
            key=lambda card: (
                card.nightly_rate_amount is None,
                -(card.nightly_rate_amount or -1),
                -card.fit_score,
                card.hotel_name.lower(),
            ),
        )

    if sort_order == "best_area_fit":
        return sorted(
            hotel_cards,
            key=lambda card: (
                -card.fit_score,
                card.area is None,
                price_key(card),
                card.hotel_name.lower(),
            ),
        )

    return sorted(
        hotel_cards,
        key=lambda card: (
            -card.fit_score,
            card.nightly_rate_amount is None,
            price_key(card),
            card.hotel_name.lower(),
        ),
    )


def _build_hotel_filter_summary(
    *,
    filters: AdvancedStayHotelFilters,
    sort_order: PlannerHotelSortOrder,
) -> str:
    parts: list[str] = []
    if filters.max_nightly_rate is not None:
        parts.append(f"nightly rates at or below {_format_hotel_amount(filters.max_nightly_rate, 'GBP')}")
    if filters.area_filter:
        parts.append(filters.area_filter)
    if filters.style_filter:
        parts.append(filters.style_filter.replace("_", " "))

    sort_label = {
        "best_fit": "best fit",
        "lowest_price": "lowest price",
        "highest_price": "highest price",
        "best_area_fit": "best area fit",
    }[sort_order]
    parts.append(f"sorted by {sort_label}")
    return ", ".join(parts)


def _keyword_score(haystack: str, keywords: list[str]) -> int:
    return sum(2 if keyword in haystack else 0 for keyword in keywords)


def _build_hotel_summary(
    *,
    hotel: HotelStayDetail,
    selected_stay_option: AdvancedStayOptionCard,
) -> str:
    area = hotel.area or "this part of the destination"
    if selected_stay_option.id == "stay_food_forward":
        return f"{hotel.hotel_name} keeps the trip rooted in {area}, with better odds of easy food-led wandering after the main daytime anchors."
    if selected_stay_option.id == "stay_quiet_local":
        return f"{hotel.hotel_name} leans into a calmer base around {area}, which fits slower mornings and a less hectic return at the end of the day."
    if selected_stay_option.id == "stay_central_base":
        return f"{hotel.hotel_name} keeps the trip practical around {area}, making first-time highlights and shorter transfer days easier to manage."
    return f"{hotel.hotel_name} gives Wandrix a better-connected base around {area}, so later day structure can stay flexible without constantly fighting the route."


def _build_hotel_fit_reason(
    *,
    hotel: HotelStayDetail,
    selected_stay_option: AdvancedStayOptionCard,
) -> str:
    area = hotel.area or "this area"
    if selected_stay_option.id == "stay_food_forward":
        return f"It fits the selected stay direction because {area} should make dinners, markets, and slower neighbourhood time feel like part of the trip rather than a detour."
    if selected_stay_option.id == "stay_quiet_local":
        return f"It fits because {area} looks more aligned with the calmer local rhythm this stay strategy is trying to protect."
    if selected_stay_option.id == "stay_central_base":
        return f"It fits because {area} should keep classic sights and first-day logistics more straightforward."
    return f"It fits because {area} looks more practical for moving around the trip without overcommitting to one atmospheric pocket too early."


def _generate_hotel_card_copy(
    *,
    configuration: TripConfiguration,
    selected_stay_option: AdvancedStayOptionCard,
    hotel_contexts: list[dict],
) -> dict[str, _HotelCopyCandidate]:
    if not hotel_contexts:
        return {}

    hotel_payload = []
    for context in hotel_contexts[:8]:
        hotel: HotelStayDetail = context["hotel"]
        hotel_payload.append(
            {
                "id": hotel.id,
                "hotel_name": hotel.hotel_name,
                "area": context["area_label"] or _fallback_stay_area_label(selected_stay_option),
                "style_tags": context["style_tags"],
                "nightly_rate_amount": hotel.nightly_rate_amount,
                "nightly_rate_currency": hotel.nightly_rate_currency,
                "notes": hotel.notes[:4],
                "fit_score": context["fit_score"],
            }
        )

    prompt = f"""
You are writing Wandrix hotel recommendation copy for the live trip board.

Write copy for each hotel so it feels specific, human, and useful.

Rules:
- Be concise and concrete.
- Do not repeat the same sentence structure across every hotel.
- Make the wording feel tailored to the hotel and the selected stay direction.
- Avoid generic planner language like "aligned with the stay strategy" or "working choice."
- `summary` should be one short sentence about what kind of stay this hotel gives.
- `why_it_fits` should be one short sentence explaining why it fits this trip direction specifically.
- `tradeoffs` should be 1 to 3 short hotel-specific tradeoffs, not copied stay-strategy warnings.
- Do not mention booking mechanics.
- Do not mention Wandrix.
- Keep all output factual enough for a planning board; do not invent amenities you were not given.
- Mention price only when it clearly changes the tradeoff.

Destination: {configuration.to_location or "this trip"}
Stay direction:
{selected_stay_option.model_dump(mode="json")}

Hotels:
{hotel_payload}
""".strip()

    try:
        model = create_chat_model(temperature=0.3)
        structured_model = model.with_structured_output(
            _HotelCopyBundle,
            method="json_schema",
        )
        result = structured_model.invoke(
            [
                ("system", "Write specific structured hotel-card copy for Wandrix."),
                ("human", prompt),
            ]
        )
        return {item.id: item for item in result.cards}
    except Exception:
        return {}


def _generate_single_hotel_card_copy(
    *,
    configuration: TripConfiguration,
    selected_stay_option: AdvancedStayOptionCard,
    hotel_context: dict,
) -> _HotelCopyCandidate | None:
    hotel: HotelStayDetail = hotel_context["hotel"]
    prompt = f"""
Write hotel card copy for one Wandrix hotel recommendation.

Rules:
- Be specific and concise.
- Avoid generic planner phrasing.
- `summary` should describe the kind of stay this hotel gives.
- `why_it_fits` should explain why it fits this stay direction.
- `tradeoffs` should be 1 to 3 hotel-specific tradeoffs.
- Do not mention booking mechanics.
- Do not mention Wandrix.

Destination: {configuration.to_location or "this trip"}
Stay direction:
{selected_stay_option.model_dump(mode="json")}

Hotel:
{{
  "id": "{hotel.id}",
  "hotel_name": "{hotel.hotel_name}",
  "area": "{hotel_context['area_label'] or _fallback_stay_area_label(selected_stay_option)}",
  "style_tags": {hotel_context["style_tags"]},
  "nightly_rate_amount": {hotel.nightly_rate_amount},
  "nightly_rate_currency": "{hotel.nightly_rate_currency}",
  "notes": {hotel.notes[:4]},
  "fit_score": {hotel_context["fit_score"]}
}}
""".strip()

    try:
        model = create_chat_model(temperature=0.3)
        structured_model = model.with_structured_output(
            _HotelCopyCandidate,
            method="json_schema",
        )
        return structured_model.invoke(
            [
                ("system", "Write one specific structured hotel-card copy block for Wandrix."),
                ("human", prompt),
            ]
        )
    except Exception:
        return None


def _build_hotel_tradeoffs(
    *,
    hotel: HotelStayDetail,
    selected_stay_option: AdvancedStayOptionCard,
    style_tags: list[PlannerHotelStyleTag] | None = None,
) -> list[str]:
    tradeoffs: list[str] = []
    style_tags_set = set(style_tags or [])

    if selected_stay_option.id == "stay_quiet_local":
        if "central" in style_tags_set or "nightlife" in style_tags_set:
            tradeoffs.append("This base may feel busier than the quieter stay direction suggests.")
        elif "practical" in style_tags_set:
            tradeoffs.append("The feel may land more functional than atmospheric.")
        elif "luxury" in style_tags_set:
            tradeoffs.append("Comfort is stronger here, but it softens the simpler local feel.")
    elif selected_stay_option.id == "stay_food_forward":
        if "calm" in style_tags_set:
            tradeoffs.append("The area may wind down earlier than a food-led trip sometimes wants.")
        elif "practical" in style_tags_set:
            tradeoffs.append("It may work better for logistics than for lingering neighbourhood evenings.")
    elif selected_stay_option.id == "stay_central_base":
        if "calm" in style_tags_set:
            tradeoffs.append("The calmer setting can trade away some of the easy first-time momentum.")
        elif "traditional" in style_tags_set:
            tradeoffs.append("Character is stronger here, but daily movement may feel a touch less effortless.")
    elif selected_stay_option.id == "stay_connected_hub":
        if "design" in style_tags_set or "luxury" in style_tags_set:
            tradeoffs.append("The stay experience is stronger here, but it matters less if routing is the main goal.")
        elif "traditional" in style_tags_set:
            tradeoffs.append("Atmosphere is stronger here, though the base may feel less purely practical.")

    if hotel.nightly_rate_amount is None:
        tradeoffs.append("Lock exact dates later to compare live nightly prices.")
    elif hotel.nightly_rate_amount >= 260:
        tradeoffs.append("Price climbs fast once the shortlist tightens.")
    elif hotel.nightly_rate_amount <= 140:
        tradeoffs.append("The lower rate may come with a simpler overall feel.")

    if "food_access" in style_tags_set and selected_stay_option.id != "stay_food_forward":
        tradeoffs.append("Dinner-heavy streets nearby can make the area feel busier after dark.")
    if "luxury" in style_tags_set and hotel.nightly_rate_amount and hotel.nightly_rate_amount >= 180:
        tradeoffs.append("You are paying more here for comfort and finish, not just location.")

    if not tradeoffs:
        tradeoffs.append("Worth checking against the rest of the shortlist once more of the trip locks in.")

    deduped: list[str] = []
    for item in tradeoffs:
        if item not in deduped:
            deduped.append(item)
    return deduped[:3]


def _infer_hotel_price_signal(
    hotel: HotelStayDetail,
    *,
    configuration: TripConfiguration,
) -> str | None:
    if hotel.nightly_rate_amount is not None:
        if hotel.nightly_rate_amount < 140:
            return "budget-friendly"
        if hotel.nightly_rate_amount < 250:
            return "mid-range"
        return "premium"
    notes_text = " ".join(hotel.notes).lower()
    if "luxury" in notes_text or "premium" in notes_text:
        return "premium"
    if "budget" in notes_text:
        return "budget"
    if "mid" in notes_text:
        return "mid-range"
    if configuration.budget_posture == "budget":
        return "budget-friendly fit"
    if configuration.budget_posture == "mid_range":
        return "mid-range fit"
    if configuration.budget_posture == "premium":
        return "premium fit"
    return "planning-first shortlist"


def _build_hotel_rate_note(hotel: HotelStayDetail) -> str | None:
    if hotel.nightly_rate_amount is not None:
        provider = hotel.rate_provider_name or "live provider"
        if hotel.nightly_tax_amount is not None and hotel.nightly_tax_amount > 0:
            return (
                f"Lowest live nightly rate via {provider}. Taxes currently add about "
                f"{_format_hotel_amount(hotel.nightly_tax_amount, hotel.nightly_rate_currency)}."
            )
        return f"Lowest live nightly rate via {provider}."
    if hotel.check_in and hotel.check_out:
        return "No live nightly rate is available for these exact dates yet."
    return "Exact nightly pricing firms up once the stay dates are locked."


def _format_hotel_amount(amount: float, currency: str | None) -> str:
    normalized_currency = (currency or "GBP").upper()
    symbol = "£" if normalized_currency == "GBP" else f"{normalized_currency} "
    rounded = round(amount)
    if rounded == int(rounded):
        return f"{symbol}{int(rounded)}"
    return f"{symbol}{rounded:.2f}"


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
