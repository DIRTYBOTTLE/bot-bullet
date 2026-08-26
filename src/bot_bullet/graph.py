from langgraph.graph import END, START, StateGraph

from bot_bullet.nodes.bullet_node import bullet_node
from bot_bullet.nodes.screen_node import screen_node
from bot_bullet.state import State

_graph = StateGraph(State)
_graph.add_node(bullet_node)
_graph.add_node(screen_node)
_graph.add_edge(START, "screen_node")
_graph.add_edge("screen_node", "bullet_node")
_graph.add_edge("bullet_node", END)
app = _graph.compile()

