from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_v1_router, root_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.graph.checkpointer import create_postgres_checkpointer_pool
from langgraph.checkpoint.postgres import PostgresSaver


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_postgres_checkpointer_pool()
    if pool is not None:
        pool.open(wait=True)
        PostgresSaver(pool).setup()
    app.state.checkpointer_pool = pool
    try:
        yield
    finally:
        if pool is not None:
            pool.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
    )

    configure_cors(app)
    app.include_router(root_router)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app
