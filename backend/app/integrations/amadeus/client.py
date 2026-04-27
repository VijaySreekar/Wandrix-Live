from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.integrations.shared import build_sync_client


_TOKEN_CACHE: dict[str, object] = {
    "access_token": None,
    "expires_at": None,
}


def get_access_token() -> str:
    cached_token = _TOKEN_CACHE.get("access_token")
    expires_at = _TOKEN_CACHE.get("expires_at")

    if (
        isinstance(cached_token, str)
        and isinstance(expires_at, datetime)
        and expires_at > datetime.now(timezone.utc)
    ):
        return cached_token

    settings = get_settings()
    with build_sync_client(base_url=settings.amadeus_base_url) as client:
        response = client.post(
            "/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.amadeus_client_id,
                "client_secret": settings.amadeus_client_secret,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()

    payload = response.json()
    access_token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 1800))
    _TOKEN_CACHE["access_token"] = access_token
    _TOKEN_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(
        seconds=max(expires_in - 60, 60)
    )
    return access_token


def create_amadeus_client(*, timeout: float | None = None):
    settings = get_settings()
    access_token = get_access_token()
    return build_sync_client(
        base_url=settings.amadeus_base_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=timeout or 30.0,
    )
