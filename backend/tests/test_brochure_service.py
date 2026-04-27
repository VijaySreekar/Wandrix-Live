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


def test_advanced_brochure_keeps_deferred_conflicts_and_omits_resolved_conflicts() -> None:
    draft = _advanced_draft(review_status="flexible", include_conflict=True)
    conflict = draft.conversation.planner_conflicts[0]
    conflict.status = "deferred"
    conflict.resolution_summary = "Saved as an intentional caution."
    resolved = conflict.model_copy(
        update={
            "id": "conflict_resolved_density",
            "status": "resolved",
            "summary": "This resolved density note should not appear.",
            "resolution_summary": "Accepted after review.",
            "resolution_action": "resolve",
        }
    )
    draft.conversation.planner_conflicts.append(resolved)

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_kyoto"),
        draft=draft,
        version_number=4,
    )

    assert any("Saved as an intentional caution" in note for note in payload.worth_reviewing_notes)
    assert not any("resolved density" in note for note in payload.worth_reviewing_notes)


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


def test_quick_plan_brochure_payload_includes_accepted_logistics_and_budget() -> None:
    draft = TripDraft.model_validate(
        {
            "trip_id": "trip_paris",
            "thread_id": "thread_paris",
            "title": "Paris quick plan",
            "configuration": {
                "from_location": "London",
                "to_location": "Paris",
                "start_date": "2027-05-01",
                "end_date": "2027-05-03",
                "selected_modules": {
                    "flights": True,
                    "weather": True,
                    "activities": True,
                    "hotels": True,
                },
            },
            "timeline": [
                {
                    "id": "flight_out",
                    "type": "flight",
                    "title": "Outbound flight",
                    "start_at": "2027-05-01T08:00:00Z",
                    "end_at": "2027-05-01T10:00:00Z",
                    "source_module": "flights",
                },
                {
                    "id": "stay_1",
                    "type": "hotel",
                    "title": "Left Bank Stay",
                    "start_at": "2027-05-01T15:00:00Z",
                    "end_at": "2027-05-03T10:00:00Z",
                    "source_module": "hotels",
                },
                {
                    "id": "activity_1",
                    "type": "activity",
                    "title": "Marais food walk",
                    "start_at": "2027-05-02T11:00:00Z",
                    "end_at": "2027-05-02T13:00:00Z",
                    "source_module": "activities",
                },
                {
                    "id": "flight_return",
                    "type": "flight",
                    "title": "Return flight",
                    "start_at": "2027-05-03T18:00:00Z",
                    "end_at": "2027-05-03T20:00:00Z",
                    "source_module": "flights",
                },
            ],
            "module_outputs": {
                "flights": [
                    {
                        "id": "flight_out",
                        "direction": "outbound",
                        "carrier": "BA",
                        "departure_airport": "LHR",
                        "arrival_airport": "CDG",
                        "departure_time": "2027-05-01T08:00:00Z",
                        "arrival_time": "2027-05-01T10:00:00Z",
                        "fare_amount": 120,
                        "fare_currency": "GBP",
                    },
                    {
                        "id": "flight_return",
                        "direction": "return",
                        "carrier": "BA",
                        "departure_airport": "CDG",
                        "arrival_airport": "LHR",
                        "departure_time": "2027-05-03T18:00:00Z",
                        "arrival_time": "2027-05-03T20:00:00Z",
                        "fare_amount": 140,
                        "fare_currency": "GBP",
                    },
                ],
                "hotels": [
                    {
                        "id": "hotel_left_bank",
                        "hotel_name": "Left Bank Stay",
                        "area": "Saint-Germain",
                        "nightly_rate_amount": 180,
                        "nightly_rate_currency": "GBP",
                        "check_in": "2027-05-01T15:00:00Z",
                        "check_out": "2027-05-03T10:00:00Z",
                    }
                ],
                "activities": [
                    {
                        "id": "activity_1",
                        "title": "Marais food walk",
                    }
                ],
            },
            "budget_estimate": {
                "total_low_amount": 700,
                "total_high_amount": 920,
                "currency": "GBP",
                "categories": [
                    {
                        "category": "flights",
                        "label": "Flights",
                        "low_amount": 260,
                        "high_amount": 260,
                        "currency": "GBP",
                        "source": "provider_price",
                    }
                ],
                "caveat": "Directional estimate only.",
            },
            "conversation": {
                "planning_mode": "quick",
                "quick_plan_finalization": {
                    "accepted": True,
                    "review_status": "complete",
                    "quality_status": "pass",
                    "brochure_eligible": True,
                    "accepted_modules": ["flights", "weather", "activities", "hotels"],
                    "assumptions": [
                        {"label": "Working dates", "value": "1-3 May 2027"}
                    ],
                    "blocked_reasons": [],
                    "review_result": {"status": "complete"},
                    "quality_result": {"status": "pass"},
                    "intelligence_summary": {
                        "plan_rationale": "Calm Paris food and culture route.",
                        "excluded_modules": [],
                        "provider_confidence_notes": [
                            "Flight anchors are provider-backed.",
                            "Stay anchor is provider-backed.",
                        ],
                    },
                },
            },
        }
    )

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_paris"),
        draft=draft,
        version_number=1,
    )

    assert payload.planning_mode == "quick"
    assert payload.quick_plan_module_scope == ["flights", "weather", "activities", "hotels"]
    assert payload.quick_plan_review_status == "complete"
    assert payload.quick_plan_quality_status == "pass"
    assert payload.quick_plan_intelligence_summary["plan_rationale"] == (
        "Calm Paris food and culture route."
    )
    assert "Flight anchors are provider-backed." in payload.quick_plan_provider_confidence_notes
    assert len(payload.flights) == 2
    assert payload.stays[0].hotel_name == "Left Bank Stay"
    assert payload.budget_estimate is not None
    assert payload.budget_summary.headline == "Estimated trip range"
    assert not any("Flight timing is not fully locked" in warning.title for warning in payload.warnings)
    assert not any("Hotel selection is still open" in warning.title for warning in payload.warnings)
    assert any("Working dates" in note for note in payload.planning_notes)
    assert any("planning snapshots" in note for note in payload.planning_notes)


def test_activities_only_quick_plan_brochure_notes_excluded_modules() -> None:
    draft = TripDraft.model_validate(
        {
            "trip_id": "trip_lisbon",
            "thread_id": "thread_lisbon",
            "title": "Lisbon activities quick plan",
            "configuration": {
                "to_location": "Lisbon",
                "selected_modules": {
                    "flights": False,
                    "weather": False,
                    "activities": True,
                    "hotels": False,
                },
            },
            "timeline": [
                {
                    "id": "activity_1",
                    "type": "activity",
                    "title": "Alfama walk",
                    "start_at": "2027-04-01T10:00:00Z",
                    "end_at": "2027-04-01T12:00:00Z",
                    "source_module": "activities",
                }
            ],
            "module_outputs": {
                "activities": [
                    {
                        "id": "activity_1",
                        "title": "Alfama walk",
                    }
                ]
            },
            "conversation": {
                "planning_mode": "quick",
                "quick_plan_finalization": {
                    "accepted": True,
                    "review_status": "complete",
                    "quality_status": "pass",
                    "brochure_eligible": True,
                    "accepted_modules": ["activities"],
                    "assumptions": [],
                    "blocked_reasons": [],
                    "review_result": {"status": "complete"},
                    "quality_result": {"status": "pass"},
                    "intelligence_summary": {
                        "plan_rationale": "Lisbon activities were accepted as the requested scope.",
                        "excluded_modules": [
                            {"module": "flights", "reason": "Excluded by request"},
                            {"module": "hotels", "reason": "Excluded by request"},
                        ],
                        "provider_confidence_notes": [
                            "Activity ideas are grounded in accepted module outputs."
                        ],
                    },
                },
            },
        }
    )

    payload = build_brochure_snapshot_payload(
        trip=SimpleNamespace(id="trip_lisbon"),
        draft=draft,
        version_number=1,
    )

    assert any("Flights were excluded" in note for note in payload.planning_notes)
    assert any("Stays were excluded" in note for note in payload.planning_notes)
    assert payload.quick_plan_excluded_modules[0]["module"] == "flights"
    assert not any(warning.id == "warning_flights_pending" for warning in payload.warnings)
    assert not any(warning.id == "warning_hotel_pending" for warning in payload.warnings)


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
