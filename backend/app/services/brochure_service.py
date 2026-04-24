from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import cast
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trip import TripModel
from app.repositories.brochure_snapshot_repository import (
    create_brochure_snapshot as create_brochure_snapshot_record,
    get_brochure_snapshot as get_brochure_snapshot_record,
    get_latest_brochure_snapshot as get_latest_brochure_snapshot_record,
    get_next_brochure_version_number,
    list_brochure_snapshots as list_brochure_snapshots_record,
)
from app.repositories.trip_repository import get_trip_for_user
from app.schemas.brochure import (
    BrochureAdvancedSectionSummary,
    BrochureBudgetSummary,
    BrochureHeroImage,
    BrochureHistoryItem,
    BrochureHistoryResponse,
    BrochureItineraryDay,
    BrochureMetric,
    BrochureResourceLink,
    BrochureSection,
    BrochureSnapshot,
    BrochureSnapshotPayload,
    BrochureSnapshotSummary,
    BrochureTravelSummary,
    BrochureWarning,
)
from app.schemas.trip_draft import TripDraft
from app.schemas.trip_planning import ActivityDetail, HotelStayDetail, TimelineItem
from app.utils.destination_images import get_destination_hero_image


def create_brochure_snapshot_for_trip(
    db: Session,
    *,
    trip: TripModel,
    draft: TripDraft,
) -> BrochureSnapshot:
    version_number = get_next_brochure_version_number(db, trip.id)
    finalized_at = draft.status.finalized_at or datetime.now(UTC)
    payload = build_brochure_snapshot_payload(trip=trip, draft=draft, version_number=version_number)

    snapshot = create_brochure_snapshot_record(
        db,
        snapshot_id=f"brochure_{uuid4().hex}",
        trip_id=trip.id,
        version_number=version_number,
        finalized_at=finalized_at,
        payload=payload.model_dump(mode="json"),
        warnings=[warning.model_dump(mode="json") for warning in payload.warnings],
        hero_image=payload.hero_image.model_dump(mode="json"),
        summary={
            "title": payload.title,
            "route_text": payload.route_text,
            "travel_window_text": payload.travel_window_text,
            "party_text": payload.party_text,
            "budget_text": payload.budget_text,
        },
    )
    return _build_snapshot_response(snapshot)


def list_trip_brochures(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> BrochureHistoryResponse:
    _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    snapshots = list_brochure_snapshots_record(db, trip_id)
    return BrochureHistoryResponse(
        items=[
            BrochureHistoryItem(
                **_build_snapshot_summary(snapshot).model_dump(),
                is_latest=bool(snapshot.is_latest),
            )
            for snapshot in snapshots
        ]
    )


def get_latest_trip_brochure(
    db: Session,
    *,
    trip_id: str,
    user_id: str,
) -> BrochureSnapshot:
    _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    snapshot = get_latest_brochure_snapshot_record(db, trip_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No brochure snapshot exists for that trip yet.",
        )
    return _build_snapshot_response(snapshot)


def get_trip_brochure(
    db: Session,
    *,
    trip_id: str,
    snapshot_id: str,
    user_id: str,
) -> BrochureSnapshot:
    _get_owned_trip(db, trip_id=trip_id, user_id=user_id)
    snapshot = get_brochure_snapshot_record(db, trip_id, snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That brochure version was not found.",
        )
    return _build_snapshot_response(snapshot)


def render_trip_brochure_pdf(
    db: Session,
    *,
    trip_id: str,
    snapshot_id: str,
    user_id: str,
) -> tuple[bytes, str]:
    snapshot = get_trip_brochure(db, trip_id=trip_id, snapshot_id=snapshot_id, user_id=user_id)
    html = build_brochure_print_html(snapshot)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF rendering is not available yet because Playwright is not installed.",
        ) from exc

    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
            except Exception:
                browser = playwright.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 2200})
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "14mm", "right": "12mm", "bottom": "14mm", "left": "12mm"},
            )
            browser.close()
    except Exception as exc:  # pragma: no cover - environment-specific
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The brochure PDF renderer is currently unavailable.",
        ) from exc

    return pdf_bytes, snapshot.pdf_file_name


def build_brochure_snapshot_payload(
    *,
    trip: TripModel,
    draft: TripDraft,
    version_number: int,
) -> BrochureSnapshotPayload:
    destination_label = draft.configuration.to_location
    origin_label = draft.configuration.from_location
    route_text = _build_route_text(origin_label, destination_label)
    travel_window_text = _build_travel_window_text(draft)
    party_text = _build_party_text(draft)
    budget_text = _build_budget_text(draft)
    warnings = _build_warnings(draft)
    advanced_section_summaries = _build_advanced_section_summaries(draft)
    flexible_items = _build_flexible_items(draft, advanced_section_summaries)
    worth_reviewing_notes = _build_worth_reviewing_notes(
        draft,
        advanced_section_summaries,
    )
    hero_image = BrochureHeroImage(
        url=get_destination_hero_image(destination_label),
        alt_text=f"{destination_label or 'Destination'} hero image for brochure cover",
        attribution="Unsplash",
    )

    return BrochureSnapshotPayload(
        title=draft.title,
        route_text=route_text,
        origin_label=origin_label,
        destination_label=destination_label,
        travel_window_text=travel_window_text,
        party_text=party_text,
        budget_text=budget_text,
        style_tags=list(draft.configuration.activity_styles),
        module_tags=_build_module_tags(draft),
        executive_summary=_build_executive_summary(draft, route_text),
        hero_image=hero_image,
        metrics=_build_metrics(draft),
        sections=[
            BrochureSection(id="summary", title="Trip summary", summary="The travel shape at a glance."),
            BrochureSection(id="proposal", title="Proposal framing", summary="The Advanced Planning choices that shaped this saved version."),
            BrochureSection(id="warnings", title="Warnings", summary="Timing, logistics, and budget notes to keep in mind."),
            BrochureSection(id="itinerary", title="Day by day itinerary", summary="The current itinerary from departure through return."),
            BrochureSection(id="flights", title="Flights and transfers", summary="Air legs, timing posture, and transfer-sensitive moments."),
            BrochureSection(id="stays", title="Where you are staying", summary="Hotel posture and stay anchors."),
            BrochureSection(id="budget", title="Budget and movement", summary="The trip spend posture and movement load."),
            BrochureSection(id="highlights", title="Highlights and notes", summary="The destination moments this trip is built around."),
        ],
        advanced_review_status=draft.conversation.advanced_review_planning.readiness_status
        if _has_advanced_brochure_context(draft)
        else None,
        advanced_review_summary=draft.conversation.advanced_review_planning.workspace_summary
        if _has_advanced_brochure_context(draft)
        else None,
        advanced_section_summaries=advanced_section_summaries,
        trip_character_summary=_build_trip_character_summary(draft),
        planned_experience_summary=_build_planned_experience_summary(draft),
        flexible_items=flexible_items,
        worth_reviewing_notes=worth_reviewing_notes,
        warnings=warnings,
        itinerary_days=_group_itinerary_days(draft.timeline),
        flights=list(draft.module_outputs.flights),
        stays=list(draft.module_outputs.hotels),
        weather=list(draft.module_outputs.weather),
        highlights=list(draft.module_outputs.activities),
        planning_notes=_build_planning_notes(draft),
        budget_summary=_build_budget_summary(draft),
        travel_summary=_build_travel_summary(draft),
        resources=_build_resource_links(trip.id, version_number, destination_label),
    )


def _has_advanced_brochure_context(draft: TripDraft) -> bool:
    conversation = draft.conversation
    return bool(
        conversation.planning_mode == "advanced"
        or conversation.advanced_review_planning.section_cards
        or conversation.trip_style_planning.completion_summary
        or conversation.activity_planning.completion_summary
        or conversation.flight_planning.completion_summary
        or conversation.stay_planning.selected_hotel_id
    )


def _build_advanced_section_summaries(
    draft: TripDraft,
) -> list[BrochureAdvancedSectionSummary]:
    if not _has_advanced_brochure_context(draft):
        return []

    review_cards = draft.conversation.advanced_review_planning.section_cards
    if review_cards:
        return [
            BrochureAdvancedSectionSummary(
                id=card.id,
                title=card.title,
                status=card.status,
                summary=card.summary[:320],
                notes=card.notes[:4],
            )
            for card in review_cards[:8]
        ]

    fallback_cards: list[BrochureAdvancedSectionSummary] = []
    flight = draft.conversation.flight_planning
    if flight.completion_summary or flight.selection_summary:
        fallback_cards.append(
            BrochureAdvancedSectionSummary(
                id="flight",
                title="Working flights",
                status="ready" if flight.selection_status == "completed" else "flexible",
                summary=(
                    flight.completion_summary
                    or flight.selection_summary
                    or "Flights were kept flexible in this saved proposal."
                )[:320],
                notes=[
                    note
                    for note in [
                        flight.arrival_day_impact_summary,
                        flight.departure_day_impact_summary,
                        *flight.timing_review_notes,
                    ]
                    if note
                ][:4],
            )
        )
    stay = draft.conversation.stay_planning
    if stay.selected_hotel_name or stay.selected_stay_direction:
        stay_needs_review = (
            stay.selection_status == "needs_review"
            or stay.hotel_selection_status == "needs_review"
            or stay.compatibility_status in {"strained", "conflicted"}
            or stay.hotel_compatibility_status in {"strained", "conflicted"}
        )
        fallback_cards.append(
            BrochureAdvancedSectionSummary(
                id="stay",
                title="Current stay",
                status="needs_review" if stay_needs_review else "ready",
                summary=(
                    stay.hotel_selection_rationale
                    or stay.selection_rationale
                    or f"{stay.selected_hotel_name or stay.selected_stay_direction} is the current stay choice."
                )[:320],
                notes=[*stay.compatibility_notes, *stay.hotel_compatibility_notes][:4],
            )
        )
    trip_style = draft.conversation.trip_style_planning
    if trip_style.completion_summary:
        fallback_cards.append(
            BrochureAdvancedSectionSummary(
                id="trip_style",
                title="Trip character",
                status="ready" if trip_style.substep == "completed" else "flexible",
                summary=trip_style.completion_summary[:320],
                notes=[
                    label
                    for label in [
                        _trip_direction_primary_label(
                            trip_style.selected_primary_direction
                        ),
                        _trip_pace_label(trip_style.selected_pace),
                    ]
                    if label
                ][:4],
            )
        )
    activity = draft.conversation.activity_planning
    if activity.completion_summary or activity.schedule_summary:
        fallback_cards.append(
            BrochureAdvancedSectionSummary(
                id="activities",
                title="Planned experiences",
                status="ready"
                if activity.completion_status == "completed"
                else "flexible",
                summary=(
                    activity.completion_summary
                    or activity.schedule_summary
                    or "Experiences were still taking shape in this saved proposal."
                )[:320],
                notes=activity.schedule_notes[:4],
            )
        )
    weather = draft.conversation.weather_planning
    if weather.workspace_summary:
        fallback_cards.append(
            BrochureAdvancedSectionSummary(
                id="weather",
                title="Weather notes",
                status="ready" if weather.results_status == "ready" else "flexible",
                summary=weather.workspace_summary[:320],
                notes=[
                    *weather.day_impact_summaries[:2],
                    *weather.activity_influence_notes[:2],
                ][:4],
            )
        )
    return fallback_cards[:8]


def _build_trip_character_summary(draft: TripDraft) -> str | None:
    if not _has_advanced_brochure_context(draft):
        return None
    trip_style = draft.conversation.trip_style_planning
    if trip_style.completion_summary:
        return trip_style.completion_summary
    style_parts = [
        _trip_direction_primary_label(trip_style.selected_primary_direction),
        _trip_pace_label(trip_style.selected_pace),
    ]
    style_text = ", ".join(part for part in style_parts if part)
    if style_text:
        return f"This proposal is shaped around {style_text.lower()}."
    if draft.configuration.custom_style:
        return f"This proposal preserves the requested feel: {draft.configuration.custom_style}."
    if draft.configuration.activity_styles:
        return (
            "This proposal keeps the original trip-style memory visible: "
            + ", ".join(draft.configuration.activity_styles)
            + "."
        )
    return None


def _build_planned_experience_summary(draft: TripDraft) -> str | None:
    if not _has_advanced_brochure_context(draft):
        return None
    activity = draft.conversation.activity_planning
    if activity.completion_summary:
        return activity.completion_summary
    if activity.schedule_summary:
        return activity.schedule_summary
    if draft.module_outputs.activities:
        lead_titles = ", ".join(
            activity_detail.title
            for activity_detail in draft.module_outputs.activities[:3]
        )
        return f"The proposal highlights {lead_titles}."
    return None


def _build_flexible_items(
    draft: TripDraft,
    advanced_section_summaries: list[BrochureAdvancedSectionSummary],
) -> list[str]:
    if not _has_advanced_brochure_context(draft):
        return []
    items: list[str] = []
    review = draft.conversation.advanced_review_planning
    if review.open_summary:
        items.append(review.open_summary)
    for section in advanced_section_summaries:
        if section.status == "flexible":
            items.append(f"{section.title}: {section.summary}")
    activity = draft.conversation.activity_planning
    if activity.reserved_candidate_ids:
        items.append(
            f"{len(activity.reserved_candidate_ids)} experience idea"
            f"{'s' if len(activity.reserved_candidate_ids) != 1 else ''} saved for later."
        )
    flight = draft.conversation.flight_planning
    if flight.selection_status == "kept_open":
        items.append("Flights were intentionally kept flexible in this proposal.")
    return _dedupe_text(items)[:8]


def _build_worth_reviewing_notes(
    draft: TripDraft,
    advanced_section_summaries: list[BrochureAdvancedSectionSummary],
) -> list[str]:
    if not _has_advanced_brochure_context(draft):
        return []
    review = draft.conversation.advanced_review_planning
    notes = [
        *review.review_notes,
        *[
            f"{conflict.summary} Suggested next step: {conflict.suggested_repair}"
            for conflict in draft.conversation.planner_conflicts
        ],
        *[
            note
            for section in advanced_section_summaries
            if section.status == "needs_review"
            for note in section.notes
        ],
    ]
    return _dedupe_text(notes)[:8]


def _trip_direction_primary_label(value: str | None) -> str | None:
    if not value:
        return None
    return {
        "food_led": "Food-led",
        "culture_led": "Culture-led",
        "nightlife_led": "Nightlife-led",
        "outdoors_led": "Outdoors-led",
        "balanced": "Balanced",
    }.get(value, value.replace("_", " ").title())


def _trip_pace_label(value: str | None) -> str | None:
    if not value:
        return None
    return {
        "slow": "Slow pace",
        "balanced": "Balanced pace",
        "full": "Full pace",
    }.get(value, value.replace("_", " ").title())


def _dedupe_text(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(text)
    return deduped


def build_brochure_print_html(snapshot: BrochureSnapshot) -> str:
    payload = snapshot.payload
    advanced_section_rows = "".join(
        f"""
        <article class="proposal-card {escape(section.status)}">
          <div class="proposal-kicker">{escape(section.status.replace('_', ' '))}</div>
          <h3>{escape(section.title)}</h3>
          <p>{escape(section.summary)}</p>
          {''.join(f'<span>{escape(note)}</span>' for note in section.notes)}
        </article>
        """
        for section in payload.advanced_section_summaries
    )
    flexible_rows = "".join(
        f'<li>{escape(item)}</li>' for item in payload.flexible_items
    )
    worth_reviewing_rows = "".join(
        f'<li>{escape(note)}</li>' for note in payload.worth_reviewing_notes
    )
    warning_cards = "".join(
        f"""
        <article class="warning-card">
          <div class="warning-kicker">{escape(warning.category.replace('_', ' '))}</div>
          <h3>{escape(warning.title)}</h3>
          <p>{escape(warning.message)}</p>
        </article>
        """
        for warning in payload.warnings
    )
    itinerary_sections = "".join(
        f"""
        <section class="day-block">
          <div class="day-header">
            <p class="eyebrow">{escape(day.label)}</p>
            <h3>{escape(day.summary or day.label)}</h3>
          </div>
          <div class="timeline-stack">{''.join(_render_timeline_item_html(item, payload.warnings) for item in day.items)}</div>
        </section>
        """
        for day in payload.itinerary_days
    )
    flight_rows = "".join(
        f"""
        <article class="detail-row">
          <h3>{escape(flight.carrier)}{f" {escape(flight.flight_number)}" if flight.flight_number else ''}</h3>
          <p>{escape(flight.departure_airport)} to {escape(flight.arrival_airport)}</p>
          <span>{escape(flight.duration_text or 'Timing still open')}</span>
        </article>
        """
        for flight in payload.flights
    )
    stay_rows = "".join(
        f"""
        <article class="detail-row">
          <h3>{escape(stay.hotel_name)}</h3>
          <p>{escape(stay.area or 'Area still open')}</p>
          <span>{escape(_format_optional_datetime(stay.check_in))} to {escape(_format_optional_datetime(stay.check_out))}</span>
        </article>
        """
        for stay in payload.stays
    )
    highlight_rows = "".join(
        f"""
        <article class="highlight-row">
          <h3>{escape(highlight.title)}</h3>
          <p>{escape(' | '.join(part for part in [highlight.category, highlight.day_label, highlight.time_label] if part) or 'Destination highlight')}</p>
          {f"<span>{escape(highlight.notes[0])}</span>" if highlight.notes else ""}
        </article>
        """
        for highlight in payload.highlights
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{escape(payload.title)} brochure</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f8f3ea;
      --panel: rgba(255,255,255,0.82);
      --ink: #1b1713;
      --muted: #6d6459;
      --line: rgba(76,55,35,0.12);
      --accent: #0f6f67;
      --accent-deep: #163b36;
      --gold: #a8732a;
      --accent-soft: rgba(15,111,103,0.1);
      --warning: #b66a1b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background: linear-gradient(180deg, #f8f6f0 0%, #eef4f2 100%);
    }}
    main {{ padding: 28px; }}
    .cover {{
      min-height: 360px;
      border-radius: 28px;
      overflow: hidden;
      position: relative;
      background: linear-gradient(180deg, rgba(13,30,28,.10), rgba(13,30,28,.62)), url('{escape(payload.hero_image.url)}') center/cover no-repeat;
      padding: 28px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #fff8f0;
    }}
    .cover h1 {{ font-size: 40px; line-height: 1.02; margin: 0; max-width: 760px; }}
    .cover p {{ max-width: 640px; color: rgba(255,248,240,.88); }}
    .cover-meta {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .pill {{
      border: 1px solid rgba(255,248,240,.22);
      background: rgba(255,248,240,.12);
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .grid {{ display: grid; gap: 20px; margin-top: 22px; }}
    .top-grid {{ grid-template-columns: 1.2fr .8fr; }}
    .panel {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 24px;
      padding: 22px;
      backdrop-filter: blur(12px);
    }}
    .panel h2 {{ margin: 0 0 12px; font-size: 20px; }}
    .proposal-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(2, minmax(0,1fr)); }}
    .proposal-card {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,.58);
      border-radius: 18px;
      padding: 16px;
      break-inside: avoid;
    }}
    .proposal-kicker {{
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: .13em;
      font-size: 10px;
      margin-bottom: 8px;
    }}
    .proposal-card span {{
      display: block;
      margin-top: 7px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .note-list {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.55;
    }}
    .summary-grid, .metric-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(2, minmax(0,1fr)); }}
    .metric {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .metric strong {{ display: block; font-size: 24px; margin-top: 4px; }}
    .warning-grid {{ display: grid; gap: 12px; }}
    .warning-card {{
      border-left: 3px solid var(--warning);
      padding: 12px 0 0 14px;
    }}
    .warning-kicker {{
      color: var(--warning);
      text-transform: uppercase;
      letter-spacing: .12em;
      font-size: 11px;
      margin-bottom: 8px;
    }}
    .warning-card h3, .detail-row h3, .highlight-row h3, .day-header h3, .proposal-card h3 {{ margin: 0; font-size: 17px; }}
    .warning-card p, .detail-row p, .highlight-row p, .timeline-item p, .panel p {{ color: var(--muted); line-height: 1.6; }}
    .timeline-stack {{ display: grid; gap: 14px; }}
    .day-block + .day-block {{ margin-top: 18px; }}
    .eyebrow {{
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: .12em;
      font-size: 11px;
      margin: 0 0 6px;
    }}
    .timeline-item {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .timeline-item-head {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: baseline;
    }}
    .timeline-inline-warning {{
      margin-top: 8px;
      border-radius: 14px;
      background: var(--accent-soft);
      color: var(--accent);
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.5;
    }}
    .detail-row, .highlight-row {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
      margin-top: 12px;
    }}
    .footer {{
      margin-top: 24px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="cover">
      <div>
        <div class="cover-meta">
          <span class="pill">Wandrix brochure</span>
          <span class="pill">Version {snapshot.version_number}</span>
          <span class="pill">{escape(payload.travel_window_text)}</span>
        </div>
      </div>
      <div>
        <h1>{escape(payload.title)}</h1>
        <p>{escape(payload.executive_summary)}</p>
        <div class="cover-meta">
          <span class="pill">{escape(payload.route_text)}</span>
          <span class="pill">{escape(payload.party_text)}</span>
          <span class="pill">{escape(payload.budget_text)}</span>
        </div>
      </div>
    </section>
    <section class="grid top-grid">
      <article class="panel">
        <h2>Proposal at a glance</h2>
        <div class="summary-grid">
          <div><p>Route</p><strong>{escape(payload.route_text)}</strong></div>
          <div><p>Trip window</p><strong>{escape(payload.travel_window_text)}</strong></div>
          <div><p>Travel party</p><strong>{escape(payload.party_text)}</strong></div>
          <div><p>Budget posture</p><strong>{escape(payload.budget_text)}</strong></div>
        </div>
        <div class="metric-grid" style="margin-top:18px;">
          {''.join(f'<div class="metric"><p>{escape(metric.label)}</p><strong>{escape(metric.value)}</strong>{f"<p>{escape(metric.note)}</p>" if metric.note else ""}</div>' for metric in payload.metrics)}
        </div>
      </article>
      <article class="panel">
        <h2>Review notes</h2>
        <div class="warning-grid">
          {warning_cards or '<p>No active travel warnings were captured in this snapshot.</p>'}
        </div>
      </article>
    </section>
    <section class="panel">
      <h2>Trip character</h2>
      <p>{escape(payload.trip_character_summary or payload.executive_summary)}</p>
      {f'<p><strong>{escape(payload.planned_experience_summary)}</strong></p>' if payload.planned_experience_summary else ''}
      {f'<p>{escape(payload.advanced_review_summary)}</p>' if payload.advanced_review_summary else ''}
      {f'<div class="proposal-grid">{advanced_section_rows}</div>' if advanced_section_rows else ''}
    </section>
    {(flexible_rows or worth_reviewing_rows) and f'''
    <section class="grid top-grid">
      <article class="panel">
        <h2>Still flexible</h2>
        <ul class="note-list">{flexible_rows or '<li>No intentionally flexible items were captured.</li>'}</ul>
      </article>
      <article class="panel">
        <h2>Worth reviewing</h2>
        <ul class="note-list">{worth_reviewing_rows or '<li>No additional review notes were captured.</li>'}</ul>
      </article>
    </section>
    ''' or ''}
    <section class="panel">
      <h2>Proposal itinerary</h2>
      {itinerary_sections or '<p>The day-by-day itinerary is still being shaped.</p>'}
    </section>
    <section class="grid top-grid">
      <article class="panel">
        <h2>Flights and transfers</h2>
        {flight_rows or '<p>Flight details were not locked in when this brochure snapshot was created.</p>'}
      </article>
      <article class="panel">
        <h2>Where you are staying</h2>
        {stay_rows or '<p>Hotel selection was still open when this brochure snapshot was saved.</p>'}
      </article>
    </section>
    <section class="grid top-grid">
      <article class="panel">
        <h2>Budget and movement</h2>
        <p>{escape(payload.budget_summary.headline)}</p>
        <strong>{escape(payload.budget_summary.detail)}</strong>
        <div style="height:14px"></div>
        <p>{escape(payload.travel_summary.headline)}</p>
        <strong>{escape(payload.travel_summary.detail)}</strong>
      </article>
      <article class="panel">
        <h2>Highlights and notes</h2>
        {highlight_rows or '<p>Highlights were still being curated when this snapshot was created.</p>'}
        {''.join(f'<div class="detail-row"><p>{escape(note)}</p></div>' for note in payload.planning_notes)}
      </article>
    </section>
    <footer class="footer">
      <span>Saved from finalized trip state on {escape(_format_optional_datetime(snapshot.finalized_at))}</span>
      <span>{escape(payload.hero_image.attribution or 'Destination imagery')}</span>
    </footer>
  </main>
</body>
</html>"""


def _render_timeline_item_html(item: TimelineItem, warnings: list[BrochureWarning]) -> str:
    related_warnings = [warning for warning in warnings if item.id in warning.related_timeline_ids]
    warning_html = "".join(
        f'<div class="timeline-inline-warning">{escape(warning.title)}: {escape(warning.message)}</div>'
        for warning in related_warnings
    )
    timing = " to ".join(
        value for value in [_format_optional_datetime(item.start_at), _format_optional_datetime(item.end_at)] if value != "TBD"
    ) or escape(item.location_label or "Timing still open")
    summary = f"<p>{escape(item.summary)}</p>" if item.summary else ""
    venue_line = (
        f"<p><strong>Venue:</strong> {escape(item.venue_name)}</p>"
        if item.venue_name
        else ""
    )
    metadata_line = "".join(
        f"<p>{escape(value)}</p>"
        for value in [item.status_text, item.price_text, item.availability_text]
        if value
    )
    link_line = (
        f'<p><a href="{escape(item.source_url)}" target="_blank" rel="noopener noreferrer">Open event listing</a></p>'
        if item.type == "event" and item.source_url
        else ""
    )
    return f"""
    <article class="timeline-item">
      <div class="timeline-item-head">
        <h3>{escape(item.title)}</h3>
        <span>{timing}</span>
      </div>
      {venue_line}
      {summary}
      {metadata_line}
      {''.join(f'<p>{escape(detail)}</p>' for detail in item.details)}
      {link_line}
      {warning_html}
    </article>
    """


def _build_snapshot_response(snapshot) -> BrochureSnapshot:
    payload = BrochureSnapshotPayload.model_validate(snapshot.payload)
    return BrochureSnapshot(
        snapshot_id=snapshot.id,
        trip_id=snapshot.trip_id,
        version_number=snapshot.version_number,
        status=snapshot.status,
        finalized_at=snapshot.finalized_at,
        created_at=snapshot.created_at,
        pdf_file_name=_build_pdf_file_name(payload, snapshot.version_number),
        payload=payload,
    )


def _build_snapshot_summary(snapshot) -> BrochureSnapshotSummary:
    payload = BrochureSnapshotPayload.model_validate(snapshot.payload)
    return BrochureSnapshotSummary(
        snapshot_id=snapshot.id,
        trip_id=snapshot.trip_id,
        version_number=snapshot.version_number,
        status=snapshot.status,
        finalized_at=snapshot.finalized_at,
        created_at=snapshot.created_at,
        pdf_file_name=_build_pdf_file_name(payload, snapshot.version_number),
    )


def _build_route_text(origin_label: str | None, destination_label: str | None) -> str:
    if origin_label or destination_label:
        return f"{origin_label or 'Origin'} to {destination_label or 'Destination'}"
    return "Route still being shaped"


def _build_travel_window_text(draft: TripDraft) -> str:
    start_date = draft.configuration.start_date
    end_date = draft.configuration.end_date
    if start_date and end_date:
        return f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
    if draft.configuration.travel_window:
        return draft.configuration.travel_window
    if draft.configuration.trip_length:
        return draft.configuration.trip_length
    return "Travel dates still open"


def _build_party_text(draft: TripDraft) -> str:
    adults = draft.configuration.travelers.adults or 0
    children = draft.configuration.travelers.children or 0
    if adults == 0 and children == 0:
        return "Travel party still open"
    return f"{adults} adults and {children} children"


def _build_budget_text(draft: TripDraft) -> str:
    if draft.configuration.budget_gbp:
        return f"GBP {int(draft.configuration.budget_gbp):,}"
    if draft.configuration.budget_posture:
        return draft.configuration.budget_posture.replace("_", " ").title()
    return "Budget still being shaped"


def _build_module_tags(draft: TripDraft) -> list[str]:
    return [
        module_name
        for module_name, enabled in draft.configuration.selected_modules.model_dump().items()
        if enabled is True
    ]


def _build_executive_summary(draft: TripDraft, route_text: str) -> str:
    if draft.conversation.last_turn_summary:
        return draft.conversation.last_turn_summary
    if draft.timeline:
        return f"{route_text}. This brochure captures the current finalized trip structure across flights, stays, weather, and destination moments."
    return f"{route_text}. This brochure captures the current finalized travel plan and the details that were ready to lock in."


def _group_itinerary_days(items: list[TimelineItem]) -> list[BrochureItineraryDay]:
    grouped: dict[str, list[TimelineItem]] = {}
    for item in items:
        key = item.day_label or "Trip flow"
        grouped.setdefault(key, []).append(item)

    itinerary_days: list[BrochureItineraryDay] = []
    for index, (label, day_items) in enumerate(grouped.items(), start=1):
        summary = next((item.summary for item in day_items if item.summary), None)
        itinerary_days.append(
            BrochureItineraryDay(
                id=f"day_{index}",
                label=label,
                summary=summary,
                items=day_items,
            )
        )
    return itinerary_days


def _build_metrics(draft: TripDraft) -> list[BrochureMetric]:
    return [
        BrochureMetric(
            label="Timeline moments",
            value=str(len(draft.timeline)),
            note="Saved in this brochure version.",
        ),
        BrochureMetric(
            label="Warnings",
            value=str(len(_build_warnings(draft))),
            note="Structured planning risks surfaced near the top.",
        ),
        BrochureMetric(
            label="Highlights",
            value=str(len(draft.module_outputs.activities)),
            note="Destination moments captured in the snapshot.",
        ),
        BrochureMetric(
            label="Hotels",
            value=str(len(draft.module_outputs.hotels)),
            note="Stay anchors included in the final brochure state.",
        ),
    ]


def _build_planning_notes(draft: TripDraft) -> list[str]:
    notes = [f"Still refining: {field_name.replace('_', ' ')}." for field_name in draft.status.missing_fields]
    if not draft.module_outputs.flights:
        notes.append("Exact flight inventory was not locked when this brochure snapshot was created.")
    if not draft.module_outputs.hotels:
        notes.append("Accommodation selection is still open and may change after this version.")
    return notes


def _build_budget_summary(draft: TripDraft) -> BrochureBudgetSummary:
    headline = "Budget posture"
    if draft.configuration.budget_gbp:
        detail = f"The trip is currently framed around roughly GBP {int(draft.configuration.budget_gbp):,}, subject to live inventory and any hotel changes."
    elif draft.configuration.budget_posture:
        detail = f"The current travel posture is {draft.configuration.budget_posture.replace('_', ' ')} while exact flight and stay pricing continues to move."
    else:
        detail = "Budget has not been locked yet, so final brochure totals should be treated as directional rather than exact."
    return BrochureBudgetSummary(headline=headline, detail=detail)


def _build_travel_summary(draft: TripDraft) -> BrochureTravelSummary:
    transfer_count = sum(1 for item in draft.timeline if item.type == "transfer")
    flight_count = len(draft.module_outputs.flights)
    detail = f"{flight_count} flight segments and {transfer_count} transfer blocks are reflected in this brochure version."
    if transfer_count >= 3:
        detail += " Movement load is fairly dense, so timing buffers matter."
    return BrochureTravelSummary(headline="Travel movement", detail=detail)


def _build_resource_links(trip_id: str, version_number: int, destination_label: str | None) -> list[BrochureResourceLink]:
    links = [
        BrochureResourceLink(
            label="Open brochure",
            url=f"/brochure/{trip_id}?version={version_number}",
        ),
        BrochureResourceLink(
            label="Saved trips",
            url="/trips?filter=brochure",
        ),
    ]
    if destination_label:
        links.append(
            BrochureResourceLink(
                label="Destination map",
                url=f"https://www.google.com/maps/search/{destination_label.replace(' ', '+')}",
            )
        )
    return links


def _build_warnings(draft: TripDraft) -> list[BrochureWarning]:
    warnings: list[BrochureWarning] = []

    if any(not flight.departure_time or not flight.arrival_time for flight in draft.module_outputs.flights) or not draft.module_outputs.flights:
        related_ids = [item.id for item in draft.timeline if item.type == "flight"]
        warnings.append(
            BrochureWarning(
                id="warning_flights_pending",
                category="timing",
                title="Flight timing is not fully locked",
                message="Exact flight departure and arrival times are still incomplete, so airport timing should be treated as provisional.",
                related_timeline_ids=related_ids,
            )
        )

    if not draft.module_outputs.hotels:
        related_ids = [item.id for item in draft.timeline if item.type == "hotel"]
        warnings.append(
            BrochureWarning(
                id="warning_hotel_pending",
                category="selection_pending",
                title="Hotel selection is still open",
                message="The trip structure includes a stay plan, but the final hotel choice was not locked at the moment this brochure was saved.",
                related_timeline_ids=related_ids,
            )
        )

    if draft.configuration.start_date is None or draft.configuration.end_date is None:
        warnings.append(
            BrochureWarning(
                id="warning_weather_window_open",
                category="weather",
                title="Weather remains date-sensitive",
                message="Dates are not fully locked, so the weather outlook should be treated as directional rather than exact.",
                related_timeline_ids=[item.id for item in draft.timeline if item.type == "weather"],
            )
        )

    for item in draft.timeline:
        if item.type == "transfer" and len(item.details) >= 3:
            warnings.append(
                BrochureWarning(
                    id=f"warning_transfer_{item.id}",
                    category="logistics",
                    title="A transfer block looks heavy",
                    message="This transfer carries several movement details, so leave extra buffer around it when traveling.",
                    related_timeline_ids=[item.id],
                )
            )
        lowered = " ".join(item.details).lower()
        if "hill" in lowered or "steep" in lowered:
            warnings.append(
                BrochureWarning(
                    id=f"warning_walking_{item.id}",
                    category="logistics",
                    title="This day may involve heavier walking",
                    message="One of the saved itinerary notes suggests steeper terrain or heavier walking than usual.",
                    related_timeline_ids=[item.id],
                )
            )

    if _has_budget_risk(draft):
        warnings.append(
            BrochureWarning(
                id="warning_budget_risk",
                category="budget",
                title="Budget and trip posture may be pulling apart",
                message="The trip tone and current spend posture do not align cleanly yet, so expect brochure totals to move when flights or stays firm up.",
                related_timeline_ids=[],
            )
        )

    for index, note in enumerate(_build_worth_reviewing_notes(draft, _build_advanced_section_summaries(draft))):
        warnings.append(
            BrochureWarning(
                id=f"warning_advanced_review_{index + 1}",
                category="review",
                title="Worth reviewing before booking",
                message=note[:320],
                related_timeline_ids=[],
            )
        )

    deduped: dict[str, BrochureWarning] = {}
    for warning in warnings:
        deduped[warning.id] = warning
    return list(deduped.values())


def _has_budget_risk(draft: TripDraft) -> bool:
    styles = set(draft.configuration.activity_styles)
    posture = draft.configuration.budget_posture
    budget_gbp = draft.configuration.budget_gbp or 0
    if "luxury" in styles and budget_gbp and budget_gbp < 2500:
        return True
    if posture == "budget" and len(draft.timeline) >= 8:
        return True
    return False


def _build_pdf_file_name(payload: BrochureSnapshotPayload, version_number: int) -> str:
    destination = (payload.destination_label or "trip").strip().lower()
    slug = "".join(ch if ch.isalnum() else "-" for ch in destination).strip("-") or "trip"
    while "--" in slug:
        slug = slug.replace("--", "-")
    return f"wandrix-{slug}-v{version_number}.pdf"


def _format_optional_datetime(value: datetime | None) -> str:
    if value is None:
        return "TBD"
    return value.astimezone(UTC).strftime("%d %b %Y %H:%M UTC")


def _get_owned_trip(db: Session, *, trip_id: str, user_id: str) -> TripModel:
    trip = get_trip_for_user(db, trip_id, user_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip was not found.",
        )
    return cast(TripModel, trip)
