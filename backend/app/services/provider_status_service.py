from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.integrations.amadeus.client import get_access_token
from app.schemas.provider_status import ProviderStatusItem, ProviderStatusResponse


def get_provider_statuses() -> ProviderStatusResponse:
    return ProviderStatusResponse(
        items=[
            _get_amadeus_status(),
            _get_xotelo_status(),
            _get_agoda_status(),
            _get_hotels_com_status(),
            _get_travel_advisor_status(),
        ]
    )


def _get_amadeus_status() -> ProviderStatusItem:
    settings = get_settings()
    checked_at = datetime.now(timezone.utc)

    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        return ProviderStatusItem(
            provider="amadeus",
            status="not_configured",
            message="Amadeus client credentials are not configured.",
            checked_at=checked_at,
        )

    try:
        get_access_token()
    except httpx.HTTPStatusError as error:
        provider_message = _extract_http_error_message(error)
        return ProviderStatusItem(
            provider="amadeus",
            status="error",
            message=provider_message,
            checked_at=checked_at,
        )
    except Exception as error:
        return ProviderStatusItem(
            provider="amadeus",
            status="error",
            message=str(error) or "Amadeus health check failed unexpectedly.",
            checked_at=checked_at,
        )

    return ProviderStatusItem(
        provider="amadeus",
        status="ok",
        message=f"Amadeus {settings.amadeus_env} credentials authenticated successfully.",
        checked_at=checked_at,
    )


def _extract_http_error_message(error: httpx.HTTPStatusError) -> str:
    try:
        payload = error.response.json()
        description = payload.get("error_description") or payload.get("title")
        if isinstance(description, str):
            return f"Amadeus authentication failed: {description}"
    except Exception:
        pass

    return f"Amadeus authentication failed with status {error.response.status_code}."


def _get_xotelo_status() -> ProviderStatusItem:
    settings = get_settings()
    checked_at = datetime.now(timezone.utc)

    if not settings.rapidapi_key:
        return ProviderStatusItem(
            provider="xotelo",
            status="not_configured",
            message="RapidAPI key is not configured for Xotelo hotel discovery.",
            checked_at=checked_at,
        )

    return ProviderStatusItem(
        provider="xotelo",
        status="ok",
        message="RapidAPI key is configured for Xotelo cached hotel discovery.",
        checked_at=checked_at,
    )


def _get_agoda_status() -> ProviderStatusItem:
    return _build_rapidapi_reference_status(
        provider="agoda",
        configured_message="RapidAPI key is configured for Agoda property-level hotel enrichment.",
        missing_message="RapidAPI key is not configured for Agoda hotel enrichment.",
    )


def _get_hotels_com_status() -> ProviderStatusItem:
    return _build_rapidapi_reference_status(
        provider="hotels_com",
        configured_message="RapidAPI key is configured for Hotels.com property review enrichment.",
        missing_message="RapidAPI key is not configured for Hotels.com property review enrichment.",
    )


def _get_travel_advisor_status() -> ProviderStatusItem:
    return _build_rapidapi_reference_status(
        provider="travel_advisor",
        configured_message="RapidAPI key is configured for Travel Advisor reference enrichment.",
        missing_message="RapidAPI key is not configured for Travel Advisor reference enrichment.",
    )


def _build_rapidapi_reference_status(
    *,
    provider: str,
    configured_message: str,
    missing_message: str,
) -> ProviderStatusItem:
    settings = get_settings()
    checked_at = datetime.now(timezone.utc)
    if not settings.rapidapi_key:
        return ProviderStatusItem(
            provider=provider,
            status="not_configured",
            message=missing_message,
            checked_at=checked_at,
        )

    return ProviderStatusItem(
        provider=provider,
        status="ok",
        message=configured_message,
        checked_at=checked_at,
    )
