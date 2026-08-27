import time

from bot_bullet.state import State
from bot_bullet.tools.capture import capture
from bot_bullet.tools.overlay import set_visible


def screen_node(state: State) -> dict[str, list[str]]:
    set_visible(False)  # 截图前隐藏弹幕，避免弹幕入镜
    time.sleep(0.1)     # 等服务端处理隐藏命令（50ms 轮询）
    try:
        imgs = capture([1])
    finally:
        set_visible(True)  # 截完恢复显示
    return {"screens_base64": imgs}