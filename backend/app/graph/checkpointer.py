from contextlib import nullcontext

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import get_settings
from app.graph.compiled import compile_planning_graph


def get_postgres_checkpointer_context():
    settings = get_settings()

    if not settings.database_url:
        return nullcontext(None)

    return PostgresSaver.from_conn_string(settings.database_url)

def create_postgres_checkpointer_pool():
    settings = get_settings()

    if not settings.database_url:
        return None

    return ConnectionPool(
        conninfo=settings.database_url,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        min_size=1,
        max_size=10,
        open=False,
    )


def compile_planning_graph_with_pool(pool: ConnectionPool | None):
    if pool is None:
        return compile_planning_graph(checkpointer=None)

    checkpointer = PostgresSaver(pool)
    return compile_planning_graph(checkpointer=checkpointer)
