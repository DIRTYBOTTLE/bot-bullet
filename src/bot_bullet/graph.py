from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from bot_bullet.nodes.bullet_node import bullet_node
from bot_bullet.nodes.screen_node import screen_node
from bot_bullet.nodes.trim_node import trim_node
from bot_bullet.state import State

TRIM_NODE = "trim_node"
SCREEN_NODE = "screen_node"
BULLET_NODE = "bullet_node"

_graph = StateGraph(State)
_graph.add_node(TRIM_NODE, trim_node)
_graph.add_node(SCREEN_NODE, screen_node)
_graph.add_node(BULLET_NODE, bullet_node)
_graph.add_edge(START, TRIM_NODE)
_graph.add_edge(TRIM_NODE,SCREEN_NODE)
_graph.add_edge(SCREEN_NODE, BULLET_NODE)
_graph.add_edge(BULLET_NODE, END)
app = _graph.compile(InMemorySaver())

