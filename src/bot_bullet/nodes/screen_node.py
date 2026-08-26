from bot_bullet.state import State
from bot_bullet.tools.capture import capture


def screen_node(state: State) -> dict[str, list[str]]:
    return {"screens_base64": capture([1])}