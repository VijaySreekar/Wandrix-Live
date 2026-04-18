from app.core.config import get_settings
from app.integrations.shared import build_sync_client


def create_open_meteo_client():
    settings = get_settings()
    return build_sync_client(base_url=settings.open_meteo_base_url)
