from datetime import date, datetime, timezone

from app.graph.planner import provider_enrichment
from app.graph.planner import quick_plan_enrichment
from app.graph.planner.turn_models import ProposedTimelineItem
from app.schemas.trip_planning import (
    ActivityDetail,
    FlightDetail,
    HotelStayDetail,
    TripConfiguration,
    TripModuleOutputs,
    WeatherDetail,
)


def test_hotel_outputs_refresh_when_existing_cache_is_empty(monkeypatch) -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="Next month",
        trip_length="5 days",
    )

    monkeypatch.setattr(
        provider_enrichment,
        "enrich_hotels",
        lambda config: [
            HotelStayDetail(
                id="live_hotel_1",
                hotel_name="Kyoto Food Base Hotel",
                area="Gion",
                notes=["Live hotel result."],
            )
        ],
    )

    outputs = provider_enrichment.build_module_outputs(
        configuration=configuration,
        previous_configuration=configuration.model_copy(deep=True),
        existing_module_outputs=TripModuleOutputs(),
        allowed_modules={"hotels"},
    )

    assert [hotel.hotel_name for hotel in outputs.hotels] == ["Kyoto Food Base Hotel"]


def test_activity_outputs_refresh_when_existing_cache_is_empty(monkeypatch) -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="Next month",
        trip_length="5 days",
        activity_styles=["food"],
    )

    monkeypatch.setattr(
        provider_enrichment,
        "enrich_activities_from_geoapify",
        lambda config, coords: [
            ActivityDetail(
                id="activity_1",
                title="Nishiki Market walk",
                notes=["Live activity result."],
                day_label="Day 1",
            )
        ],
    )

    outputs = provider_enrichment.build_module_outputs(
        configuration=configuration,
        previous_configuration=configuration.model_copy(deep=True),
        existing_module_outputs=TripModuleOutputs(),
        allowed_modules={"activities"},
    )

    assert [activity.title for activity in outputs.activities] == ["Nishiki Market walk"]


def test_hotel_outputs_refresh_when_cached_results_are_missing_rich_fields(
    monkeypatch,
) -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        travel_window="Late March",
        trip_length="5 nights",
    )

    monkeypatch.setattr(
        provider_enrichment,
        "enrich_hotels",
        lambda config: [
            HotelStayDetail(
                id="live_hotel_1",
                hotel_name="Cross Hotel Kyoto",
                area="Nakagyo Ward",
                image_url="https://dynamic-media-cdn.tripadvisor.com/media/photo-o/test.jpg",
                notes=["Refreshed live hotel result."],
            )
        ],
    )

    stale_outputs = TripModuleOutputs(
        hotels=[
            HotelStayDetail(
                id="cached_hotel_1",
                hotel_name="Cross Hotel Kyoto",
                area="Nakagyo Ward",
                notes=["Old cached hotel result without imagery."],
            )
        ]
    )

    outputs = provider_enrichment.build_module_outputs(
        configuration=configuration,
        previous_configuration=configuration.model_copy(deep=True),
        existing_module_outputs=stale_outputs,
        allowed_modules={"hotels"},
    )

    assert outputs.hotels[0].id == "live_hotel_1"
    assert outputs.hotels[0].image_url is not None


def test_hotel_outputs_refresh_when_cached_results_are_too_shallow(
    monkeypatch,
) -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date="2027-03-22",
        end_date="2027-03-27",
    )

    monkeypatch.setattr(
        provider_enrichment,
        "enrich_hotels",
        lambda config: [
            HotelStayDetail(
                id=f"live_hotel_{index}",
                hotel_name=f"Kyoto Hotel {index}",
                area="Nakagyo-ku",
                image_url=f"https://example.com/hotel-{index}.jpg",
                nightly_rate_amount=120 + index,
                nightly_rate_currency="GBP",
                notes=["Refreshed live hotel result."],
            )
            for index in range(1, 7)
        ],
    )

    stale_outputs = TripModuleOutputs(
        hotels=[
            HotelStayDetail(
                id=f"cached_hotel_{index}",
                hotel_name=f"Cached Kyoto Hotel {index}",
                area="Nakagyo-ku",
                image_url=f"https://example.com/cached-{index}.jpg",
                nightly_rate_amount=90 + index,
                nightly_rate_currency="GBP",
                notes=["Old cached shortlist."],
            )
            for index in range(1, 5)
        ]
    )

    outputs = provider_enrichment.build_module_outputs(
        configuration=configuration,
        previous_configuration=configuration.model_copy(deep=True),
        existing_module_outputs=stale_outputs,
        allowed_modules={"hotels"},
    )

    assert len(outputs.hotels) == 6
    assert outputs.hotels[0].id == "live_hotel_1"


def test_quick_plan_enrichment_uses_bounded_provider_profile(monkeypatch) -> None:
    captured: dict = {}

    def _fake_build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        *,
        allowed_modules,
        options,
    ):
        del configuration, previous_configuration, existing_module_outputs
        captured["allowed_modules"] = allowed_modules
        captured["options"] = options
        return TripModuleOutputs()

    monkeypatch.setattr(
        quick_plan_enrichment,
        "build_module_outputs",
        _fake_build_module_outputs,
    )

    quick_plan_enrichment.build_quick_plan_module_outputs(
        configuration=TripConfiguration(
            to_location="Valencia",
            travel_window="late September",
        ),
        previous_configuration=TripConfiguration(),
        existing_module_outputs=TripModuleOutputs(),
        allowed_modules={"flights", "hotels", "activities", "weather"},
    )

    options = captured["options"]
    assert captured["allowed_modules"] == {"flights", "hotels", "activities", "weather"}
    assert options.parallel is True
    assert options.request_timeout_seconds == 3.0
    assert options.flight_allow_live_fallback is False
    assert options.flight_parameter_sets_limit == 1
    assert options.hotel_result_limit == 6
    assert options.hotel_rate_lookup_limit == 0
    assert options.hotel_include_llm_fallback is False
    assert options.activity_category_limit == 1


def test_timeline_anchors_return_flight_to_final_trip_day() -> None:
    configuration = TripConfiguration(
        from_location="Coventry",
        to_location="Valencia",
        start_date=date(2026, 9, 22),
        end_date=date(2026, 9, 26),
    )
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="cached_return",
                direction="return",
                carrier="WY",
                departure_airport="VLC",
                arrival_airport="BHX",
                departure_time=datetime(2026, 9, 22, 8, 10, tzinfo=timezone.utc),
                price_text="GBP 795",
                stop_count=2,
                stop_details_available=False,
                layover_summary="2 stops; connection airports are not supplied yet.",
                inventory_source="cached",
            )
        ]
    )

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=[],
        module_outputs=module_outputs,
    )

    assert timeline[0].title == "Return flight option"
    assert timeline[0].day_label == "Day 5"
    assert timeline[0].start_at is not None
    assert timeline[0].start_at.date() == date(2026, 9, 26)
    assert all("cached inventory" not in detail.lower() for detail in timeline[0].details)


def test_timeline_keeps_provider_source_notes_out_of_hotel_details() -> None:
    configuration = TripConfiguration(
        to_location="Valencia",
        start_date=date(2026, 9, 22),
        end_date=date(2026, 9, 26),
    )
    module_outputs = TripModuleOutputs(
        hotels=[
            HotelStayDetail(
                id="hotel_1",
                hotel_name="Devesa Gardens Valencia",
                area="Valencian Community",
                check_in=datetime(2026, 9, 22, 16, 0, tzinfo=timezone.utc),
                check_out=datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc),
                notes=[
                    "TripAdvisor: https://www.tripadvisor.com/example",
                    "Cached hotel search result from Xotelo via RapidAPI.",
                    "Useful for a conference base with a quieter edge.",
                ],
            )
        ]
    )

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=[],
        module_outputs=module_outputs,
    )

    assert timeline[0].type == "hotel"
    assert timeline[0].summary == "Stay anchor"
    assert timeline[0].end_at == datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    assert timeline[0].details == ["Useful for a conference base with a quieter edge."]


def test_weather_outputs_do_not_become_standalone_itinerary_rows() -> None:
    configuration = TripConfiguration(
        to_location="Kyoto",
        start_date=date(2026, 4, 26),
        end_date=date(2026, 4, 29),
    )
    module_outputs = TripModuleOutputs(
        weather=[
            WeatherDetail(
                id="weather_day_1",
                day_label="Day 1",
                forecast_date=date(2026, 4, 26),
                summary="Light rain possible.",
                notes=["Location: Kyoto"],
            ),
            WeatherDetail(
                id="weather_day_2",
                day_label="Day 2",
                forecast_date=date(2026, 4, 27),
                summary="Heavy rain risk in the forecast.",
                notes=["Location: Kyoto"],
            ),
        ]
    )

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=[],
        module_outputs=module_outputs,
    )

    assert timeline == []


def test_unbacked_quick_plan_flight_preview_becomes_travel_note() -> None:
    configuration = TripConfiguration(
        from_location="Coventry",
        to_location="Valencia",
        start_date=date(2026, 9, 22),
        end_date=date(2026, 9, 26),
    )
    preview = [
        ProposedTimelineItem(
            type="flight",
            title="Outbound travel: Coventry to Valencia via your selected connection",
            day_label="Day 1",
            location_label="Coventry to Valencia",
            details=["Keep this strategic until flights are selected."],
        )
    ]

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=preview,
        module_outputs=TripModuleOutputs(),
    )

    assert timeline[0].type == "transfer"
    assert "Flight option still needs selection" in timeline[0].details[-1]


def test_quick_plan_authoritative_preview_can_include_logistics_anchors() -> None:
    configuration = TripConfiguration(
        from_location="London",
        to_location="Lisbon",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 21),
    )
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="flight_outbound",
                direction="outbound",
                carrier="TAP",
                flight_number="TP1351",
                departure_airport="LHR",
                arrival_airport="LIS",
                departure_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 18, 10, 45, tzinfo=timezone.utc),
                duration_text="2h 45m",
                notes=["Direct morning flight."],
            ),
            FlightDetail(
                id="flight_return",
                direction="return",
                carrier="TAP",
                flight_number="TP1358",
                departure_airport="LIS",
                arrival_airport="LHR",
                departure_time=datetime(2026, 9, 18, 17, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 18, 19, 40, tzinfo=timezone.utc),
                duration_text="2h 40m",
                notes=["Evening return flight."],
            ),
        ],
        hotels=[
            HotelStayDetail(
                id="hotel_lisbon",
                hotel_name="Baixa Story Hotel",
                area="Baixa",
                notes=["Central base for the accepted plan."],
            )
        ],
    )

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=[
            ProposedTimelineItem(
                type="activity",
                title="Sunset walk through Alfama",
                day_label="Day 1",
                start_at=datetime(2026, 9, 18, 18, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc),
                timing_source="planner_estimate",
            )
        ],
        module_outputs=module_outputs,
        include_derived_when_preview_present=False,
        include_derived_modules_when_preview_present={"flights", "hotels"},
    )

    titles = [item.title for item in timeline]
    stay = next(item for item in timeline if item.source_module == "hotels")

    assert "Outbound flight option" in titles
    assert "Return flight option" in titles
    assert "Baixa Story Hotel" in titles
    assert "Sunset walk through Alfama" in titles
    assert stay.start_at == datetime(2026, 9, 18, 15, 30, tzinfo=timezone.utc)
    assert stay.end_at == datetime(2026, 9, 21, 11, 0, tzinfo=timezone.utc)
    assert stay.timing_source == "planner_estimate"


def test_quick_plan_logistics_anchor_merge_does_not_duplicate_preview_anchor() -> None:
    configuration = TripConfiguration(
        from_location="London",
        to_location="Lisbon",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 21),
    )
    module_outputs = TripModuleOutputs(
        flights=[
            FlightDetail(
                id="flight_outbound",
                direction="outbound",
                carrier="TAP",
                departure_airport="LHR",
                arrival_airport="LIS",
                departure_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 9, 18, 10, 45, tzinfo=timezone.utc),
                notes=[],
            )
        ]
    )

    timeline = provider_enrichment.build_timeline(
        configuration=configuration,
        llm_preview=[
            ProposedTimelineItem(
                type="flight",
                title="Outbound TAP flight to Lisbon",
                day_label="Day 1",
                start_at=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 18, 10, 45, tzinfo=timezone.utc),
                timing_source="provider_exact",
                source_module="flights",
            )
        ],
        module_outputs=module_outputs,
        include_derived_when_preview_present=False,
        include_derived_modules_when_preview_present={"flights", "hotels"},
    )

    assert [item.type for item in timeline].count("flight") == 1
    assert timeline[0].title == "Outbound TAP flight to Lisbon"
