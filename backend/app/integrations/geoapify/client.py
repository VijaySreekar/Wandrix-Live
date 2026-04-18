from app.core.config import get_settings
from app.integrations.shared import build_sync_client


def create_geoapify_client():
    settings = get_settings()
    return build_sync_client(base_url=settings.geoapify_base_url)
