"""左下角弹幕展示工具（B站 SC 风格，底层 PySide6 独立子进程）。

把字符串变成屏幕左下角的 SC 风格弹幕卡片：真正跨 App 置顶、真·透明圆角、
动画不阻塞宿主。实现方式：

- 首次调用 ``show_bullet`` 时拉起一个子进程 ``bot_bullet.tools.overlay_server``
  （PySide6 + Qt 事件循环），此后通过 stdin 逐行发送 JSON 消息；
- 宿主进程只负责发字符串，不 import PySide6，也不跑 GUI 事件循环，
  因此可在任意主循环里调用，不会和你的弹幕生成逻辑抢主线程。

用法::

    from bot_bullet.tools.overlay import show_bullet

    show_bullet("一条弹幕")                          # 默认随机网络昵称、自动循环价位
    show_bullet("一条弹幕", name="老铁", price=1000)  # 指定用户名和价位
"""

from __future__ import annotations

import atexit
import json
import random
import subprocess
import sys

# 网络昵称词库：形容词 + 名词 随机组合
_NICK_ADJ = [
    "爱笑", "爱哭", "爱打游戏", "爱吃辣", "熬夜冠军", "养生", "快乐",
    "摸鱼", "佛系", "暴躁", "温柔", "可爱", "高冷", "段子手", "追剧",
    "干饭", "网抑云", "精神小伙", "美少女", "资深", "路过", "潜水", "吃瓜",
]
_NICK_NOUN = [
    "的猫", "的狗", "的兔子", "的小笼包", "的夜宵", "的键盘", "的屏幕",
    "的网友", "的大佬", "的小透明", "的锦鲤", "的咸鱼", "的打工人",
    "的柠檬精", "的鸽子", "的沙发", "的空调", "的奶茶", "的快乐星球", "的摆烂人",
]
# 价位（元）：不传 price 时随机取一个整数；overlay_server 按就近档位匹配颜色
__all__ = ["show_bullet", "set_visible"]

_proc: subprocess.Popen | None = None
_shutdown_registered = False


def show_bullet(
    text: str,
    *,
    name: str | None = None,
    price: int | None = None,
) -> None:
    """在屏幕左下角显示一条 SC 风格弹幕，60 秒后自动消失；多条依次向上顶。

    :param text: 消息内容。
    :param name: 网络昵称；不传则随机生成一个。
    :param price: 价位（元）；不传则随机取一个整数。
    """
    text = text.strip()
    if not text:
        return
    if name is None:
        name = _random_nickname()
    if price is None:
        price = random.randint(30, 1000)
    _send({"type": "bullet", "text": text, "name": name, "price": price})


def _random_nickname() -> str:
    """随机生成一个网络昵称，如 "爱打游戏的猫"、"吃瓜的咸鱼"。"""
    return f"{random.choice(_NICK_ADJ)}{random.choice(_NICK_NOUN)}"


def set_visible(visible: bool) -> None:
    """隐藏/显示弹幕悬浮窗。

    截图前调用 ``set_visible(False)`` 让弹幕临时消失，截完再 ``set_visible(True)``
    恢复，避免弹幕被截进图里、大模型吐槽自己的弹幕。
    """
    global _proc
    if _proc is None or _proc.poll() is not None:
        return  # 弹幕服务还没启动过，无需隐藏
    try:
        _proc.stdin.write(
            (json.dumps({"type": "visible", "visible": visible}, ensure_ascii=False) + "\n").encode("utf-8")
        )
        _proc.stdin.flush()
    except (BrokenPipeError, OSError):
        pass


def _send(payload: dict) -> None:
    if not _ensure_proc():
        return
    try:
        _proc.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        _proc.stdin.flush()
    except (BrokenPipeError, OSError):
        # 子进程意外退出则重启一次再试
        if not _ensure_proc(force=True):
            return
        try:
            _proc.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            _proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass


def _ensure_proc(force: bool = False) -> bool:
    """确保 overlay_server 子进程存在并存活；返回是否可用。"""
    global _proc, _shutdown_registered
    if _proc is not None and not force and _proc.poll() is None:
        return True
    if _proc is not None and _proc.poll() is None:
        try:
            _proc.stdin.close()
            _proc.terminate()
        except OSError:
            pass
    _proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "bot_bullet.tools.overlay_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _shutdown_registered:
        atexit.register(_shutdown)
        _shutdown_registered = True
    return True


def _shutdown() -> None:
    """退出时关闭子进程。"""
    global _proc
    if _proc is not None and _proc.poll() is None:
        try:
            _proc.stdin.close()
            _proc.terminate()
            _proc.wait(timeout=2)
        except Exception:
            pass
    _proc = None


# import time
# while True:
#     show_bullet("算法大富大贵的时光算法大富大贵的时光算法大富大贵的时光算法大富大贵的时光")
#     time.sleep(5)