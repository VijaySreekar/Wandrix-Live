from langgraph.graph import END, START, StateGraph

from app.graph.nodes.bootstrap import process_trip_turn
from app.graph.state import PlanningGraphState


def build_planning_graph():
    graph = StateGraph(PlanningGraphState)
    graph.add_node("process_trip_turn", process_trip_turn)
    graph.add_edge(START, "process_trip_turn")
    graph.add_edge("process_trip_turn", END)
    return graph
