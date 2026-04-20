from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.location_search import LocationSearchKind, LocationSearchResponse
from app.schemas.provider_status import ProviderStatusResponse
from app.services.location_search_service import search_locations
from app.services.provider_status_service import get_provider_statuses


router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status", response_model=ProviderStatusResponse)
def get_provider_status_route(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProviderStatusResponse:
    return get_provider_statuses()


@router.get("/locations/search", response_model=LocationSearchResponse)
def search_locations_route(
    query: str = Query(..., min_length=2, max_length=120),
    kind: LocationSearchKind = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> LocationSearchResponse:
    return search_locations(query=query, kind=kind)
