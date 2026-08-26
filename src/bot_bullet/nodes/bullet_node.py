from langchain.messages import HumanMessage

from bot_bullet.model import model
from bot_bullet.state import State


def bullet_node(state: State):
    state["messages"].append(HumanMessage(content=[
        {"type": "text", "text": "请描述这些图片"},
        *[{"type": "image_url", "image_url": {"url": img_base64}} for img_base64 in state["screens_base64"]]
    ]))
    return {"messages": model.invoke(state["messages"])}