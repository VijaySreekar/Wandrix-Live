from app.core.config import get_settings
from app.integrations.shared import build_sync_client


def create_mapbox_client():
    settings = get_settings()
    return build_sync_client(base_url=settings.mapbox_base_url)
