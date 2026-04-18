from fastapi import APIRouter

from app.schemas.common import HealthResponse, MessageResponse


router = APIRouter(tags=["system"])
api_router = APIRouter(tags=["system"])


@router.get("/", response_model=MessageResponse)
async def read_root() -> MessageResponse:
    return MessageResponse(message="Wandrix FastAPI backend is running.")


@router.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@api_router.get("/ping", response_model=MessageResponse)
async def ping() -> MessageResponse:
    return MessageResponse(message="pong")
