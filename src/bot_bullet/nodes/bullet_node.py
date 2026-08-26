from langchain.messages import HumanMessage
from langchain_core.messages import BaseMessage

from bot_bullet.model import get_model
from bot_bullet.state import State


def bullet_node(state: State) -> dict[str, list[BaseMessage]]:
    image_parts = [
        {"type": "image_url", "image_url": {"url": img_base64}}
        for img_base64 in state["screens_base64"]
    ]
    content = [{"type": "text", "text": "请描述这些图片"}, *image_parts]
    human_message = HumanMessage(content=content)
    response = get_model().invoke([*state["messages"], human_message])
    return {"messages": [human_message, response]}
