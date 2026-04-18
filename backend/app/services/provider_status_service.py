from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.integrations.amadeus.client import get_access_token
from app.schemas.provider_status import ProviderStatusItem, ProviderStatusResponse


def get_provider_statuses() -> ProviderStatusResponse:
    return ProviderStatusResponse(
        items=[
            _get_amadeus_status(),
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
