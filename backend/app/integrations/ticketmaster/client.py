from app.core.config import get_settings
from app.integrations.shared import build_async_client


def create_ticketmaster_client():
    settings = get_settings()
    return build_async_client(base_url=settings.ticketmaster_base_url)
