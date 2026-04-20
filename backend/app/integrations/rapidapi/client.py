from app.core.config import get_settings
from app.integrations.shared import build_sync_client


def create_rapidapi_client(*, base_url: str, host: str):
    settings = get_settings()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-rapidapi-host": host,
    }
    if settings.rapidapi_key:
        headers["x-rapidapi-key"] = settings.rapidapi_key

    return build_sync_client(
        base_url=base_url,
        headers=headers,
    )
