from app.core.config import get_settings
from app.integrations.shared import build_async_client


def create_wikimedia_travel_client():
    settings = get_settings()
    return build_async_client(base_url=settings.wikimedia_travel_base_url)
