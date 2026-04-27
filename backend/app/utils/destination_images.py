from functools import lru_cache
from urllib.parse import quote, urlparse

import httpx


GENERIC_DESTINATION_IMAGE = (
    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1600&q=80"
)
GENERIC_ISLAND_IMAGE = (
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80"
)
GENERIC_DESTINATION_IMAGE_MARKERS = {
    "photo-1488646953014-85cb44e25828",
    "photo-1449824913935-59a10b8d2000",
    "photo-1507525428034-b723cf961d3e",
}
TRUSTED_DESTINATION_IMAGE_HOSTS = {
    "upload.wikimedia.org",
}
UNSTABLE_DESTINATION_IMAGE_HOSTS = {
    "source.unsplash.com",
}
NON_DESTINATION_IMAGE_MARKERS = {
    "special_marker",
    "location_map",
    "locator_map",
    "map_of_",
    "_map.",
    "flag_of_",
    ".svg",
    "coat_of_arms",
    "seal_of_",
    "emblem",
    "logo",
}
WIKIPEDIA_REST_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Wandrix/0.1 (https://wandrix.app; destination-image-resolver)",
}
WIKIPEDIA_TIMEOUT_SECONDS = 2.5


def get_destination_card_image(
    destination_name: str | None,
    *,
    country_or_region: str | None = None,
    provided_image_url: str | None = None,
) -> str:
    wikimedia_image = _resolve_wikimedia_destination_image(
        destination_name=destination_name,
        country_or_region=country_or_region,
    )
    if wikimedia_image:
        return wikimedia_image

    normalized_provided = normalize_destination_image_url(provided_image_url)
    if normalized_provided:
        return normalized_provided

    return get_destination_hero_image(destination_name)


def get_destination_hero_image(destination_name: str | None) -> str:
    normalized = (destination_name or "").strip().lower()
    if not normalized:
        return GENERIC_DESTINATION_IMAGE

    if "island" in normalized:
        return GENERIC_ISLAND_IMAGE

    return GENERIC_DESTINATION_IMAGE


def normalize_destination_image_url(image_url: str | None) -> str | None:
    trimmed = (image_url or "").strip()
    if not trimmed:
        return None

    parsed = urlparse(trimmed)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname:
        return None
    if hostname in UNSTABLE_DESTINATION_IMAGE_HOSTS:
        return None
    if hostname not in TRUSTED_DESTINATION_IMAGE_HOSTS:
        return None
    lowered_url = trimmed.lower()
    if any(marker in lowered_url for marker in GENERIC_DESTINATION_IMAGE_MARKERS):
        return None
    if any(marker in lowered_url for marker in NON_DESTINATION_IMAGE_MARKERS):
        return None

    return trimmed


@lru_cache(maxsize=512)
def _resolve_wikimedia_destination_image(
    *,
    destination_name: str | None,
    country_or_region: str | None,
) -> str | None:
    for title in _build_wikipedia_title_candidates(
        destination_name,
        country_or_region=country_or_region,
    ):
        image_url = _fetch_wikipedia_summary_image(title)
        normalized = normalize_destination_image_url(image_url)
        if normalized:
            return normalized

    return None


def _build_wikipedia_title_candidates(
    destination_name: str | None,
    *,
    country_or_region: str | None,
) -> list[str]:
    destination = (destination_name or "").strip()
    country = (country_or_region or "").strip()
    candidates: list[str] = []

    destination_variants = _expand_destination_title_variants(destination)

    candidates.extend(destination_variants)
    if country:
        for variant in destination_variants:
            candidates.append(f"{variant}, {country}")
            candidates.append(f"{variant} {country}")
            candidates.extend(_search_wikipedia_titles(f"{variant} {country} travel"))
    for variant in destination_variants:
        candidates.extend(_search_wikipedia_titles(f"{variant} travel"))

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = _normalize_destination_key(candidate)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(candidate)

    return deduped


@lru_cache(maxsize=512)
def _search_wikipedia_titles(query: str) -> tuple[str, ...]:
    normalized_query = " ".join(query.strip().split())
    if not normalized_query:
        return ()

    try:
        response = httpx.get(
            WIKIPEDIA_SEARCH_URL,
            headers=WIKIPEDIA_HEADERS,
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": normalized_query,
                "srlimit": 5,
                "srnamespace": 0,
            },
            timeout=WIKIPEDIA_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return ()

    search_results = payload.get("query", {}).get("search", [])
    if not isinstance(search_results, list):
        return ()

    titles: list[str] = []
    for result in search_results:
        if not isinstance(result, dict):
            continue
        title = result.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())

    return tuple(titles)


def _fetch_wikipedia_summary_image(title: str) -> str | None:
    encoded_title = quote(title, safe="")
    try:
        response = httpx.get(
            f"{WIKIPEDIA_REST_SUMMARY_URL}/{encoded_title}",
            headers=WIKIPEDIA_HEADERS,
            timeout=WIKIPEDIA_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    if payload.get("type") == "disambiguation":
        return None

    original_image = payload.get("originalimage")
    if isinstance(original_image, dict):
        source = original_image.get("source")
        if isinstance(source, str):
            return source

    thumbnail = payload.get("thumbnail")
    if isinstance(thumbnail, dict):
        source = thumbnail.get("source")
        if isinstance(source, str):
            return source

    return None


def _expand_destination_title_variants(destination: str) -> list[str]:
    normalized = destination.strip()
    if not normalized:
        return []

    variants = [normalized]
    if "(" in normalized and ")" in normalized:
        before_parentheses, _, remainder = normalized.partition("(")
        inside_parentheses, _, _ = remainder.partition(")")
        for value in [before_parentheses.strip(), inside_parentheses.strip()]:
            if value:
                variants.append(value)

    return variants


def _normalize_destination_key(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())
