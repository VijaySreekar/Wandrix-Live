from datetime import date, datetime, timedelta, timezone
from typing import Any, cast

from fastapi import HTTPException, status
from psycopg import OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.graph.planner.quick_plan_selection import (
    build_quick_plan_timeline_module_outputs,
    prioritize_quick_plan_module_outputs,
)
from app.graph.planner.quick_plan_enrichment import build_quick_plan_module_outputs
from app.repositories.trip_draft_repository import (
    get_trip_draft as get_trip_draft_record,
    upsert_trip_draft as upsert_trip_draft_record,
)
from app.repositories.trip_repository import get_trip_for_user
from app.repositories.trip_repository import update_trip_title as update_trip_title_record
from app.graph.planner.opening_turn import decide_opening_turn
from app.schemas.conversation import (
    CheckpointConversationHistoryResponse,
    OpeningTurnRequest,
    OpeningTurnResponse,
    TripConversationMessageRequest,
    TripConversationMessageResponse,
)
from app.schemas.trip_draft import TripDraft, TripPlanningPhase
from app.schemas.trip_planning import (
    FlightDetail,
    HotelStayDetail,
    TripBudgetEstimate,
    TripBudgetEstimateCategory,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)
from app.services.brochure_service import create_brochure_snapshot_for_trip
from app.services.providers.flights import (
    enrich_flights_from_amadeus,
    enrich_flights_from_travelpayouts,
)
from app.services.providers.iata_lookup import resolve_flight_gateway
from app.services.quick_plan_itinerary import build_provider_backed_quick_plan_itinerary

LAST_TURN_SUMMARY_MAX_LENGTH = 400


def respond_to_opening_turn(
    *,
    payload: OpeningTurnRequest,
) -> OpeningTurnResponse:
    decision = decide_opening_turn(
        user_message=payload.message,
        profile_context=payload.profile_context.model_dump(mode="json")
        if payload.profile_context
        else {},
        current_location_context=payload.current_location_context.model_dump(mode="json")
        if payload.current_location_context
        else {},
    )

    return OpeningTurnResponse(
        should_start_trip=decision.should_start_trip,
        message=decision.message,
    )


def send_trip_message(
    graph,
    db: Session,
    *,
    trip_id: str,
    user_id: str,
    payload: TripConversationMessageRequest,
) -> TripConversationMessageResponse:
    trip = get_trip_for_user(db, trip_id, user_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )

    draft = get_trip_draft_record(db, trip.id)

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip draft was not found.",
        )

    previous_draft_payload = _build_trip_draft_payload(
        trip_id=trip.id,
        thread_id=draft.thread_id,
        title=draft.title,
        configuration=draft.configuration,
        timeline=draft.timeline,
        module_outputs=draft.module_outputs,
        budget_estimate=draft.budget_estimate,
        status=draft.status,
        conversation=draft.conversation,
    )
    previous_draft = TripDraft.model_validate(previous_draft_payload)

    graph_payload = {
        "browser_session_id": trip.browser_session_id,
        "trip_id": trip.id,
        "thread_id": trip.thread_id,
        "user_input": payload.message,
        "profile_context": payload.profile_context.model_dump(mode="json")
        if payload.profile_context
        else {},
        "current_location_context": payload.current_location_context.model_dump(
            mode="json"
        )
        if payload.current_location_context
        else {},
        "board_action": payload.board_action.model_dump(mode="json")
        if payload.board_action
        else {},
        "trip_draft": {
            "title": draft.title,
            "configuration": draft.configuration,
            "timeline": draft.timeline,
            "module_outputs": draft.module_outputs,
            "budget_estimate": draft.budget_estimate,
            "status": draft.status,
            "conversation": previous_draft_payload["conversation"],
        },
        "metadata": {"user_id": user_id},
    }
    graph_config = {
        "configurable": {
            "thread_id": trip.thread_id,
        }
    }
    graph_result = _invoke_graph_with_retry(
        graph,
        payload=graph_payload,
        config=graph_config,
    )
    updated_draft = graph_result.get("trip_draft")
    if not updated_draft:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Graph did not return an updated trip draft.",
        )

    assistant_response = cast(
        str,
        graph_result.get("assistant_response")
        or "The planner processed your turn, but no assistant response was returned.",
    )

    if _should_run_quick_plan_stage_one(payload, updated_draft=updated_draft):
        persisted_draft, assistant_response = _persist_quick_plan_stage_one(
            db,
            trip_id=trip.id,
            thread_id=trip.thread_id,
            fallback_draft=draft,
            updated_draft=updated_draft,
        )
    else:
        persisted_draft = upsert_trip_draft_record(
            db,
            trip_id=trip.id,
            thread_id=trip.thread_id,
            title=updated_draft.get("title") or draft.title,
            configuration=updated_draft.get("configuration") or draft.configuration,
            timeline=updated_draft.get("timeline") or draft.timeline,
            module_outputs=updated_draft.get("module_outputs") or draft.module_outputs,
            budget_estimate=updated_draft.get("budget_estimate"),
            status=updated_draft.get("status") or draft.status,
            conversation=updated_draft.get("conversation") or draft.conversation,
        )
    next_draft_payload = _build_trip_draft_payload(
        trip_id=trip.id,
        thread_id=trip.thread_id,
        title=persisted_draft.title,
        configuration=persisted_draft.configuration,
        timeline=persisted_draft.timeline,
        module_outputs=persisted_draft.module_outputs,
        budget_estimate=persisted_draft.budget_estimate,
        status=persisted_draft.status,
        conversation=persisted_draft.conversation,
    )
    next_draft = TripDraft.model_validate(next_draft_payload)

    _sync_graph_turn_history(
        graph,
        config=graph_config,
        graph_result=graph_result,
        assistant_response=assistant_response,
    )

    if _should_create_brochure_snapshot(previous_draft, next_draft):
        create_brochure_snapshot_for_trip(db, trip=trip, draft=next_draft)

    next_title = persisted_draft.title.strip()
    if next_title and next_title != trip.title:
        trip = update_trip_title_record(
            db,
            trip,
            title=next_title,
        )
    phase = cast(
        TripPlanningPhase,
        persisted_draft.status.get("phase") or "opening",
    )
    return TripConversationMessageResponse(
        trip_id=trip.id,
        thread_id=trip.thread_id,
        draft_phase=phase,
        message=assistant_response,
        trip_draft=TripDraft.model_validate(
            next_draft_payload
        ),
    )


def _should_run_quick_plan_stage_one(
    payload: TripConversationMessageRequest,
    *,
    updated_draft: dict,
) -> bool:
    conversation = updated_draft.get("conversation") or {}
    build_state = conversation.get("quick_plan_build") or {}
    return bool(
        get_settings().quick_plan_stage_one_only
        and payload.board_action
        and payload.board_action.type == "select_quick_plan"
        and build_state.get("active_stage") == "flights"
    )


def _persist_quick_plan_stage_one(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    fallback_draft,
    updated_draft: dict,
) -> tuple[object, str]:
    initial_payload = _with_quick_plan_build_state(
        {
            "title": updated_draft.get("title") or fallback_draft.title,
            "configuration": updated_draft.get("configuration")
            or fallback_draft.configuration,
            "timeline": [],
            "module_outputs": TripModuleOutputs().model_dump(mode="json"),
            "budget_estimate": None,
            "status": updated_draft.get("status") or fallback_draft.status,
            "conversation": updated_draft.get("conversation")
            or fallback_draft.conversation,
        },
        status="running",
        active_stage="flights",
        completed_stages=["brief"],
        failed_stage=None,
        message="Brief saved. Finding flight options for the first Quick Plan board.",
    )
    initial_draft = upsert_trip_draft_record(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        **initial_payload,
    )

    configuration = TripConfiguration.model_validate(initial_draft.configuration)
    previous_configuration = TripConfiguration.model_validate(
        fallback_draft.configuration
    )
    existing_module_outputs = TripModuleOutputs.model_validate(
        fallback_draft.module_outputs
    )
    module_outputs = _build_quick_plan_stage_one_flight_outputs(
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=existing_module_outputs,
    )
    provider_returned_flights = bool(module_outputs.flights)
    if not provider_returned_flights:
        module_outputs = TripModuleOutputs(
            flights=_build_stage_one_placeholder_flights(configuration)
        )
    has_flights = bool(module_outputs.flights)
    used_placeholder_flights = has_flights and not provider_returned_flights
    weather_stage_draft = _persist_quick_plan_stage_one_weather_stage(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        initial_draft=initial_draft,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    module_outputs = _build_quick_plan_stage_one_weather_outputs(
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=TripModuleOutputs.model_validate(
            weather_stage_draft.module_outputs
        ),
    )
    has_weather = bool(module_outputs.weather)
    hotel_stage_draft = _persist_quick_plan_stage_one_hotel_stage(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        weather_stage_draft=weather_stage_draft,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    module_outputs = _build_quick_plan_stage_one_hotel_outputs(
        configuration=configuration,
        previous_configuration=previous_configuration,
        existing_module_outputs=TripModuleOutputs.model_validate(
            hotel_stage_draft.module_outputs
        ),
    )
    has_hotels = bool(module_outputs.hotels)
    itinerary_stage_draft = _persist_quick_plan_stage_one_itinerary_stage(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        hotel_stage_draft=hotel_stage_draft,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    itinerary_result = build_provider_backed_quick_plan_itinerary(
        configuration=configuration,
        module_outputs=module_outputs,
    )
    module_outputs = itinerary_result.module_outputs
    has_itinerary = bool(itinerary_result.timeline)
    stage_message = _quick_plan_stage_one_build_message(
        provider_returned_flights=provider_returned_flights,
        used_placeholder_flights=used_placeholder_flights,
        has_weather=has_weather,
        has_hotels=has_hotels,
        has_itinerary=has_itinerary,
    )
    response_message = _quick_plan_stage_one_response_message(
        provider_returned_flights=provider_returned_flights,
        used_placeholder_flights=used_placeholder_flights,
        has_weather=has_weather,
        has_hotels=has_hotels,
        has_itinerary=has_itinerary,
    )
    final_payload = _with_quick_plan_build_state(
        {
            "title": itinerary_stage_draft.title,
            "configuration": itinerary_stage_draft.configuration,
            "timeline": [item.model_dump(mode="json") for item in itinerary_result.timeline],
            "module_outputs": TripModuleOutputs(
                flights=module_outputs.flights,
                weather=module_outputs.weather,
                hotels=module_outputs.hotels,
                activities=module_outputs.activities,
            ).model_dump(mode="json"),
            "budget_estimate": _build_stage_one_budget_estimate(
                configuration,
                module_outputs.flights,
                module_outputs.hotels,
            ),
            "status": itinerary_stage_draft.status,
            "conversation": itinerary_stage_draft.conversation,
        },
        status="complete" if has_flights else "failed",
        active_stage=None,
        completed_stages=_quick_plan_stage_one_completed_stages(
            has_flights=has_flights,
            has_weather=has_weather,
            has_hotels=has_hotels,
            has_itinerary=has_itinerary,
        ),
        failed_stage=_quick_plan_stage_one_failed_stage(
            has_flights=has_flights,
            has_hotels=has_hotels,
            hotels_selected=configuration.selected_modules.hotels,
            has_itinerary=has_itinerary,
        ),
        message=stage_message,
    )
    final_payload = _with_stage_one_selected_hotel(final_payload, module_outputs.hotels)
    persisted_draft = upsert_trip_draft_record(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        **final_payload,
    )
    return (
        persisted_draft,
        response_message,
    )


def _persist_quick_plan_stage_one_weather_stage(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    initial_draft,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
):
    weather_stage_payload = _with_quick_plan_build_state(
        {
            "title": initial_draft.title,
            "configuration": initial_draft.configuration,
            "timeline": initial_draft.timeline,
            "module_outputs": TripModuleOutputs(
                flights=module_outputs.flights
            ).model_dump(mode="json"),
            "budget_estimate": _build_stage_one_budget_estimate(
                configuration,
                module_outputs.flights,
                [],
            ),
            "status": initial_draft.status,
            "conversation": initial_draft.conversation,
        },
        status="running",
        active_stage="weather" if configuration.selected_modules.weather else None,
        completed_stages=["brief", "flights"] if module_outputs.flights else ["brief"],
        failed_stage=None if module_outputs.flights else "flights",
        message=(
            "Flights are saved. Checking the weather for the selected dates."
            if configuration.selected_modules.weather
            else "Flights are saved. Weather is not selected for this Quick Plan."
        ),
    )
    return upsert_trip_draft_record(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        **weather_stage_payload,
    )


def _persist_quick_plan_stage_one_hotel_stage(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    weather_stage_draft,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
):
    hotel_stage_payload = _with_quick_plan_build_state(
        {
            "title": weather_stage_draft.title,
            "configuration": weather_stage_draft.configuration,
            "timeline": weather_stage_draft.timeline,
            "module_outputs": TripModuleOutputs(
                flights=module_outputs.flights,
                weather=module_outputs.weather,
            ).model_dump(mode="json"),
            "budget_estimate": _build_stage_one_budget_estimate(
                configuration,
                module_outputs.flights,
                [],
            ),
            "status": weather_stage_draft.status,
            "conversation": weather_stage_draft.conversation,
        },
        status="running",
        active_stage="hotels" if configuration.selected_modules.hotels else None,
        completed_stages=_quick_plan_stage_one_completed_stages(
            has_flights=bool(module_outputs.flights),
            has_weather=bool(module_outputs.weather),
            has_hotels=False,
        ),
        failed_stage=None if module_outputs.flights else "flights",
        message=(
            "Flights and weather are saved. Selecting the best-fit hotel next."
            if configuration.selected_modules.hotels
            else "Flights and weather are saved. Hotels are not selected for this Quick Plan."
        ),
    )
    return upsert_trip_draft_record(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        **hotel_stage_payload,
    )


def _persist_quick_plan_stage_one_itinerary_stage(
    db: Session,
    *,
    trip_id: str,
    thread_id: str,
    hotel_stage_draft,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
):
    itinerary_stage_payload = _with_quick_plan_build_state(
        {
            "title": hotel_stage_draft.title,
            "configuration": hotel_stage_draft.configuration,
            "timeline": hotel_stage_draft.timeline,
            "module_outputs": TripModuleOutputs(
                flights=module_outputs.flights,
                weather=module_outputs.weather,
                hotels=module_outputs.hotels,
            ).model_dump(mode="json"),
            "budget_estimate": _build_stage_one_budget_estimate(
                configuration,
                module_outputs.flights,
                module_outputs.hotels,
            ),
            "status": hotel_stage_draft.status,
            "conversation": hotel_stage_draft.conversation,
        },
        status="running",
        active_stage="itinerary",
        completed_stages=_quick_plan_stage_one_completed_stages(
            has_flights=bool(module_outputs.flights),
            has_weather=bool(module_outputs.weather),
            has_hotels=bool(module_outputs.hotels),
            has_itinerary=False,
        ),
        failed_stage=_quick_plan_stage_one_failed_stage(
            has_flights=bool(module_outputs.flights),
            has_hotels=bool(module_outputs.hotels),
            hotels_selected=configuration.selected_modules.hotels,
        ),
        message="Flights, weather, and hotel are saved. Building the clocked itinerary next.",
    )
    return upsert_trip_draft_record(
        db,
        trip_id=trip_id,
        thread_id=thread_id,
        **itinerary_stage_payload,
    )


def _build_quick_plan_stage_one_flight_outputs(
    *,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    live_flights: list[FlightDetail] = []
    if configuration.start_date:
        try:
            live_flights = enrich_flights_from_travelpayouts(
                configuration,
                timeout=8.0,
            )
        except Exception:
            live_flights = []

    if not live_flights and configuration.start_date:
        try:
            live_flights = enrich_flights_from_amadeus(configuration, timeout=8.0)
        except Exception:
            live_flights = []

    if live_flights:
        return TripModuleOutputs(
            flights=_promote_stage_one_provider_flights(
                _select_stage_one_best_fit_flights(
                    configuration=configuration,
                    flights=live_flights,
                )
            )
        )

    try:
        module_outputs = build_quick_plan_module_outputs(
            configuration=configuration,
            previous_configuration=previous_configuration,
            existing_module_outputs=existing_module_outputs,
            allowed_modules={"flights"},
        )
    except Exception:
        module_outputs = TripModuleOutputs()

    return TripModuleOutputs(
        flights=_promote_stage_one_provider_flights(
            _select_stage_one_best_fit_flights(
                configuration=configuration,
                flights=module_outputs.flights,
            )
        )
    )


def _select_stage_one_best_fit_flights(
    *,
    configuration: TripConfiguration,
    flights: list[FlightDetail],
) -> list[FlightDetail]:
    prioritized_outputs = prioritize_quick_plan_module_outputs(
        configuration=configuration,
        module_outputs=TripModuleOutputs(flights=flights),
    )
    selected_outputs = build_quick_plan_timeline_module_outputs(prioritized_outputs)
    return selected_outputs.flights


def _promote_stage_one_provider_flights(flights: list[FlightDetail]) -> list[FlightDetail]:
    return [
        flight.model_copy(
            update={
                "inventory_source": "live"
                if flight.inventory_source == "cached"
                else flight.inventory_source,
                "inventory_notice": "Schedule and fare can change before booking."
                if flight.inventory_source == "cached"
                else flight.inventory_notice,
            }
        )
        for flight in flights
    ]


def _build_quick_plan_stage_one_weather_outputs(
    *,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    try:
        weather_outputs = build_quick_plan_module_outputs(
            configuration=configuration,
            previous_configuration=previous_configuration,
            existing_module_outputs=existing_module_outputs,
            allowed_modules={"weather"},
        )
    except Exception:
        weather_outputs = existing_module_outputs
    weather = _merge_stage_one_weather_with_outlook(
        configuration,
        weather_outputs.weather,
    )
    return TripModuleOutputs(
        flights=existing_module_outputs.flights,
        weather=weather,
    )


def _build_quick_plan_stage_one_hotel_outputs(
    *,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
) -> TripModuleOutputs:
    hotels: list[HotelStayDetail] = []
    try:
        hotel_outputs = build_quick_plan_module_outputs(
            configuration=configuration,
            previous_configuration=previous_configuration,
            existing_module_outputs=existing_module_outputs,
            allowed_modules={"hotels"},
        )
        hotels = hotel_outputs.hotels
    except Exception:
        hotels = existing_module_outputs.hotels

    ranked_outputs = prioritize_quick_plan_module_outputs(
        configuration=configuration,
        module_outputs=TripModuleOutputs(hotels=hotels),
    )
    return TripModuleOutputs(
        flights=existing_module_outputs.flights,
        weather=existing_module_outputs.weather,
        hotels=ranked_outputs.hotels[:3],
    )


def _quick_plan_stage_one_completed_stages(
    *,
    has_flights: bool,
    has_weather: bool,
    has_hotels: bool,
    has_itinerary: bool = False,
) -> list[str]:
    completed = ["brief"]
    if has_flights:
        completed.append("flights")
    if has_weather:
        completed.append("weather")
    if has_hotels:
        completed.append("hotels")
    if has_itinerary:
        completed.append("itinerary")
    return completed


def _quick_plan_stage_one_failed_stage(
    *,
    has_flights: bool,
    has_hotels: bool,
    hotels_selected: bool,
    has_itinerary: bool = True,
) -> str | None:
    if not has_flights:
        return "flights"
    if hotels_selected and not has_hotels:
        return "hotels"
    if not has_itinerary:
        return "itinerary"
    return None


def _quick_plan_stage_one_build_message(
    *,
    provider_returned_flights: bool,
    used_placeholder_flights: bool,
    has_weather: bool,
    has_hotels: bool,
    has_itinerary: bool,
) -> str:
    weather_suffix = (
        " Weather is on the board for the selected dates."
        if has_weather
        else " Weather is skipped because it is not selected for this plan."
    )
    hotel_suffix = (
        " The best-fit hotel is selected on the board."
        if has_hotels
        else " Hotel selection needs another pass."
    )
    itinerary_suffix = (
        " The clocked itinerary is now on the board."
        if has_itinerary
        else " The clocked itinerary needs another pass."
    )
    if used_placeholder_flights:
        return (
            "Best-fit route and flight budget are on the board."
            + weather_suffix
            + hotel_suffix
            + itinerary_suffix
        )
    if provider_returned_flights:
        return (
            "Best-fit flights and budget are on the board."
            + weather_suffix
            + hotel_suffix
            + itinerary_suffix
        )
    return "The brief is on the board, but flight options were not available on this run."


def _quick_plan_stage_one_response_message(
    *,
    provider_returned_flights: bool,
    used_placeholder_flights: bool,
    has_weather: bool,
    has_hotels: bool,
    has_itinerary: bool,
) -> str:
    prefix = (
        "I've started the Quick Plan as a live board instead of waiting on a full itinerary. "
    )
    itinerary_sentence = _quick_plan_stage_one_itinerary_response_sentence(
        has_itinerary
    )
    if used_placeholder_flights:
        return (
            prefix
            + "The confirmed brief is saved, and I selected the best-fit flight route shape with an estimated flight budget. "
            + _quick_plan_stage_one_weather_response_sentence(has_weather)
            + " "
            + _quick_plan_stage_one_hotel_response_sentence(has_hotels)
            + " "
            + itinerary_sentence
        )
    if provider_returned_flights:
        return (
            prefix
            + "The confirmed brief, selected flight option, and flight budget are now saved. "
            + _quick_plan_stage_one_weather_response_sentence(has_weather)
            + " "
            + _quick_plan_stage_one_hotel_response_sentence(has_hotels)
            + " "
            + itinerary_sentence
        )
    return (
        prefix
        + "The confirmed brief is saved, but I could not get reliable flight options in this pass. I kept the board editable so we can retry flights before adding the rest."
    )


def _quick_plan_stage_one_weather_response_sentence(has_weather: bool) -> str:
    if has_weather:
        return "The weather for the selected dates is also on the board."
    return "Weather is skipped because it is not selected for this plan."


def _quick_plan_stage_one_hotel_response_sentence(has_hotels: bool) -> str:
    if has_hotels:
        return "I selected a working hotel based on budget fit, stay evidence, and area confidence."
    return "Hotel selection still needs another pass once stay inventory is available."


def _quick_plan_stage_one_itinerary_response_sentence(has_itinerary: bool) -> str:
    if has_itinerary:
        return "The board now includes a clocked day-by-day itinerary with transfers, meals, activities, hotel reset time, and return-flight timing."
    return "The itinerary still needs another pass, but the route, weather, and stay baseline are saved."


def _build_stage_one_weather_outlook(
    configuration: TripConfiguration,
) -> list[WeatherDetail]:
    if not (
        configuration.selected_modules.weather
        and configuration.to_location
        and configuration.start_date
    ):
        return []

    trip_days = _stage_one_weather_day_count(configuration)
    items: list[WeatherDetail] = []
    for index in range(trip_days):
        forecast_date = configuration.start_date + timedelta(days=index)
        high_c, low_c, summary, tags = _stage_one_weather_profile(
            destination=configuration.to_location,
            forecast_date=forecast_date,
            preference=configuration.weather_preference,
        )
        items.append(
            WeatherDetail(
                id=f"weather_outlook_{index + 1}",
                day_label=f"Day {index + 1}",
                summary=summary,
                forecast_date=forecast_date,
                condition_tags=tags,
                temperature_band=_stage_one_temperature_band(high_c, low_c),
                weather_risk_level="medium" if "rain" in tags or "hot" in tags else "low",
                high_c=high_c,
                low_c=low_c,
                notes=[
                    f"Date: {forecast_date.isoformat()}",
                    f"Location: {configuration.to_location}",
                    "Weather outlook used for planning until the live forecast window covers the trip.",
                ],
            )
        )
    return items


def _merge_stage_one_weather_with_outlook(
    configuration: TripConfiguration,
    live_weather: list[WeatherDetail],
) -> list[WeatherDetail]:
    if not (
        configuration.selected_modules.weather
        and configuration.to_location
        and configuration.start_date
    ):
        return []

    trip_days = _stage_one_weather_day_count(configuration)
    outlook_by_date = {
        item.forecast_date: item
        for item in _build_stage_one_weather_outlook(configuration)
        if item.forecast_date is not None
    }
    live_by_date = {
        item.forecast_date: item
        for item in live_weather
        if item.forecast_date is not None
    }

    merged: list[WeatherDetail] = []
    for index in range(trip_days):
        forecast_date = configuration.start_date + timedelta(days=index)
        live_item = live_by_date.get(forecast_date)
        if live_item is not None:
            merged.append(
                live_item.model_copy(
                    update={
                        "id": f"weather_live_{index + 1}",
                        "day_label": f"Day {index + 1}",
                    }
                )
            )
            continue

        outlook_item = outlook_by_date.get(forecast_date)
        if outlook_item is not None:
            merged.append(
                outlook_item.model_copy(
                    update={
                        "id": f"weather_outlook_{index + 1}",
                        "day_label": f"Day {index + 1}",
                    }
                )
            )

    return merged


def _stage_one_weather_day_count(configuration: TripConfiguration) -> int:
    if configuration.start_date and configuration.end_date:
        return min(max((configuration.end_date - configuration.start_date).days + 1, 1), 7)
    return 4


def _stage_one_weather_profile(
    *,
    destination: str,
    forecast_date: date,
    preference: str | None,
) -> tuple[int, int, str, list[str]]:
    destination_key = destination.lower()
    month = forecast_date.month

    if any(token in destination_key for token in ["barcelona", "valencia", "seville", "malaga", "madrid"]):
        if month in {6, 7, 8, 9}:
            high_c, low_c = 28, 20
            tags = ["clear", "warm"]
            summary = "Warm, mostly sunny planning outlook."
        elif month in {4, 5, 10}:
            high_c, low_c = 22, 15
            tags = ["clear", "mild"]
            summary = "Mild, bright planning outlook."
        else:
            high_c, low_c = 16, 9
            tags = ["cloudy", "mild"]
            summary = "Cooler mixed-weather planning outlook."
    elif any(token in destination_key for token in ["kyoto", "osaka", "tokyo"]):
        if month in {6, 7, 8, 9}:
            high_c, low_c = 29, 22
            tags = ["warm", "rain"]
            summary = "Warm, humid planning outlook with shower risk."
        elif month in {3, 4, 5, 10, 11}:
            high_c, low_c = 21, 13
            tags = ["mild"]
            summary = "Mild seasonal planning outlook."
        else:
            high_c, low_c = 11, 4
            tags = ["cool"]
            summary = "Cool seasonal planning outlook."
    else:
        if month in {6, 7, 8}:
            high_c, low_c = 24, 16
            tags = ["mild", "clear"]
            summary = "Generally warm planning outlook."
        elif month in {12, 1, 2}:
            high_c, low_c = 8, 2
            tags = ["cool"]
            summary = "Cool seasonal planning outlook."
        else:
            high_c, low_c = 18, 10
            tags = ["mild"]
            summary = "Mild seasonal planning outlook."

    if preference and any(token in preference.lower() for token in ["sun", "warm", "hot"]):
        summary = f"{summary} Prioritize sunnier outdoor windows."

    return high_c, low_c, summary, tags


def _stage_one_temperature_band(high_c: int, low_c: int) -> str:
    if high_c >= 30:
        return "hot"
    if high_c >= 24:
        return "warm"
    if low_c <= 2:
        return "cold"
    if high_c <= 10:
        return "cool"
    return "mild"


def _build_stage_one_placeholder_flights(
    configuration: TripConfiguration,
) -> list[FlightDetail]:
    if not (
        configuration.selected_modules.flights
        and configuration.from_location
        and configuration.to_location
        and configuration.start_date
    ):
        return []

    origin_gateway = resolve_flight_gateway(configuration.from_location)
    destination_gateway = resolve_flight_gateway(configuration.to_location)
    origin = origin_gateway.search_iata if origin_gateway else "TBD"
    destination = destination_gateway.search_iata if destination_gateway else "TBD"
    outbound_notes = _build_stage_one_placeholder_notes(
        origin_gateway=origin_gateway,
        destination_gateway=destination_gateway,
        booking_note="Exact airline and time will be selected from live inventory before booking.",
    )
    return_notes = _build_stage_one_placeholder_notes(
        origin_gateway=destination_gateway,
        destination_gateway=origin_gateway,
        booking_note="Exact airline and return time will be selected from live inventory before booking.",
    )
    fare_low, fare_high, fare_currency = _estimate_stage_one_flight_total(
        configuration,
        origin,
        destination,
    )
    price_text = _format_stage_one_flight_price_text(
        fare_low,
        fare_high,
        fare_currency,
    )
    flights = [
        FlightDetail(
            id="quick_plan_placeholder_outbound",
            direction="outbound",
            carrier="Best-fit route estimate",
            departure_airport=origin,
            arrival_airport=destination,
            duration_text="Best-fit route",
            price_text=price_text,
            stop_details_available=False,
            inventory_notice="Exact airline and timing still need live booking inventory.",
            inventory_source="placeholder",
            notes=outbound_notes,
        )
    ]
    if configuration.end_date:
        flights.append(
            FlightDetail(
                id="quick_plan_placeholder_return",
                direction="return",
                carrier="Best-fit route estimate",
                departure_airport=destination,
                arrival_airport=origin,
                duration_text="Best-fit route",
                stop_details_available=False,
                inventory_notice="Exact airline and timing still need live booking inventory.",
                inventory_source="placeholder",
                notes=return_notes,
            )
        )
    return flights


def _build_stage_one_placeholder_notes(
    *,
    origin_gateway,
    destination_gateway,
    booking_note: str,
) -> list[str]:
    notes = [
        origin_gateway.planning_note("origin") if origin_gateway else None,
        destination_gateway.planning_note("destination") if destination_gateway else None,
        booking_note,
    ]
    return [note for note in notes if note]


def _build_stage_one_budget_estimate(
    configuration: TripConfiguration,
    flights: list[FlightDetail],
    hotels: list[HotelStayDetail],
) -> dict | None:
    priced_flights = [
        flight
        for flight in flights
        if flight.fare_amount is not None and flight.fare_currency
    ]
    currencies = {flight.fare_currency for flight in priced_flights if flight.fare_currency}
    if priced_flights and len(currencies) == 1:
        total = _stage_one_provider_flight_total(priced_flights)
        currency = next(iter(currencies))
        source = "provider_price"
        notes = ["Uses the selected provider-backed flight fare currently on the board."]
        low_amount = high_amount = total
    else:
        origin_gateway = resolve_flight_gateway(configuration.from_location or "")
        destination_gateway = resolve_flight_gateway(configuration.to_location or "")
        low_amount, high_amount, currency = _estimate_stage_one_flight_total(
            configuration,
            origin_gateway.search_iata if origin_gateway else "TBD",
            destination_gateway.search_iata if destination_gateway else "TBD",
        )
        source = "planner_estimate"
        notes = [
            "Planner estimate for the selected route shape until exact airline inventory is available."
        ]

    categories = [
        TripBudgetEstimateCategory(
            category="flights",
            label="Flights",
            low_amount=low_amount,
            high_amount=high_amount,
            currency=currency,
            source=source,
            notes=notes,
        )
    ]
    stay_category = _build_stage_one_stay_budget_category(
        configuration,
        hotels[0] if hotels else None,
        currency,
    )
    if stay_category is not None:
        categories.append(stay_category)

    total_low = sum(
        category.low_amount or 0
        for category in categories
        if category.low_amount is not None
    )
    total_high = sum(
        category.high_amount or 0
        for category in categories
        if category.high_amount is not None
    )
    estimate = TripBudgetEstimate(
        total_low_amount=total_low or low_amount,
        total_high_amount=total_high or high_amount,
        currency=currency,
        categories=categories,
        caveat="Quick Plan estimate only; food, activities, and local transport are not included yet.",
    )
    return estimate.model_dump(mode="json")


def _build_stage_one_stay_budget_category(
    configuration: TripConfiguration,
    hotel: HotelStayDetail | None,
    fallback_currency: str,
) -> TripBudgetEstimateCategory | None:
    if hotel is None:
        return None

    nights = _stage_one_stay_nights(configuration)
    if hotel.nightly_rate_amount is not None:
        currency = hotel.nightly_rate_currency or fallback_currency
        nightly_low = nightly_high = hotel.nightly_rate_amount
        source = "provider_price"
        notes = [
            "Uses the selected hotel nightly rate currently available from the provider."
        ]
    else:
        currency = fallback_currency
        nightly_low, nightly_high = _estimate_stage_one_hotel_nightly_band(
            configuration
        )
        source = "planner_estimate"
        notes = [
            "Planner estimate for the selected hotel shape because exact nightly rate is not available."
        ]

    return TripBudgetEstimateCategory(
        category="stay",
        label="Stay",
        low_amount=round(nightly_low * nights, 2),
        high_amount=round(nightly_high * nights, 2),
        currency=currency,
        source=source,
        notes=notes,
    )


def _stage_one_stay_nights(configuration: TripConfiguration) -> int:
    if configuration.start_date and configuration.end_date:
        return max((configuration.end_date - configuration.start_date).days, 1)
    return 3


def _estimate_stage_one_hotel_nightly_band(
    configuration: TripConfiguration,
) -> tuple[float, float]:
    posture = configuration.budget_posture or "mid_range"
    if posture == "budget":
        return 90, 150
    if posture == "premium":
        return 230, 420
    return 140, 240


def _stage_one_provider_flight_total(flights: list[FlightDetail]) -> float:
    if (
        len(flights) >= 2
        and len({flight.fare_amount for flight in flights}) == 1
        and len({flight.price_text for flight in flights}) == 1
    ):
        return round(flights[0].fare_amount or 0, 2)
    return round(sum(flight.fare_amount or 0 for flight in flights), 2)


def _estimate_stage_one_flight_total(
    configuration: TripConfiguration,
    origin_iata: str,
    destination_iata: str,
) -> tuple[float, float, str]:
    travelers = max((configuration.travelers.adults or 1) + (configuration.travelers.children or 0), 1)
    posture = configuration.budget_posture or "mid_range"
    per_person_low, per_person_high = _estimate_stage_one_flight_band(
        origin_iata,
        destination_iata,
        posture,
    )
    return (
        float(per_person_low * travelers),
        float(per_person_high * travelers),
        configuration.budget_currency or "GBP",
    )


def _estimate_stage_one_flight_band(
    origin_iata: str,
    destination_iata: str,
    budget_posture: str,
) -> tuple[int, int]:
    origin_region = _stage_one_flight_region(origin_iata)
    destination_region = _stage_one_flight_region(destination_iata)
    if origin_region == destination_region == "europe":
        base = (120, 280)
    elif origin_region != destination_region and {origin_region, destination_region} & {"asia"}:
        base = (650, 1050)
    elif origin_region != destination_region:
        base = (480, 900)
    else:
        base = (220, 520)

    if budget_posture == "premium":
        return (round(base[0] * 1.35), round(base[1] * 1.55))
    if budget_posture == "budget":
        return (round(base[0] * 0.78), round(base[1] * 0.9))
    return base


def _stage_one_flight_region(iata_code: str) -> str:
    code = iata_code.upper()
    europe = {"LON", "LGW", "LHR", "STN", "LTN", "LCY", "MAN", "BHX", "EDI", "GLA", "PAR", "ROM", "MIL", "MAD", "BCN", "LIS", "OPO", "AMS", "BER", "PRG", "BUD", "ZRH", "NAP", "PSA"}
    asia = {"OSA", "KIX", "ITM", "TYO", "HND", "NRT", "DXB"}
    north_america = {"NYC", "JFK", "EWR", "LGA", "SFO", "LAX", "YYC", "CUN"}
    if code in europe:
        return "europe"
    if code in asia:
        return "asia"
    if code in north_america:
        return "north_america"
    return "other"


def _format_stage_one_flight_price_text(
    low_amount: float,
    high_amount: float,
    currency: str,
) -> str:
    return f"Flight budget {currency} {low_amount:,.0f}-{high_amount:,.0f} total"


def _with_quick_plan_build_state(
    payload: dict,
    *,
    status: str,
    active_stage: str | None,
    completed_stages: list[str],
    failed_stage: str | None,
    message: str,
) -> dict:
    next_payload = dict(payload)
    conversation = dict(next_payload.get("conversation") or {})
    conversation["quick_plan_build"] = {
        "status": status,
        "active_stage": active_stage,
        "completed_stages": completed_stages,
        "failed_stage": failed_stage,
        "message": message,
    }
    conversation["quick_plan_finalization"] = {
        "accepted": False,
        "review_status": None,
        "quality_status": None,
        "brochure_eligible": False,
        "accepted_modules": [],
        "assumptions": [],
        "blocked_reasons": [
            "Quick Plan remains editable until itinerary review and brochure eligibility are added."
        ],
        "review_result": {},
        "quality_result": {},
        "intelligence_summary": {},
    }
    status_payload = dict(next_payload.get("status") or {})
    status_payload["brochure_ready"] = False
    status_payload["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    next_payload["conversation"] = conversation
    next_payload["status"] = status_payload
    return next_payload


def _with_stage_one_selected_hotel(
    payload: dict,
    hotels: list[HotelStayDetail],
) -> dict:
    if not hotels:
        return payload

    selected_hotel = hotels[0]
    next_payload = dict(payload)
    conversation = dict(next_payload.get("conversation") or {})
    stay_planning = dict(conversation.get("stay_planning") or {})
    stay_planning.update(
        {
            "selected_hotel_id": selected_hotel.id,
            "selected_hotel_name": selected_hotel.hotel_name,
            "hotel_selection_status": "selected",
            "hotel_selection_rationale": _stage_one_hotel_selection_rationale(
                selected_hotel
            ),
            "hotel_selection_assumptions": _stage_one_hotel_selection_assumptions(
                selected_hotel
            ),
            "hotel_results_status": "ready",
            "hotel_results_summary": (
                "Quick Plan selected the strongest working hotel from the ranked provider shortlist."
            ),
            "hotel_total_results": len(hotels),
            "selected_stay_direction": selected_hotel.area,
            "selection_status": "selected",
            "selection_rationale": selected_hotel.area
            or "Best-fit stay base selected from the hotel shortlist.",
        }
    )
    conversation["stay_planning"] = stay_planning
    next_payload["conversation"] = conversation
    return next_payload


def _stage_one_hotel_selection_rationale(hotel: HotelStayDetail) -> str:
    parts = ["Selected as the best-fit working hotel"]
    if hotel.area:
        parts.append(f"in {hotel.area}")
    if hotel.nightly_rate_amount is not None:
        parts.append("with usable nightly pricing")
    elif hotel.source_url or hotel.image_url:
        parts.append("with stronger provider evidence than the alternates")
    return " ".join(parts) + "."


def _stage_one_hotel_selection_assumptions(hotel: HotelStayDetail) -> list[str]:
    assumptions = [
        "The hotel remains editable; this is the Quick Plan working pick, not a booking."
    ]
    if hotel.nightly_rate_amount is None:
        assumptions.append("Exact nightly rate was not available in the first hotel pass.")
    if hotel.area:
        assumptions.append(f"The stay base is treated as {hotel.area}.")
    return assumptions[:4]


def _build_trip_draft_payload(
    *,
    trip_id: str,
    thread_id: str,
    title: str,
    configuration,
    timeline,
    module_outputs,
    budget_estimate,
    status,
    conversation,
) -> dict:
    return {
        "trip_id": trip_id,
        "thread_id": thread_id,
        "title": title,
        "configuration": configuration,
        "timeline": timeline,
        "module_outputs": module_outputs,
        "budget_estimate": budget_estimate,
        "status": status,
        "conversation": _sanitize_conversation_payload(conversation),
    }


def _sanitize_conversation_payload(conversation):
    if not isinstance(conversation, dict):
        return conversation
    sanitized = dict(conversation)
    summary = sanitized.get("last_turn_summary")
    if isinstance(summary, str) and len(summary) > LAST_TURN_SUMMARY_MAX_LENGTH:
        sanitized["last_turn_summary"] = (
            summary[: LAST_TURN_SUMMARY_MAX_LENGTH - 1].rstrip() + "…"
        )
    return sanitized


def _should_create_brochure_snapshot(previous_draft: TripDraft, next_draft: TripDraft) -> bool:
    if next_draft.status.confirmation_status != "finalized":
        return False
    if (
        next_draft.conversation.planning_mode == "quick"
        and not next_draft.conversation.quick_plan_finalization.brochure_eligible
    ):
        return False

    if previous_draft.status.confirmation_status != "finalized":
        return True

    return previous_draft.status.finalized_at != next_draft.status.finalized_at


def get_trip_conversation_history(
    graph,
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> CheckpointConversationHistoryResponse:
    trip = get_trip_for_user(db, trip_id, user_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )

    snapshot = _get_graph_state_with_retry(
        graph,
        {
            "configurable": {
                "thread_id": trip.thread_id,
            }
        },
    )
    values = getattr(snapshot, "values", {}) or {}
    raw_messages = values.get("raw_messages", [])
    draft = get_trip_draft_record(db, trip.id)
    if draft is not None:
        raw_messages = _normalize_quick_plan_stage_one_history(
            raw_messages,
            draft=draft,
        )

    return CheckpointConversationHistoryResponse.model_validate(
        {
            "trip_id": trip.id,
            "thread_id": trip.thread_id,
            "messages": raw_messages,
        }
    )


def _invoke_graph_with_retry(graph, *, payload: dict, config: dict):
    try:
        return graph.invoke(payload, config=config)
    except OperationalError:
        return graph.invoke(payload, config=config)


def _get_graph_state_with_retry(graph, config: dict):
    try:
        return graph.get_state(config)
    except OperationalError:
        return graph.get_state(config)


def _normalize_quick_plan_stage_one_history(raw_messages, *, draft) -> list[Any]:
    if not isinstance(raw_messages, list):
        return []

    conversation = draft.conversation if isinstance(draft.conversation, dict) else {}
    build_state = conversation.get("quick_plan_build") or {}
    completed_stages = build_state.get("completed_stages") or []
    if (
        conversation.get("planning_mode") != "quick"
        or "flights" not in completed_stages
        or build_state.get("status") not in {"complete", "failed"}
    ):
        return raw_messages

    try:
        module_outputs = TripModuleOutputs.model_validate(draft.module_outputs or {})
    except Exception:
        return raw_messages

    if not module_outputs.flights:
        return raw_messages

    used_placeholder_flights = any(
        flight.inventory_source == "placeholder" for flight in module_outputs.flights
    )
    provider_returned_flights = bool(module_outputs.flights) and not used_placeholder_flights
    response_message = _quick_plan_stage_one_response_message(
        provider_returned_flights=provider_returned_flights,
        used_placeholder_flights=used_placeholder_flights,
        has_weather=bool(module_outputs.weather),
        has_hotels=bool(module_outputs.hotels),
        has_itinerary="itinerary" in completed_stages,
    )
    return _replace_quick_plan_history_turn(raw_messages, response_message)


def _replace_quick_plan_history_turn(
    raw_messages: list[Any],
    response_message: str,
) -> list[Any]:
    next_messages = list(raw_messages)
    quick_plan_anchor_index = _find_latest_quick_plan_history_anchor(next_messages)
    if quick_plan_anchor_index is None:
        return _replace_latest_quick_plan_assistant_message(
            next_messages,
            response_message,
        )

    anchor_message = next_messages[quick_plan_anchor_index]
    if isinstance(anchor_message, dict) and anchor_message.get("role") == "system":
        next_anchor = dict(anchor_message)
        next_anchor["role"] = "user"
        next_anchor["content"] = "Use Quick Plan and generate the first draft itinerary now."
        next_messages[quick_plan_anchor_index] = next_anchor

    for index in range(quick_plan_anchor_index + 1, len(next_messages)):
        message = next_messages[index]
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        next_message = dict(message)
        next_message["content"] = response_message
        next_messages[index] = next_message
        return next_messages

    return next_messages


def _find_latest_quick_plan_history_anchor(raw_messages: list[Any]) -> int | None:
    for index in range(len(raw_messages) - 1, -1, -1):
        message = raw_messages[index]
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = str(message.get("content") or "").lower()
        if role == "user" and ("quick plan" in content or "quick-plan" in content):
            return index
        if role == "system" and "quick" in content and "plan" in content:
            return index
    return None


def _replace_latest_quick_plan_assistant_message(
    raw_messages: list[Any],
    response_message: str,
) -> list[Any]:
    for index in range(len(raw_messages) - 1, -1, -1):
        message = raw_messages[index]
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = str(message.get("content") or "").lower()
        if "quick plan" not in content and "quick-plan" not in content:
            continue
        next_messages = list(raw_messages)
        next_message = dict(message)
        next_message["content"] = response_message
        next_messages[index] = next_message
        return next_messages
    return raw_messages


def _sync_graph_turn_history(
    graph,
    *,
    config: dict,
    graph_result: dict,
    assistant_response: str,
) -> None:
    update_state = getattr(graph, "update_state", None)
    if not callable(update_state):
        return

    raw_messages = graph_result.get("raw_messages")
    if not isinstance(raw_messages, list):
        return

    synced_messages, changed = _replace_latest_assistant_history_message(
        raw_messages,
        assistant_response=assistant_response,
    )
    if not changed and graph_result.get("assistant_response") == assistant_response:
        return

    try:
        _update_graph_state_with_retry(
            graph,
            config=config,
            values={
                "assistant_response": assistant_response,
                "raw_messages": synced_messages,
            },
        )
    except Exception:
        # History sync should never fail the completed product turn. The draft write
        # remains authoritative; the next refresh will fall back to the last checkpoint.
        return


def _replace_latest_assistant_history_message(
    raw_messages: list[Any],
    *,
    assistant_response: str,
) -> tuple[list[Any], bool]:
    next_messages = list(raw_messages)

    for index in range(len(next_messages) - 1, -1, -1):
        message = next_messages[index]
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue

        if message.get("content") == assistant_response:
            return next_messages, False

        next_message = dict(message)
        next_message["content"] = assistant_response
        next_messages[index] = next_message
        return next_messages, True

    next_messages.append(
        {
            "role": "assistant",
            "content": assistant_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return next_messages, True


def _update_graph_state_with_retry(graph, *, config: dict, values: dict):
    try:
        return graph.update_state(config, values)
    except OperationalError:
        return graph.update_state(config, values)
    except Exception:
        return graph.update_state(config, values, as_node="process_trip_turn")
