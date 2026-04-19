from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.provider_status import ProviderStatusResponse
from app.services.provider_status_service import get_provider_statuses


router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status", response_model=ProviderStatusResponse)
def get_provider_status_route(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProviderStatusResponse:
    return get_provider_statuses()
