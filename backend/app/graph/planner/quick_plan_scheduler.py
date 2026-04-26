from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
import logging
from typing import Any

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_context import (
    build_quick_plan_configuration_payload,
    build_quick_plan_draft_payload,
    build_quick_plan_generation_context,
    build_quick_plan_module_payload,
)
from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.graph.planner.turn_models import ProposedTimelineItem, QuickPlanDraft
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_conversation import TripConversationState
from app.schemas.trip_planning import (
    FlightDetail,
    TimelineTimingSource,
    TripConfiguration,
    TripModuleOutputs,
)


logger = logging.getLogger(__name__)

QUICK_PLAN_TIMELINE_MAX_ITEMS = 16


class ScheduledQuickPlanDraft(BaseModel):
    board_summary: str | None = Field(default=None, max_length=400)
    timeline_preview: list[ProposedTimelineItem] = Field(
        default_factory=list,
        max_length=QUICK_PLAN_TIMELINE_MAX_ITEMS,
    )
    schedule_notes: list[str] = Field(default_factory=list, max_length=6)


def schedule_quick_plan_draft(
    *,
    title: str,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    conversation: TripConversationState,
    draft: QuickPlanDraft,
    dossier: QuickPlanDossier | None = None,
    repair_context: dict[str, Any] | None = None,
) -> QuickPlanDraft:
    if not draft.timeline_preview:
        return draft

    generation_context = build_quick_plan_generation_context(
        conversation=conversation,
        dossier=dossier,
    )
    configuration_payload = build_quick_plan_configuration_payload(configuration)
    module_payload = build_quick_plan_module_payload(module_outputs)
    draft_payload = build_quick_plan_draft_payload(draft)
    repair_instruction = ""
    if repair_context:
        repair_instruction = f"""

Private repair context:
{repair_context}

Repair scheduling rules:
- This is a fresh regenerated candidate; make sure reviewer timing and coverage gaps are addressed.
- Every visible row must remain clocked with usable start_at and end_at values.
""".rstrip()
    prompt = f"""
You are Wandrix's Quick Plan scheduling engine.

Turn the existing Quick Plan draft into a real clocked itinerary.

Product behavior:
- Every visible timeline item must have start_at and end_at.
- Use provider_exact only when the time comes directly from provider data or user-confirmed dates/times.
- Use planner_estimate for meals, transfers, hotel reset blocks, conference/work blocks, and untimed activities.
- Add a short timing_note when timing_source is planner_estimate.
- Do not use Flex, TBD, vague dayparts, or unscheduled rows.
- Do not invent live facts such as confirmed opening hours, ticket availability, reservation status, or prices.

Scheduling rules:
- Keep the itinerary practical and chronological inside each day.
- Use the selected provider anchors first: flight arrival/departure, hotel area/check-in/out, timed activities/events, and weather.
- If flight times are available, place arrival-day activity after landing and place final-day blocks before airport departure.
- Arrival day should include airport transfer, check-in/reset, food, and a light evening based on the arrival time.
- Full leisure days should include breakfast or morning start, activity blocks, lunch, afternoon pacing, dinner, and return-to-stay when the day ends away from the stay.
- Business or conference trips should protect work blocks, add breakfast, transfer to venue, lunch near venue, return/reset, dinner/evening, and back-to-stay.
- Weather should influence placement, but do not create detached weather-only filler.
- Keep provider/source names out of user-facing details unless they are actual venue/airline/hotel names.

Current trip title:
{title}

Confirmed configuration:
{configuration_payload}

Conversation state:
{generation_context}

Provider anchors:
{module_payload}

Current unscheduled or partially scheduled Quick Plan draft:
{draft_payload}
{repair_instruction}
""".strip()

    try:
        scheduled = _invoke_quick_plan_scheduler_model(
            prompt,
            temperature=0.1,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )
    except Exception:
        logger.warning(
            "Quick Plan scheduler returned no usable output on configured reasoning effort.",
            exc_info=True,
        )
        try:
            scheduled = _invoke_quick_plan_scheduler_model(
                prompt,
                temperature=0.1,
                timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
                max_retries=0,
                reasoning_effort="medium",
            )
        except Exception:
            logger.warning(
                "Quick Plan scheduler returned no usable output on medium reasoning fallback.",
                exc_info=True,
            )
            return _repair_existing_draft_schedule(
                draft,
                configuration=configuration,
                module_outputs=module_outputs,
            )

    repaired_items = _validate_and_repair_schedule(
        scheduled.timeline_preview,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    if not repaired_items:
        return _repair_existing_draft_schedule(
            draft,
            configuration=configuration,
            module_outputs=module_outputs,
        )

    return QuickPlanDraft(
        board_summary=scheduled.board_summary or draft.board_summary,
        timeline_preview=repaired_items,
    )


def _invoke_quick_plan_scheduler_model(
    prompt: str,
    *,
    temperature: float,
    timeout: float,
    max_retries: int,
    reasoning_effort: str | None = None,
) -> ScheduledQuickPlanDraft:
    try:
        model = create_quick_plan_chat_model(
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
            reasoning_effort=reasoning_effort,
        )
    except TypeError:
        model = create_quick_plan_chat_model(temperature=temperature)
    structured_model = model.with_structured_output(
        ScheduledQuickPlanDraft,
        method="json_schema",
    )
    return structured_model.invoke(
        [
            (
                "system",
                "Clock every Quick Plan timeline item with provider anchors, meal rhythm, transfers, work blocks when relevant, and validated chronology.",
            ),
            ("human", prompt),
        ]
    )


def _repair_existing_draft_schedule(
    draft: QuickPlanDraft,
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> QuickPlanDraft:
    repaired_items = _validate_and_repair_schedule(
        draft.timeline_preview,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    if not repaired_items:
        return draft
    return QuickPlanDraft(
        board_summary=draft.board_summary,
        timeline_preview=repaired_items,
    )


def _validate_and_repair_schedule(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> list[ProposedTimelineItem]:
    bounds = _build_schedule_bounds(configuration, module_outputs)
    repaired: list[ProposedTimelineItem] = []
    fallback_counts: dict[str, int] = defaultdict(int)

    for item in items:
        start_at, end_at = _repair_item_times(
            item,
            configuration=configuration,
            module_outputs=module_outputs,
            fallback_counts=fallback_counts,
        )
        if start_at is None or end_at is None:
            continue
        if end_at <= start_at:
            end_at = start_at + _default_duration(item.type)

        start_at, end_at = _apply_day_bounds(
            item=item,
            start_at=start_at,
            end_at=end_at,
            configuration=configuration,
            bounds=bounds,
        )
        if start_at is None or end_at is None or end_at <= start_at:
            continue

        timing_source = item.timing_source or _default_timing_source(item)
        repaired.append(
            item.model_copy(
                update={
                    "start_at": start_at,
                    "end_at": end_at,
                    "timing_source": timing_source,
                    "timing_note": _repair_timing_note(
                        item=item,
                        timing_source=timing_source,
                    ),
                }
            )
        )

    repaired.sort(
        key=lambda item: (
            _day_sort_value(item.day_label),
            item.start_at or datetime.max,
            item.title.lower(),
        )
    )
    repaired = _ensure_trip_day_coverage(
        repaired,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    return _cap_timeline_items(
        repaired,
        configuration=configuration,
        max_items=QUICK_PLAN_TIMELINE_MAX_ITEMS,
    )


def _cap_timeline_items(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    max_items: int,
) -> list[ProposedTimelineItem]:
    if len(items) <= max_items:
        return items

    expected_days = _expected_trip_days(configuration)
    if expected_days is None or expected_days <= 0 or expected_days > max_items:
        return items[:max_items]

    selected: list[ProposedTimelineItem] = []
    selected_ids: set[int] = set()
    for day_index in range(1, expected_days + 1):
        day_item = next(
            (
                item
                for item in items
                if _day_number(item.day_label or "") == day_index
                and id(item) not in selected_ids
            ),
            None,
        )
        if day_item is None:
            continue
        selected.append(day_item)
        selected_ids.add(id(day_item))

    for item in items:
        if len(selected) >= max_items:
            break
        if id(item) in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(id(item))

    selected.sort(
        key=lambda item: (
            _day_sort_value(item.day_label),
            item.start_at or datetime.max,
            item.title.lower(),
        )
    )
    return selected


def _ensure_trip_day_coverage(
    items: list[ProposedTimelineItem],
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> list[ProposedTimelineItem]:
    expected_days = _expected_trip_days(configuration)
    if expected_days is None or expected_days <= 0:
        return items

    covered_days = {_day_number(item.day_label or "") for item in items}
    covered_days = {day for day in covered_days if day is not None}
    missing_days = [
        day_index
        for day_index in range(1, expected_days + 1)
        if day_index not in covered_days
    ]
    if not missing_days:
        return items

    anchors = [
        _build_missing_day_anchor(
            day_index=day_index,
            expected_days=expected_days,
            configuration=configuration,
            module_outputs=module_outputs,
        )
        for day_index in missing_days
    ]
    merged = [*items, *anchors]
    merged.sort(
        key=lambda item: (
            _day_sort_value(item.day_label),
            item.start_at or datetime.max,
            item.title.lower(),
        )
    )
    return merged


def _expected_trip_days(configuration: TripConfiguration) -> int | None:
    if not (configuration.start_date and configuration.end_date):
        return None
    return max((configuration.end_date - configuration.start_date).days + 1, 1)


def _build_missing_day_anchor(
    *,
    day_index: int,
    expected_days: int,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> ProposedTimelineItem:
    destination = configuration.to_location or "the destination"
    item_date = _date_for_day_index(configuration=configuration, day_index=day_index)
    if day_index == expected_days:
        title = f"Final {destination} morning and departure buffer"
        start_time = _final_day_anchor_start_time(module_outputs)
        duration = timedelta(hours=2)
        details = [
            "Keep the final day deliberately light so checkout, airport transfer, or onward travel has enough breathing room.",
        ]
    elif day_index == 1:
        title = f"Arrival-day orientation in {destination}"
        start_time = _arrival_day_anchor_start_time(module_outputs)
        duration = timedelta(hours=2)
        details = [
            "Use this as a calm first-day buffer around arrival, check-in, food, and an easy local orientation.",
        ]
    else:
        title = f"{destination} food-and-culture pacing anchor"
        start_time = time(11, 0)
        duration = timedelta(hours=3)
        details = [
            "Keep this day covered with a flexible food-and-culture block that can be swapped for stronger live recommendations.",
        ]

    start_at = datetime.combine(
        item_date,
        start_time,
        tzinfo=_schedule_timezone(module_outputs),
    )
    end_at = start_at + duration
    return ProposedTimelineItem(
        type="note",
        title=title,
        day_label=f"Day {day_index}",
        start_at=start_at,
        end_at=end_at,
        timing_source="planner_estimate",
        timing_note="Planner-estimated coverage anchor for a complete Quick Plan day.",
        location_label=destination,
        details=details,
    )


def _date_for_day_index(
    *,
    configuration: TripConfiguration,
    day_index: int,
) -> date:
    if configuration.start_date:
        return configuration.start_date + timedelta(days=day_index - 1)
    return date.today() + timedelta(days=day_index + 29)


def _arrival_day_anchor_start_time(module_outputs: TripModuleOutputs) -> time:
    outbound = _primary_flight(module_outputs.flights, "outbound")
    if outbound and outbound.arrival_time:
        return (outbound.arrival_time + timedelta(hours=2)).time().replace(
            second=0,
            microsecond=0,
        )
    return time(15, 30)


def _final_day_anchor_start_time(module_outputs: TripModuleOutputs) -> time:
    returning = _primary_flight(module_outputs.flights, "return")
    if returning and returning.departure_time:
        return max(
            time(8, 30),
            (returning.departure_time - timedelta(hours=5)).time().replace(
                second=0,
                microsecond=0,
            ),
        )
    return time(10, 0)


def _schedule_timezone(module_outputs: TripModuleOutputs):
    for flight in module_outputs.flights:
        for timestamp in [
            flight.departure_time,
            flight.arrival_time,
        ]:
            if timestamp and timestamp.tzinfo:
                return timestamp.tzinfo
    return None


def _repair_item_times(
    item: ProposedTimelineItem,
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    fallback_counts: dict[str, int],
) -> tuple[datetime | None, datetime | None]:
    if item.start_at and item.end_at:
        return item.start_at, _align_bound_timezone(item.end_at, item.start_at)
    if item.start_at:
        return item.start_at, item.start_at + _default_duration(item.type)
    if item.end_at:
        return item.end_at - _default_duration(item.type), item.end_at

    fallback_start = _fallback_start_for_item(
        item,
        configuration=configuration,
        module_outputs=module_outputs,
        fallback_counts=fallback_counts,
    )
    if fallback_start is None:
        return None, None
    return fallback_start, fallback_start + _default_duration(item.type)


def _apply_day_bounds(
    *,
    item: ProposedTimelineItem,
    start_at: datetime,
    end_at: datetime,
    configuration: TripConfiguration,
    bounds: dict[date, tuple[datetime | None, datetime | None]],
) -> tuple[datetime | None, datetime | None]:
    item_date = _item_date(item=item, start_at=start_at, configuration=configuration)
    if item_date is None:
        return start_at, end_at

    earliest, latest = bounds.get(item_date, (None, None))
    earliest = _align_bound_timezone(earliest, start_at)
    latest = _align_bound_timezone(latest, start_at)
    duration = end_at - start_at

    if earliest and item.type != "flight" and start_at < earliest:
        start_at = earliest
        end_at = start_at + duration

    if latest and item.type != "flight" and end_at > latest:
        end_at = latest
        start_at = end_at - duration
        if earliest and start_at < earliest:
            return None, None

    if latest and item.type != "flight" and start_at >= latest:
        return None, None

    return start_at, end_at


def _build_schedule_bounds(
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> dict[date, tuple[datetime | None, datetime | None]]:
    bounds: dict[date, tuple[datetime | None, datetime | None]] = {}
    outbound = _primary_flight(module_outputs.flights, "outbound")
    returning = _primary_flight(module_outputs.flights, "return")

    if outbound and outbound.arrival_time:
        bounds[outbound.arrival_time.date()] = (outbound.arrival_time, None)
    elif configuration.start_date:
        bounds[configuration.start_date] = (
            datetime.combine(configuration.start_date, time(hour=9)),
            None,
        )

    if returning and returning.departure_time:
        earliest, _ = bounds.get(returning.departure_time.date(), (None, None))
        bounds[returning.departure_time.date()] = (
            earliest,
            returning.departure_time,
        )
    elif configuration.end_date:
        earliest, _ = bounds.get(configuration.end_date, (None, None))
        bounds[configuration.end_date] = (
            earliest,
            datetime.combine(configuration.end_date, time(hour=18)),
        )

    return bounds


def _fallback_start_for_item(
    item: ProposedTimelineItem,
    *,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    fallback_counts: dict[str, int],
) -> datetime | None:
    item_date = _fallback_date_for_item(
        item=item,
        configuration=configuration,
        module_outputs=module_outputs,
    )
    if item_date is None:
        return None

    day_key = item.day_label or item_date.isoformat()
    slot_index = fallback_counts[day_key]
    fallback_counts[day_key] += 1
    return datetime.combine(item_date, _fallback_time_for_item(item, slot_index))


def _fallback_date_for_item(
    *,
    item: ProposedTimelineItem,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
) -> date | None:
    day_number = _day_number(item.day_label or "") or 1
    anchor = configuration.start_date
    if anchor is None:
        outbound = _primary_flight(module_outputs.flights, "outbound")
        if outbound and outbound.arrival_time:
            anchor = outbound.arrival_time.date()
    if anchor is None:
        anchor = date.today() + timedelta(days=30)
    return anchor + timedelta(days=day_number - 1)


def _fallback_time_for_item(
    item: ProposedTimelineItem,
    slot_index: int,
) -> time:
    if item.type == "meal":
        meal_slots = [time(8, 30), time(12, 30), time(19, 30)]
        return meal_slots[min(slot_index, len(meal_slots) - 1)]
    if item.type == "transfer":
        transfer_slots = [time(9, 15), time(13, 45), time(18, 0), time(21, 0)]
        return transfer_slots[min(slot_index, len(transfer_slots) - 1)]
    if item.type == "hotel":
        return time(15, 30)
    if item.type == "event":
        event_slots = [time(9, 30), time(14, 0), time(19, 0)]
        return event_slots[min(slot_index, len(event_slots) - 1)]
    if item.type == "note":
        note_slots = [time(9, 0), time(16, 30), time(20, 30)]
        return note_slots[min(slot_index, len(note_slots) - 1)]

    activity_slots = [time(10, 0), time(13, 30), time(16, 30), time(19, 30)]
    return activity_slots[min(slot_index, len(activity_slots) - 1)]


def _primary_flight(
    flights: list[FlightDetail],
    direction: str,
) -> FlightDetail | None:
    return next((flight for flight in flights if flight.direction == direction), None)


def _item_date(
    *,
    item: ProposedTimelineItem,
    start_at: datetime,
    configuration: TripConfiguration,
) -> date | None:
    if start_at:
        return start_at.date()
    if configuration.start_date and item.day_label:
        day_number = _day_number(item.day_label)
        if day_number is not None:
            return configuration.start_date + timedelta(days=day_number - 1)
    return None


def _day_number(day_label: str) -> int | None:
    normalized = day_label.strip().lower()
    if not normalized.startswith("day "):
        return None
    suffix = normalized.removeprefix("day ").split()[0]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _default_duration(item_type: str) -> timedelta:
    if item_type == "meal":
        return timedelta(minutes=75)
    if item_type == "transfer":
        return timedelta(minutes=45)
    if item_type == "hotel":
        return timedelta(minutes=45)
    if item_type == "flight":
        return timedelta(hours=2)
    if item_type == "event":
        return timedelta(hours=2)
    if item_type == "note":
        return timedelta(minutes=30)
    return timedelta(hours=2)


def _align_bound_timezone(
    bound: datetime | None,
    reference: datetime,
) -> datetime | None:
    if bound is None:
        return None
    if bound.tzinfo is None and reference.tzinfo is not None:
        return bound.replace(tzinfo=reference.tzinfo)
    if bound.tzinfo is not None and reference.tzinfo is None:
        return bound.replace(tzinfo=None)
    return bound


def _default_timing_source(item: ProposedTimelineItem) -> TimelineTimingSource:
    if item.source_module in {"flights", "activities"} and item.type in {"flight", "event"}:
        return "provider_exact"
    return "planner_estimate"


def _repair_timing_note(
    *,
    item: ProposedTimelineItem,
    timing_source: TimelineTimingSource,
) -> str | None:
    if timing_source != "planner_estimate":
        return item.timing_note
    if item.timing_note:
        return item.timing_note
    return "Estimated by the planner from the trip rhythm and provider anchors."


def _day_sort_value(day_label: str | None) -> int:
    if not day_label:
        return 999
    day_number = _day_number(day_label)
    if day_number is not None:
        return day_number
    return 999
