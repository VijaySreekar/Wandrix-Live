from app.core.config import get_settings
from app.integrations.geoapify.client import create_geoapify_client
from app.schemas.trip_planning import ActivityDetail, TripConfiguration
from app.services.providers.location_lookup import (
    Coordinates,
    resolve_destination_coordinates,
)


STYLE_CATEGORY_MAP = {
    "culture": ["entertainment.culture", "tourism.sights"],
    "food": ["commercial.marketplace", "catering.restaurant", "catering.cafe"],
    "relaxed": ["leisure.park", "tourism.sights"],
    "outdoors": ["leisure.park", "natural"],
    "adventure": ["sport", "leisure.park"],
    "family": ["leisure.playground", "entertainment"],
    "nightlife": ["entertainment", "catering.bar"],
    "romantic": ["tourism.sights", "leisure.park"],
    "luxury": ["accommodation", "catering.restaurant"],
}

MAX_ACTIVITY_RESULTS = 6
PER_CATEGORY_LIMIT = 8

ANCHOR_KEYWORDS = {
    "market",
    "museum",
    "gallery",
    "shrine",
    "temple",
    "garden",
    "palace",
    "castle",
    "walk",
    "food hall",
    "food alley",
    "tasting",
    "tea",
    "teahouse",
    "sake",
    "brewery",
    "izakaya",
    "bar",
    "jazz",
    "night",
    "festival",
    "show",
    "performance",
}

GENERIC_CHAIN_TOKENS = {
    "saizeriya",
    "starbucks",
    "mcdonald",
    "burger king",
    "subway",
    "kfc",
    "domino",
    "pizza hut",
    "doutor",
    "komeda",
    "tully",
    "yoshinoya",
    "sukiya",
    "matsuya",
    "yang guo fu",
    "maratang",
}

GENERIC_LOCATION_TERMS = {
    "ward",
    "street",
    "st",
    "st.",
    "road",
    "rd",
    "rd.",
    "avenue",
    "ave",
    "ave.",
    "dori",
    "ku",
}

CATEGORY_EDITORIAL_LABELS = {
    "commercial.marketplace": "Food market with plenty to browse and taste.",
    "catering.restaurant": "Food-led stop that can carry part of the day well.",
    "catering.cafe": "Cafe stop that works well as a lighter pause.",
    "catering.bar": "Evening spot with more atmosphere than a generic dinner stop.",
    "entertainment.culture": "Culture-led stop with enough substance to shape part of the day.",
    "tourism.sights": "Classic sight worth building part of the day around.",
    "leisure.park": "Slower outdoor stop when the trip needs breathing room.",
    "natural": "Outdoor stop that helps the trip open up a bit.",
}

TIME_EDITORIAL_LABELS = {
    "Morning": "Best earlier in the day.",
    "Afternoon": "Easy to place in the middle of the day.",
    "Evening": "Best once the day turns toward dinner and wandering.",
    "Flexible": "Flexible enough to place where the day needs it most.",
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

    features: list[dict] = []
    category_values = _derive_categories(configuration)
    with create_geoapify_client() as client:
        for category_value in category_values:
            response = client.get(
                "/places",
                params={
                    "categories": category_value,
                    "filter": f"circle:{longitude},{latitude},5000",
                    "bias": f"proximity:{longitude},{latitude}",
                    "limit": PER_CATEGORY_LIMIT,
                    "lang": "en",
                    "apiKey": get_settings().geoapify_api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()
            features.extend(payload.get("features") or [])

    if not features:
        return []

    activity_items: list[ActivityDetail] = []
    used_titles: set[str] = set()
    used_locations: set[tuple[float, float]] = set()

    for index, feature in enumerate(features, start=1):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        geometry_coordinates = geometry.get("coordinates") or []
        categories = properties.get("categories") or []
        category_label = _select_preferred_category(categories)
        raw_name = properties.get("name")
        title = _select_display_title(
            raw_name=raw_name if isinstance(raw_name, str) else None,
            category_label=category_label if isinstance(category_label, str) else None,
            properties=properties,
            location_name=configuration.to_location,
            index=index,
        )
        if not title:
            continue

        if _should_skip_feature(
            title=title,
            raw_name=raw_name if isinstance(raw_name, str) else None,
            category_label=category_label if isinstance(category_label, str) else None,
            properties=properties,
        ):
            continue

        normalized_title = title.strip().lower()
        if normalized_title in used_titles:
            continue

        latitude = geometry_coordinates[1] if len(geometry_coordinates) > 1 else None
        longitude = geometry_coordinates[0] if len(geometry_coordinates) > 1 else None
        location_key = None
        if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)):
            location_key = (round(float(latitude), 4), round(float(longitude), 4))
            if location_key in used_locations:
                continue

        used_titles.add(normalized_title)
        if location_key is not None:
            used_locations.add(location_key)

        address_line = _build_location_label(properties)
        distance = properties.get("distance")
        notes = []
        venue_name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None

        if isinstance(address_line, str):
            notes.append(address_line)
        if venue_name and venue_name != title and not _looks_english_forward(venue_name):
            notes.append(f"Local name: {venue_name}")
        if isinstance(distance, (int, float)):
            notes.append(f"Approx {int(distance)}m from the searched destination center.")

        activity_items.append(
            ActivityDetail(
                id=f"geoapify_activity_{index}",
                title=title.strip(),
                category=category_label if isinstance(category_label, str) else None,
                latitude=float(latitude) if isinstance(latitude, (int, float)) else None,
                longitude=float(longitude) if isinstance(longitude, (int, float)) else None,
                venue_name=venue_name if venue_name and venue_name != title else None,
                location_label=address_line if isinstance(address_line, str) else None,
                source_label="Geoapify",
                estimated_duration_minutes=_estimated_duration_minutes(
                    category_label if isinstance(category_label, str) else None,
                    index,
                ),
                day_label=f"Day {min(index, 3)}",
                time_label=_time_label_for_index(index),
                notes=notes,
            )
        )

        if len(activity_items) >= MAX_ACTIVITY_RESULTS:
            break

    return activity_items


def _derive_categories(configuration: TripConfiguration) -> list[str]:
    categories: list[str] = []
    for style in configuration.activity_styles:
        categories.extend(STYLE_CATEGORY_MAP.get(style, []))

    if not categories:
        categories = [
            "tourism.sights",
            "entertainment.culture",
            "commercial.marketplace",
            "catering.restaurant",
        ]

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
        lowered = category_label.lower()
        if "commercial.marketplace" in lowered:
            return f"Market tasting walk{location_suffix}"
        if "catering.bar" in lowered:
            return f"Evening drinks stop{location_suffix}"
        if "catering" in lowered:
            return f"Food stop{location_suffix}"
        if "museum" in lowered or "gallery" in lowered:
            return f"Museum stop{location_suffix}"
        if "entertainment.culture" in lowered:
            return f"Cultural stop{location_suffix}"
        if "tourism.sights" in lowered:
            return f"Sightseeing walk{location_suffix}"
        if "leisure.park" in lowered:
            return f"Park stop{location_suffix}"
        category_name = category_label.split(".")[-1].replace("_", " ").title()
        return f"{category_name}{location_suffix}"

    return f"Local activity {index}{location_suffix}"


def _estimated_duration_minutes(category_label: str | None, index: int) -> int:
    if isinstance(category_label, str):
        lowered = category_label.lower()
        if "commercial.marketplace" in lowered:
            return 120
        if any(token in lowered for token in ["catering.restaurant", "catering.cafe"]):
            return 90
        if any(token in lowered for token in ["entertainment.culture", "museum", "gallery"]):
            return 120
        if any(token in lowered for token in ["leisure.park", "natural", "tourism.sights"]):
            return 75
    return 60 if index >= 4 else 90


def _select_display_title(
    raw_name: str | None,
    category_label: str | None,
    properties: dict,
    location_name: str | None,
    index: int,
) -> str | None:
    cleaned_name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None
    if cleaned_name and _looks_english_forward(cleaned_name):
        return cleaned_name

    english_label = _extract_english_label(properties)
    if english_label:
        return english_label

    focus_label = _extract_focus_location(properties) or location_name
    return _fallback_title(category_label, focus_label, index)


def _should_skip_feature(
    title: str,
    raw_name: str | None,
    category_label: str | None,
    properties: dict,
) -> bool:
    if not isinstance(category_label, str) or not category_label:
        return False

    lowered_category = category_label.lower()
    if not any(token in lowered_category for token in ["catering", "accommodation"]):
        return False

    signal_text = " ".join(
        value
        for value in [
            title,
            raw_name,
            properties.get("name"),
            properties.get("address_line2"),
            properties.get("formatted"),
        ]
        if isinstance(value, str)
    ).lower()

    if any(token in signal_text for token in GENERIC_CHAIN_TOKENS):
        return True

    if any(keyword in signal_text for keyword in ANCHOR_KEYWORDS):
        return False

    return True


def _extract_english_label(properties: dict) -> str | None:
    raw_name = properties.get("name")
    if isinstance(raw_name, str) and raw_name.strip():
        raw_name = raw_name.strip()
        if _looks_english_forward(raw_name):
            return raw_name

    for field_name in ("address_line2", "formatted"):
        value = properties.get(field_name)
        if not isinstance(value, str):
            continue
        candidate = _best_title_fragment(value)
        if candidate:
            return candidate

    return None


def _best_title_fragment(value: str) -> str | None:
    if not isinstance(value, str):
        return None

    fragments = [fragment.strip() for fragment in value.split(",") if fragment.strip()]
    for fragment in fragments[:2]:
        if not _looks_english_forward(fragment):
            continue
        if any(character.isdigit() for character in fragment):
            continue
        if len(fragment.split()) > 5:
            continue
        if _is_generic_location_fragment(fragment):
            continue
        return fragment

    return None


def _extract_focus_location(properties: dict) -> str | None:
    for field_name in ("suburb", "neighbourhood", "city_district", "district", "city"):
        value = properties.get(field_name)
        if isinstance(value, str) and value.strip() and _looks_english_forward(value):
            return value.strip()

    address_line = properties.get("address_line2") or properties.get("formatted")
    if isinstance(address_line, str):
        fragments = [fragment.strip() for fragment in address_line.split(",") if fragment.strip()]
        for fragment in fragments:
            if (
                _looks_english_forward(fragment)
                and not any(character.isdigit() for character in fragment)
                and len(fragment.split()) <= 4
            ):
                return fragment

    return None


def _build_location_label(properties: dict) -> str | None:
    address_line = properties.get("address_line2") or properties.get("formatted")
    fragments = []
    if isinstance(address_line, str):
        fragments = [fragment.strip() for fragment in address_line.split(",") if fragment.strip()]

    cleaned_fragments: list[str] = []
    for fragment in fragments:
        if not _looks_english_forward(fragment):
            continue
        if any(character.isdigit() for character in fragment):
            continue
        lowered = fragment.lower()
        if any(keyword in lowered for keyword in (*ANCHOR_KEYWORDS, "alley", "street", "dori", "house")):
            continue
        if fragment not in cleaned_fragments:
            cleaned_fragments.append(fragment)

    if cleaned_fragments:
        return ", ".join(cleaned_fragments[:2])

    address_line = properties.get("address_line2") or properties.get("formatted")
    if isinstance(address_line, str) and address_line.strip():
        return address_line.strip()

    pieces = []
    for field_name in ("suburb", "city_district", "city", "country"):
        value = properties.get(field_name)
        if isinstance(value, str) and value.strip():
            pieces.append(value.strip())
    return ", ".join(pieces) or None


def _build_editorial_activity_summary(
    *,
    title: str,
    category_label: str | None,
    time_label: str | None,
    venue_name: str | None,
) -> str:
    summary_parts = [
        _editorial_category_summary(category_label, title),
        TIME_EDITORIAL_LABELS.get(time_label or "", "Flexible enough to place where the day needs it most."),
    ]

    if (
        venue_name
        and venue_name.strip()
        and venue_name.strip() != title
        and not _looks_english_forward(venue_name)
    ):
        summary_parts.append(f"Known locally as {venue_name.strip()}.")

    return " ".join(part for part in summary_parts if part).strip()


def _editorial_category_summary(category_label: str | None, title: str) -> str:
    lowered_title = title.lower()
    if "market" in lowered_title:
        return "Food market with plenty to browse and taste."
    if any(token in lowered_title for token in ["alley", "izakaya", "bar", "jazz", "night"]):
        return "Strong evening-facing pick with more atmosphere than a generic stop."
    if any(token in lowered_title for token in ["museum", "gallery"]):
        return "Culture-led stop with enough substance to shape part of the day."
    if any(token in lowered_title for token in ["shrine", "temple", "garden", "palace", "castle"]):
        return "Classic sight worth building part of the day around."

    if category_label:
        lowered_category = category_label.lower()
        for key, value in CATEGORY_EDITORIAL_LABELS.items():
            if key in lowered_category:
                return value

    return "Solid trip pick that can help give the day a clearer center."


def _looks_english_forward(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False

    latin_characters = sum(
        1
        for character in stripped
        if character.isascii() and (character.isalpha() or character.isdigit() or character in {" ", "-", "&", "'"})
    )
    visible_characters = sum(1 for character in stripped if not character.isspace())
    if visible_characters == 0:
        return False

    return latin_characters / visible_characters >= 0.65


def _select_preferred_category(categories: object) -> str | None:
    if not isinstance(categories, list) or not categories:
        return None

    string_categories = [category for category in categories if isinstance(category, str) and category]
    if not string_categories:
        return None

    return max(string_categories, key=_category_priority)


def _category_priority(category: str) -> int:
    lowered = category.lower()
    if "commercial.marketplace" in lowered:
        return 100
    if "museum" in lowered or "gallery" in lowered:
        return 95
    if "entertainment.culture" in lowered:
        return 90
    if "tourism.sights" in lowered:
        return 85
    if "catering.bar" in lowered:
        return 75
    if "catering.restaurant" in lowered:
        return 65
    if "catering.cafe" in lowered:
        return 60
    if lowered == "catering":
        return 55
    if "leisure.park" in lowered or "natural" in lowered:
        return 45
    if lowered == "building":
        return 5
    return 20


def _is_generic_location_fragment(fragment: str) -> bool:
    lowered = fragment.lower().strip()
    if not lowered:
        return True
    if any(keyword in lowered for keyword in ANCHOR_KEYWORDS):
        return False

    tokens = [token.strip(" .,'") for token in lowered.replace("-", " ").split() if token.strip(" .,'")]
    if not tokens:
        return True

    return any(token in GENERIC_LOCATION_TERMS for token in tokens)
