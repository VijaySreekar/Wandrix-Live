from contextlib import nullcontext

from langgraph.checkpoint.postgres import PostgresSaver

from app.core.config import get_settings


def get_postgres_checkpointer_context():
    settings = get_settings()

    if not settings.database_url:
        return nullcontext(None)

    return PostgresSaver.from_conn_string(settings.database_url)
