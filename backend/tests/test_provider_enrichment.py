from app.graph.planner import provider_enrichment
from app.schemas.trip_planning import ActivityDetail, HotelStayDetail, TripConfiguration, TripModuleOutputs


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
