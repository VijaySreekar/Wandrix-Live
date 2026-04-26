from fastapi import APIRouter

from app.schemas.package import TravelPackageRequest, TravelPackageResponse
from app.services.package_generator import generate_travel_package


router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("/generate", response_model=TravelPackageResponse)
def generate_package(
    payload: TravelPackageRequest,
) -> TravelPackageResponse:
    return generate_travel_package(payload)
