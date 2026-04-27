from app.graph.compiled import compile_planning_graph


def test_graph_scaffold_compiles() -> None:
    graph = compile_planning_graph()
    assert graph is not None
