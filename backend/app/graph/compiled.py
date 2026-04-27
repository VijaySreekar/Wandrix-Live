from app.graph.builder import build_planning_graph


def compile_planning_graph(*, checkpointer=None):
    graph = build_planning_graph()
    return graph.compile(checkpointer=checkpointer)
