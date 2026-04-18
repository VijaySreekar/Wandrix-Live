from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_v1_router, root_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.graph.checkpointer import get_postgres_checkpointer_context
from app.graph.compiled import compile_planning_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_postgres_checkpointer_context() as checkpointer:
        if checkpointer is not None:
            checkpointer.setup()
        app.state.planning_graph = compile_planning_graph(checkpointer=checkpointer)
        yield


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
