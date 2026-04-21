from pydantic import BaseModel, Field

from app.schemas.conversation import PlannerLocationContext, PlannerProfileContext
from app.services.providers.location_lookup import reverse_geocode_coordinates


class ResolvedPlannerLocationContext(BaseModel):
    source: str = Field(..., min_length=1, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    summary: str | None = Field(default=None, max_length=240)
    latitude: float | None = None
    longitude: float | None = None
    message_context: str | None = Field(default=None, max_length=240)


def resolve_planner_location_context(
    *,
    current_location_context: dict,
    profile_context: dict,
) -> ResolvedPlannerLocationContext | None:
    current = (
        PlannerLocationContext.model_validate(current_location_context)
        if current_location_context
        else None
    )
    profile = (
        PlannerProfileContext.model_validate(profile_context)
        if profile_context
        else PlannerProfileContext()
    )

    if current and current.source == "browser_location":
        resolved = _resolve_browser_context(current)
        if resolved is not None:
            return resolved

    if profile.home_city or profile.home_country or profile.home_airport:
        return _resolve_profile_context(profile)

    return None


def _resolve_browser_context(
    current: PlannerLocationContext,
) -> ResolvedPlannerLocationContext | None:
    city = current.city
    region = current.region
    country = current.country
    summary = current.summary

    if (not city and not region and not country) and (
        current.latitude is not None and current.longitude is not None
    ):
        reverse_summary = reverse_geocode_coordinates(
            latitude=current.latitude,
            longitude=current.longitude,
        )
        city = reverse_summary.get("city")
        region = reverse_summary.get("region")
        country = reverse_summary.get("country")
        summary = reverse_summary.get("summary")

    if not any([city, region, country, summary]):
        return None

    readable_summary = summary or _build_human_summary(
        city=city,
        region=region,
        country=country,
    )
    return ResolvedPlannerLocationContext(
        source="browser_location",
        city=city,
        region=region,
        country=country,
        summary=readable_summary,
        latitude=current.latitude,
        longitude=current.longitude,
        message_context=f"Using your current location in {readable_summary}",
    )


def _resolve_profile_context(
    profile: PlannerProfileContext,
) -> ResolvedPlannerLocationContext:
    summary = (
        profile.location_summary
        or _build_human_summary(
            city=profile.home_city,
            country=profile.home_country,
        )
        or profile.home_airport
        or "your saved home base"
    )
    return ResolvedPlannerLocationContext(
        source="profile_home_base",
        city=profile.home_city,
        country=profile.home_country,
        summary=summary,
        message_context=(
            f"I couldn't use browser location, so I used your saved home base around {summary} "
            "as a starting point."
        ),
    )


def _build_human_summary(
    *,
    city: str | None = None,
    region: str | None = None,
    country: str | None = None,
) -> str | None:
    parts = [part for part in [city, region, country] if part]
    if not parts:
        return None
    return ", ".join(dict.fromkeys(parts))
