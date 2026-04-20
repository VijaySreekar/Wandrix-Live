from app.graph.planner.location_context import ResolvedPlannerLocationContext
from app.schemas.trip_conversation import PlannerChecklistItem, TripDetailsStepKey
from app.schemas.trip_planning import TripConfiguration


def get_active_modules(configuration: TripConfiguration) -> list[str]:
    return [
        name
        for name, enabled in configuration.selected_modules.model_dump(mode="json").items()
        if enabled
    ]


def get_visible_steps(configuration: TripConfiguration) -> list[TripDetailsStepKey]:
    active_modules = get_active_modules(configuration)
    has_flights = "flights" in active_modules
    has_hotels = "hotels" in active_modules
    has_activities = "activities" in active_modules
    has_weather = "weather" in active_modules

    steps: list[TripDetailsStepKey] = ["modules", "route", "timing"]

    if has_flights or has_hotels or has_activities:
        steps.append("travellers")
    if has_activities:
        steps.append("vibe")
    if has_flights or has_hotels or has_activities:
        steps.append("budget")
    if has_weather and steps == ["modules", "route", "timing"]:
        return steps
    return steps


def get_required_steps(configuration: TripConfiguration) -> list[TripDetailsStepKey]:
    active_modules = get_active_modules(configuration)
    has_flights = "flights" in active_modules
    has_hotels = "hotels" in active_modules
    has_activities = "activities" in active_modules

    steps: list[TripDetailsStepKey] = ["modules", "route", "timing"]

    if has_flights or has_hotels or has_activities:
        steps.append("travellers")
    if has_activities:
        steps.append("vibe")
    if has_flights or has_hotels:
        steps.append("budget")
    return steps


def compute_scope_missing_fields(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
) -> list[str]:
    active_modules = get_active_modules(configuration)
    flights_active = "flights" in active_modules
    travellers_relevant = any(
        module in active_modules for module in ["flights", "hotels", "activities"]
    )
    budget_relevant = any(module in active_modules for module in ["flights", "hotels"])
    activities_active = "activities" in active_modules
    detailed_timing_relevant = any(
        module in active_modules for module in ["flights", "hotels"]
    )

    missing_fields: list[str] = []

    if not configuration.to_location:
        missing_fields.append("to_location")
    if flights_active and not configuration.from_location and not (
        resolved_location_context and resolved_location_context.summary
    ):
        missing_fields.append("from_location")
    has_any_timing_signal = bool(
        configuration.start_date
        or configuration.end_date
        or configuration.travel_window
        or configuration.trip_length
    )
    if detailed_timing_relevant:
        if not configuration.start_date and not configuration.travel_window:
            missing_fields.append("start_date")
        if not configuration.end_date and not configuration.trip_length:
            missing_fields.append("end_date")
    elif not has_any_timing_signal:
        missing_fields.append("start_date")
    if travellers_relevant and configuration.travelers.adults is None:
        missing_fields.append("adults")
    if activities_active and not configuration.activity_styles:
        missing_fields.append("activity_styles")
    if budget_relevant and configuration.budget_posture is None and configuration.budget_gbp is None:
        missing_fields.append("budget_posture")
    if not active_modules:
        missing_fields.append("selected_modules")

    return missing_fields


def build_details_checklist_sections(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
) -> tuple[list[PlannerChecklistItem], list[PlannerChecklistItem]]:
    route_origin = configuration.from_location or (
        resolved_location_context.summary if resolved_location_context else None
    )
    route_value = " -> ".join(
        part for part in [route_origin, configuration.to_location] if part
    )
    travellers_value = _format_travellers(
        configuration.travelers.adults,
        configuration.travelers.children,
    )
    budget_value = _format_budget_value(configuration)
    modules_value = _format_module_scope(configuration)
    active_modules = get_active_modules(configuration)

    items = [
        _build_checklist_item("route", "Route", route_value),
        _build_checklist_item(
            "timing",
            "Timing",
            configuration.travel_window or _format_date_value(configuration.start_date, configuration.end_date),
        ),
        _build_checklist_item("trip_length", "Trip length", configuration.trip_length),
        _build_checklist_item("travellers", "Travellers", travellers_value),
        _build_checklist_item(
            "trip_style",
            "Trip style",
            ", ".join(configuration.activity_styles) if configuration.activity_styles else None,
        ),
        _build_checklist_item("budget", "Budget", budget_value),
        _build_checklist_item("modules", "Trip modules", modules_value),
    ]

    have_details: list[PlannerChecklistItem] = []
    need_details: list[PlannerChecklistItem] = []

    for item in items:
        if item.value:
            have_details.append(item)
        else:
            if item.id == "trip_length" and not any(
                module in active_modules for module in ["flights", "hotels"]
            ):
                continue
            if item.id == "travellers" and not any(
                module in active_modules for module in ["flights", "hotels", "activities"]
            ):
                continue
            if item.id == "trip_style" and "activities" not in active_modules:
                continue
            if item.id == "budget" and not any(
                module in active_modules for module in ["flights", "hotels"]
            ):
                continue
            need_details.append(item)

    return have_details, need_details


def has_origin_signal_for_details(
    configuration: TripConfiguration,
    resolved_location_context: ResolvedPlannerLocationContext | None = None,
) -> bool:
    return bool(
        configuration.from_location
        or (resolved_location_context and resolved_location_context.summary)
    )


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
