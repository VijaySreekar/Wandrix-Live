from datetime import UTC, datetime
from types import SimpleNamespace

from app.schemas.brochure import BrochureSnapshot, BrochureSnapshotPayload
from app.schemas.trip_draft import TripDraft
from app.services.brochure_service import (
    build_brochure_print_html,
    build_brochure_snapshot_payload,
)


def test_advanced_brochure_payload_includes_review_context() -> None:
    draft = _advanced_draft(review_status="flexible")

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_kyoto"),
        draft=draft,
        version_number=1,
    )

    assert payload.advanced_review_status == "flexible"
    assert payload.advanced_review_summary == "Kyoto has a settled style and flexible flights."
    assert payload.trip_character_summary == "Culture-led, relaxed Kyoto proposal."
    assert payload.planned_experience_summary == "Temples and markets shape the days."
    assert [section.title for section in payload.advanced_section_summaries] == [
        "Trip character",
        "Working flights",
        "Planned experiences",
    ]
    assert "Working flights: Flights can stay flexible until fares settle." in payload.flexible_items
    assert payload.worth_reviewing_notes == []


def test_needs_review_advanced_brochure_creates_caution_notes_and_print_sections() -> None:
    draft = _advanced_draft(review_status="needs_review")

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_kyoto"),
        draft=draft,
        version_number=2,
    )
    snapshot = BrochureSnapshot(
        snapshot_id="brochure_1",
        trip_id="trip_kyoto",
        version_number=2,
        status="latest",
        finalized_at=datetime(2027, 3, 1, 12, 0, tzinfo=UTC),
        created_at=datetime(2027, 3, 1, 12, 0, tzinfo=UTC),
        pdf_file_name="wandrix-kyoto-v2.pdf",
        payload=payload,
    )
    html = build_brochure_print_html(snapshot)

    assert payload.advanced_review_status == "needs_review"
    assert "The selected hotel is far from the strongest evening plan." in payload.worth_reviewing_notes
    assert any(warning.category == "review" for warning in payload.warnings)
    assert "Trip character" in html
    assert "Still flexible" in html
    assert "Worth reviewing" in html
    assert "The selected hotel is far from the strongest evening plan." in html


def test_advanced_brochure_preserves_planner_conflict_notes() -> None:
    draft = _advanced_draft(review_status="flexible", include_conflict=True)

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_kyoto"),
        draft=draft,
        version_number=3,
    )

    assert any("slow pace" in note for note in payload.worth_reviewing_notes)
    assert any("lower-priority ideas" in note for note in payload.worth_reviewing_notes)


def test_minimal_legacy_brochure_payload_still_validates() -> None:
    payload = BrochureSnapshotPayload.model_validate(
        {
            "title": "Legacy Lisbon",
            "route_text": "London to Lisbon",
            "travel_window_text": "May",
            "party_text": "2 adults",
            "budget_text": "Mid range",
            "executive_summary": "A saved trip.",
            "hero_image": {
                "url": "https://example.com/lisbon.jpg",
                "alt_text": "Lisbon",
            },
            "budget_summary": {
                "headline": "Budget posture",
                "detail": "Directional budget.",
            },
            "travel_summary": {
                "headline": "Travel movement",
                "detail": "No movement details.",
            },
        }
    )

    assert payload.advanced_review_status is None
    assert payload.advanced_section_summaries == []
    assert payload.flexible_items == []
    assert payload.worth_reviewing_notes == []


def test_quick_plan_brochure_payload_omits_advanced_sections() -> None:
    draft = TripDraft.model_validate(
        {
            "trip_id": "trip_lisbon",
            "thread_id": "thread_lisbon",
            "title": "Lisbon quick plan",
            "configuration": {
                "to_location": "Lisbon",
                "selected_modules": {
                    "flights": False,
                    "weather": False,
                    "activities": True,
                    "hotels": False,
                },
            },
            "conversation": {
                "planning_mode": "quick",
            },
        }
    )

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_lisbon"),
        draft=draft,
        version_number=1,
    )

    assert payload.advanced_review_status is None
    assert payload.advanced_section_summaries == []
    assert payload.trip_character_summary is None
    assert payload.planned_experience_summary is None


def _advanced_draft(*, review_status: str, include_conflict: bool = False) -> TripDraft:
    review_notes = (
        ["The selected hotel is far from the strongest evening plan."]
        if review_status == "needs_review"
        else []
    )
    stay_status = "needs_review" if review_status == "needs_review" else "ready"
    return TripDraft.model_validate(
        {
            "trip_id": "trip_kyoto",
            "thread_id": "thread_kyoto",
            "title": "Kyoto proposal",
            "configuration": {
                "to_location": "Kyoto",
                "start_date": "2027-03-22",
                "end_date": "2027-03-26",
                "selected_modules": {
                    "flights": True,
                    "weather": True,
                    "activities": True,
                    "hotels": True,
                },
            },
            "timeline": [
                {
                    "id": "day_1_temple",
                    "type": "activity",
                    "title": "Temple morning",
                    "day_label": "Day 1",
                    "summary": "A calm cultural opening.",
                }
            ],
            "module_outputs": {
                "hotels": [
                    {
                        "id": "hotel_gion",
                        "hotel_name": "Gion House",
                        "area": "Gion",
                    }
                ],
                "activities": [
                    {
                        "id": "activity_temple",
                        "title": "Temple morning",
                        "category": "culture",
                        "day_label": "Day 1",
                    }
                ],
                "weather": [
                    {
                        "id": "weather_1",
                        "day_label": "Day 1",
                        "summary": "Mild and clear.",
                        "weather_risk_level": "low",
                    }
                ],
            },
            "conversation": {
                "planning_mode": "advanced",
                "advanced_step": "review",
                "planner_conflicts": [
                    {
                        "id": "conflict_slow_pace_dense_days",
                        "severity": "warning",
                        "category": "schedule_density",
                        "affected_areas": ["Trip character", "Planned experiences"],
                        "summary": "Day 1 may feel fuller than the slow pace you chose.",
                        "evidence": ["Slow pace is selected."],
                        "source_decision_ids": ["trip_style_pace", "selected_activities"],
                        "suggested_repair": "Review the activities plan and move lower-priority ideas into reserve.",
                        "revision_target": "activities",
                    }
                ]
                if include_conflict
                else [],
                "advanced_review_planning": {
                    "readiness_status": review_status,
                    "workspace_summary": "Kyoto has a settled style and flexible flights.",
                    "open_summary": "1 area still flexible.",
                    "review_notes": review_notes,
                    "section_cards": [
                        {
                            "id": "trip_style",
                            "title": "Trip character",
                            "status": "ready",
                            "summary": "Culture-led, relaxed Kyoto proposal.",
                            "notes": ["Culture-led", "Slow pace"],
                        },
                        {
                            "id": "flight",
                            "title": "Working flights",
                            "status": "flexible",
                            "summary": "Flights can stay flexible until fares settle.",
                            "notes": [],
                        },
                        {
                            "id": "activities",
                            "title": "Planned experiences",
                            "status": stay_status,
                            "summary": "Temples and markets shape the days.",
                            "notes": review_notes,
                        },
                    ],
                },
                "trip_style_planning": {
                    "substep": "completed",
                    "selected_primary_direction": "culture_led",
                    "selected_pace": "slow",
                    "completion_summary": "Culture-led, relaxed Kyoto proposal.",
                },
                "activity_planning": {
                    "completion_status": "completed",
                    "completion_summary": "Temples and markets shape the days.",
                    "reserved_candidate_ids": ["activity_market_extra"],
                },
            },
        }
    )
