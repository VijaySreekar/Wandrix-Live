from fastapi import APIRouter

from app.api.routes import auth, browser_sessions, conversation, packages, providers, system, trips


root_router = APIRouter()
root_router.include_router(system.router)

api_v1_router = APIRouter()
api_v1_router.include_router(system.api_router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(browser_sessions.router)
api_v1_router.include_router(trips.router)
api_v1_router.include_router(providers.router)
api_v1_router.include_router(conversation.router)
api_v1_router.include_router(packages.router)
