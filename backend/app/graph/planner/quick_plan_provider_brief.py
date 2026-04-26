from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.graph.planner.quick_plan_context import build_quick_plan_module_payload
from app.graph.planner.quick_plan_dossier import QuickPlanDossier
from app.graph.planner.quick_plan_strategy import QuickPlanStrategyBrief
from app.graph.planner.quick_plan_timeouts import QUICK_PLAN_LLM_TIMEOUT_SECONDS
from app.integrations.llm.client import create_quick_plan_chat_model
from app.schemas.trip_planning import (
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
)


logger = logging.getLogger(__name__)


class QuickPlanProviderFlightAnchor(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    direction: str | None = Field(default=None, max_length=40)
    carrier: str | None = Field(default=None, max_length=120)
    flight_number: str | None = Field(default=None, max_length=80)
    departure_airport: str | None = Field(default=None, max_length=80)
    arrival_airport: str | None = Field(default=None, max_length=80)
    departure_time: str | None = Field(default=None, max_length=80)
    arrival_time: str | None = Field(default=None, max_length=80)
    duration_text: str | None = Field(default=None, max_length=120)
    price_text: str | None = Field(default=None, max_length=120)
    fare_amount: float | None = None
    fare_currency: str | None = Field(default=None, max_length=12)
    stop_count: int | None = None
    timing_quality: str | None = Field(default=None, max_length=80)


class QuickPlanProviderStayAnchor(BaseModel):
    id: str | None = Field(default=None, max_length=120)
    hotel_name: str | None = Field(default=None, max_length=180)
    area: str | None = Field(default=None, max_length=160)
    address: str | None = Field(default=None, max_length=240)
    nightly_rate_amount: float | None = None
    nightly_rate_currency: str | None = Field(default=None, max_length=12)
    check_in: str | None = Field(default=None, max_length=80)
    check_out: str | None = Field(default=None, max_length=80)
    source_label: str | None = Field(default=None, max_length=120)


class QuickPlanProviderBrief(BaseModel):
    selected_outbound_flight: QuickPlanProviderFlightAnchor | None = None
    selected_return_flight: QuickPlanProviderFlightAnchor | None = None
    selected_stay_base: QuickPlanProviderStayAnchor | None = None
    activity_clusters: list[str] = Field(default_factory=list, max_length=10)
    weather_constraints: list[str] = Field(default_factory=list, max_length=6)
    missing_provider_facts: list[str] = Field(default_factory=list, max_length=10)
    fact_safety_caveats: list[str] = Field(default_factory=list, max_length=10)
    planner_context: list[str] = Field(default_factory=list, max_length=10)


def build_quick_plan_provider_brief(
    *,
    dossier: QuickPlanDossier,
    configuration: TripConfiguration,
    module_outputs: TripModuleOutputs,
    strategy_brief: QuickPlanStrategyBrief,
    repair_context: dict[str, Any] | None = None,
) -> QuickPlanProviderBrief | None:
    prompt = f"""
You are Wandrix's private provider interpreter.

Interpret already-ranked provider/module outputs into planner-friendly context.
Do not rerank providers. Treat the first ranked outbound, first ranked return,
and first ranked hotel as primary anchors unless their facts are missing or contradictory.

Return:
- selected outbound and return flight summaries
- selected stay base summary
- activity clusters useful for planning
- weather constraints
- missing provider facts and fact-safety caveats
- short planner context notes
- During quality repair, revise provider interpretation only when logistics
  realism or fact-safety feedback requires it.
- Never invent provider facts, live prices, reservation status, opening hours,
  or exact timings to satisfy quality feedback. Use honest caveats or planning
  blocks when facts are missing.

Selected module scope:
{dossier.readiness.allowed_modules}

Trip configuration:
{configuration.model_dump(mode="json")}

Strategy brief:
{strategy_brief.model_dump(mode="json")}

Ranked module outputs:
{build_quick_plan_module_payload(module_outputs)}

Repair context, if any:
{repair_context or {}}
""".strip()

    try:
        model = create_quick_plan_chat_model(
            temperature=0.1,
            timeout=QUICK_PLAN_LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )
        structured_model = model.with_structured_output(
            QuickPlanProviderBrief,
            method="json_schema",
        )
        brief = structured_model.invoke(
            [
                (
                    "system",
                    "Convert ranked Quick Plan provider outputs into safe planner context.",
                ),
                ("human", prompt),
            ]
        )
        return _normalize_provider_brief(brief, module_outputs=module_outputs)
    except Exception:
        logger.warning(
            "Quick Plan provider brief returned no usable output.",
            exc_info=True,
        )
        return None


def _normalize_provider_brief(
    brief: QuickPlanProviderBrief,
    *,
    module_outputs: TripModuleOutputs,
) -> QuickPlanProviderBrief:
    missing = list(brief.missing_provider_facts)
    caveats = list(brief.fact_safety_caveats)
    outbound = next(
        (flight for flight in module_outputs.flights if flight.direction == "outbound"),
        None,
    )
    returning = next(
        (flight for flight in module_outputs.flights if flight.direction == "return"),
        None,
    )
    stay = module_outputs.hotels[0] if module_outputs.hotels else None

    for flight in module_outputs.flights[:2]:
        missing.extend(_missing_flight_facts(flight))
    if stay:
        missing.extend(_missing_hotel_facts(stay))

    if missing:
        caveats.append(
            "Do not present missing provider facts as confirmed; keep them as "
            "planner estimates or open checks."
        )

    return brief.model_copy(
        update={
            "selected_outbound_flight": _flight_summary(outbound)
            or brief.selected_outbound_flight,
            "selected_return_flight": _flight_summary(returning)
            or brief.selected_return_flight,
            "selected_stay_base": _hotel_summary(stay) or brief.selected_stay_base,
            "missing_provider_facts": list(dict.fromkeys(missing))[:10],
            "fact_safety_caveats": list(dict.fromkeys(caveats))[:10],
        }
    )


def _missing_flight_facts(flight: FlightDetail) -> list[str]:
    missing: list[str] = []
    if flight.direction and not flight.departure_time:
        missing.append(f"{flight.direction} flight departure time")
    if flight.direction and not flight.arrival_time:
        missing.append(f"{flight.direction} flight arrival time")
    if not (flight.fare_amount or flight.price_text):
        missing.append(f"{flight.direction or 'flight'} fare")
    return missing


def _missing_hotel_facts(hotel: HotelStayDetail) -> list[str]:
    missing: list[str] = []
    if hotel.nightly_rate_amount is None:
        missing.append("hotel nightly rate")
    if not hotel.check_in:
        missing.append("hotel check-in time")
    if not hotel.check_out:
        missing.append("hotel check-out time")
    return missing


def _flight_summary(flight: FlightDetail | None) -> QuickPlanProviderFlightAnchor | None:
    if flight is None:
        return None
    return QuickPlanProviderFlightAnchor.model_validate(
        flight.model_dump(
            mode="json",
            include={
                "id",
                "direction",
                "carrier",
                "flight_number",
                "departure_airport",
                "arrival_airport",
                "departure_time",
                "arrival_time",
                "duration_text",
                "price_text",
                "fare_amount",
                "fare_currency",
                "stop_count",
                "timing_quality",
            },
        )
    )


def _hotel_summary(hotel: HotelStayDetail | None) -> QuickPlanProviderStayAnchor | None:
    if hotel is None:
        return None
    return QuickPlanProviderStayAnchor.model_validate(
        hotel.model_dump(
            mode="json",
            include={
                "id",
                "hotel_name",
                "area",
                "address",
                "nightly_rate_amount",
                "nightly_rate_currency",
                "check_in",
                "check_out",
                "source_label",
            },
        )
    )
