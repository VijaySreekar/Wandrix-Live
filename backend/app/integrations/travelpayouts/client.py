from app.core.config import get_settings
from app.integrations.shared import build_sync_client


def create_travelpayouts_client():
    settings = get_settings()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    if settings.travelpayouts_api_token:
        headers["X-Access-Token"] = settings.travelpayouts_api_token

    return build_sync_client(
        base_url=settings.travelpayouts_base_url,
        headers=headers,
    )
