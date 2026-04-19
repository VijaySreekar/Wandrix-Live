from app.core.config import get_settings
from app.integrations.geoapify.client import create_geoapify_client
from app.schemas.trip_planning import ActivityDetail, TripConfiguration
from app.services.providers.location_lookup import (
    Coordinates,
    resolve_destination_coordinates,
)


STYLE_CATEGORY_MAP = {
    "culture": ["entertainment.culture", "tourism.sights"],
    "food": ["catering.restaurant", "catering.cafe"],
    "relaxed": ["leisure.park", "tourism.sights"],
    "outdoors": ["leisure.park", "natural"],
    "adventure": ["sport", "leisure.park"],
    "family": ["leisure.playground", "entertainment"],
    "nightlife": ["entertainment", "catering.bar"],
    "romantic": ["tourism.sights", "leisure.park"],
    "luxury": ["accommodation", "catering.restaurant"],
}


def enrich_activities_from_geoapify(
    configuration: TripConfiguration,
    coordinates: Coordinates | None = None,
) -> list[ActivityDetail]:
    if not _can_search_activities(configuration):
        return []

    latitude, longitude = coordinates or resolve_destination_coordinates(
        configuration.to_location or "",
    )
    if latitude is None or longitude is None:
        return []

    category_values = _derive_categories(configuration)
    with create_geoapify_client() as client:
        response = client.get(
            "/places",
            params={
                "categories": ",".join(category_values),
                "filter": f"circle:{longitude},{latitude},5000",
                "bias": f"proximity:{longitude},{latitude}",
                "limit": 6,
                "lang": "en",
                "apiKey": get_settings().geoapify_api_key,
            },
        )
        response.raise_for_status()
        payload = response.json()

    features = payload.get("features") or []
    if not features:
        return []

    activity_items: list[ActivityDetail] = []
    used_titles: set[str] = set()

    for index, feature in enumerate(features, start=1):
        properties = feature.get("properties") or {}
        categories = properties.get("categories") or []
        category_label = categories[0] if isinstance(categories, list) and categories else None
        fallback_title = _fallback_title(category_label, configuration.to_location, index)
        title = (
            properties.get("name")
            or properties.get("formatted")
            or properties.get("address_line2")
            or fallback_title
        )
        if not isinstance(title, str):
            continue

        normalized_title = title.strip().lower()
        if normalized_title in used_titles:
            continue
        used_titles.add(normalized_title)

        address_line = properties.get("address_line2") or properties.get("formatted")
        distance = properties.get("distance")
        notes = []

        if isinstance(address_line, str):
            notes.append(address_line)
        if isinstance(distance, (int, float)):
            notes.append(f"Approx {int(distance)}m from the searched destination center.")

        activity_items.append(
            ActivityDetail(
                id=f"geoapify_activity_{index}",
                title=title.strip(),
                category=category_label if isinstance(category_label, str) else None,
                day_label=f"Day {min(index, 3)}",
                time_label=_time_label_for_index(index),
                notes=notes,
            )
        )

        if len(activity_items) >= 4:
            break

    return activity_items
def _derive_categories(configuration: TripConfiguration) -> list[str]:
    categories: list[str] = []
    for style in configuration.activity_styles:
        categories.extend(STYLE_CATEGORY_MAP.get(style, []))

    if not categories:
        categories = ["tourism.sights", "entertainment.culture", "catering.restaurant"]

    deduped: list[str] = []
    seen: set[str] = set()
    for category in categories:
        if category in seen:
            continue
        seen.add(category)
        deduped.append(category)

    return deduped


def _can_search_activities(configuration: TripConfiguration) -> bool:
    return bool(configuration.selected_modules.activities and configuration.to_location)


def _time_label_for_index(index: int) -> str:
    labels = {
        1: "Morning",
        2: "Afternoon",
        3: "Evening",
        4: "Flexible",
    }
    return labels.get(index, "Flexible")


def _fallback_title(category_label: str | None, location_name: str | None, index: int) -> str:
    location_suffix = f" in {location_name}" if location_name else ""
    if isinstance(category_label, str) and category_label:
        category_name = category_label.split(".")[-1].replace("_", " ").title()
        return f"{category_name}{location_suffix}"

    return f"Local activity {index}{location_suffix}"
