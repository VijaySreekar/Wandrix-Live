from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.auth import AuthenticatedUser


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthenticatedUser)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    return current_user
