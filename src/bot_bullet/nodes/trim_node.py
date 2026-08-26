from langchain.messages import RemoveMessage, SystemMessage

from bot_bullet.state import State

KEEP_ROUNDS = 3

def trim_node(state: State) -> State:
    messages = state["messages"]
    sys_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    history = [m for m in messages if not isinstance(m, SystemMessage)]
    keep_msg_ids = [m.id for m in sys_msgs + history[-KEEP_ROUNDS*2:]]
    return {"messages": [RemoveMessage(m.id) for m in messages if m.id not in keep_msg_ids]}