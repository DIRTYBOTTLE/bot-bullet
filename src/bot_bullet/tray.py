"""macOS 状态栏弹幕应用（rumps 实现，可靠的状态栏图标）。

菜单：
- 开始/暂停：切换截屏→生成→显示的整个流程（暂停时隐藏弹幕悬浮窗）
- 设置 DeepSeek API Key…：填写/修改 key，存入配置文件
- 退出

用法：``python -m bot_bullet.tray``（或 ``uv run bot-bullet-tray``）
"""

from __future__ import annotations

import os
import sys
import threading
import time
import traceback

import rumps
from dotenv import load_dotenv
from langchain.messages import SystemMessage

from bot_bullet.config import get_api_key, set_api_key
from bot_bullet.graph import app
from bot_bullet.prompt import SYSTEM_PROMPT
from bot_bullet.tools.overlay import set_visible, show_bullet

POLL_INTERVAL = 15  # 每轮间隔（秒）


def _notify(title: str, message: str) -> None:
    """发送系统通知；未打包成 .app 时通知中心不可用，静默忽略。"""
    try:
        rumps.notification(title, "", message)
    except Exception:
        pass


def make_icon_path() -> str | None:
    """画一个红底圆角「弹」图标并存成 PNG，返回路径；失败返回 None（退化为标题显示）。"""
    try:
        import AppKit

        from bot_bullet.config import CONFIG_DIR

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = CONFIG_DIR / "icon.png"
        if path.exists():
            return str(path)

        size = 22.0
        image = AppKit.NSImage.alloc().initWithSize_((size, size))
        image.lockFocus()
        rect = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(0, 0, size, size), 5.0, 5.0
        )
        AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.36, 0.36, 1.0).set()
        rect.fill()
        text = AppKit.NSString.stringWithString_("弹")
        attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(12.0),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor(),
        }
        ts = text.sizeWithAttributes_(attrs)
        text.drawAtPoint_withAttributes_(
            ((size - ts.width) / 2, (size - ts.height) / 2), attrs
        )
        image.unlockFocus()

        rep = AppKit.NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
        png = rep.representationUsingType_properties_(
            AppKit.NSBitmapImageFileTypePNG, None
        )
        png.writeToFile_atomically_(str(path), True)
        return str(path)
    except Exception:
        return None


class LoopThread:
    """后台循环：截图→生成→显示。用事件控制开始/暂停。"""

    def __init__(self) -> None:
        self._paused = threading.Event()  # 默认不暂停
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def pause(self) -> None:
        self._paused.set()
        set_visible(False)  # 暂停时隐藏弹幕悬浮窗

    def resume(self) -> None:
        self._paused.clear()
        set_visible(True)

    def stop(self) -> None:
        self._running = False
        self._paused.clear()  # 让被阻塞的轮询立即返回

    def _run(self) -> None:
        first = True
        graph_config = {"configurable": {"thread_id": 1}}
        while self._running:
            # 暂停时轮询等待。注意：macOS 主线程阻塞在 rumps 的 ObjC 事件循环时，
            # threading.Event.wait() 会异常卡住，所以这里用 is_set() 轮询代替。
            while self._running and self._paused.is_set():
                time.sleep(0.2)
            if not self._running:
                break
            try:
                state = app.invoke(
                    {
                        "messages": [SystemMessage(SYSTEM_PROMPT)] if first else []
                    },
                    graph_config,
                )
                show_bullet(state["messages"][-1].text)
            except Exception as e:
                print(f"[{type(e).__name__}] {e}", flush=True)
                traceback.print_exc()
            finally:
                first = False
                time.sleep(POLL_INTERVAL)


class BotBulletApp(rumps.App):
    def __init__(self) -> None:
        icon = make_icon_path()
        # 有图标就不显示文字标题；图标生成失败时退回显示「弹」文字
        super().__init__(
            "bot-bullet",
            title=None if icon else "弹",
            icon=icon,
            quit_button=None,
        )
        self.loop = LoopThread()
        self.running = False
        self.toggle_item = rumps.MenuItem("开始", callback=self._toggle_run)
        self.menu = [
            self.toggle_item,
            rumps.MenuItem("设置 DeepSeek API Key…", callback=self._prompt_key),
            None,
            rumps.MenuItem("退出", callback=self._quit),
        ]

    def _toggle_run(self, sender) -> None:
        if self.running:
            self.loop.pause()
            self.running = False
            self.toggle_item.title = "开始"
        else:
            self.loop.resume()
            self.running = True
            self.toggle_item.title = "暂停"

    def _prompt_key(self, sender) -> None:
        import re
        import subprocess

        current = get_api_key()
        # 仅当 key 是安全字符时才预填，避免破坏 AppleScript 字符串
        if not re.fullmatch(r"[A-Za-z0-9_\-.]+", current):
            current = ""
        script = (
            'display dialog "输入你的 DeepSeek API Key（sk-...）：" '
            f'default answer "{current}" '
            'with title "设置 DeepSeek API Key" with icon note '
            'buttons {"取消", "保存"} default button "保存"'
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            return
        output = result.stdout.strip()
        if "text returned:" not in output:
            return  # 用户点了取消
        key = output.split("text returned:", 1)[1].strip()
        if not key:
            return
        set_api_key(key)
        os.environ["DEEPSEEK_API_KEY"] = key
        # 清掉模型缓存，让新 key 立即生效
        from bot_bullet.model import get_model

        get_model.cache_clear()
        _notify("bot-bullet", "DeepSeek API Key 已保存")
        # 之前没在运行（多数是没 key 而暂停）→ 自动开始，让用户立即看到效果
        if not self.running:
            self._toggle_run(self.toggle_item)

    def _quit(self, sender) -> None:
        self.loop.stop()
        rumps.quit_application()


def _acquire_single_instance() -> bool:
    """用文件锁确保只有一个实例在跑，防止重复图标；返回是否获得锁。"""
    import fcntl

    from bot_bullet.config import CONFIG_DIR

    global _LOCK_FILE
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _LOCK_FILE = open(CONFIG_DIR / "tray.lock", "w")
    try:
        fcntl.flock(_LOCK_FILE, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


_LOCK_FILE = None


def main() -> None:
    if not _acquire_single_instance():
        # 已有一个实例在跑，直接退出，避免出现两个图标
        print("[bot-bullet] 已在运行，请使用已存在的实例。", flush=True)
        return

    load_dotenv()
    key = get_api_key()
    if key:
        os.environ["DEEPSEEK_API_KEY"] = key

    bot = BotBulletApp()
    if not key:
        # 没 key：先设暂停再启动线程，避免空跑
        bot.loop.pause()
        bot.loop.start()
        threading.Timer(
            1.0,
            lambda: _notify(
                "bot-bullet", "还没有设置 DeepSeek API Key，请先在菜单里填写。"
            ),
        ).start()
    else:
        bot.loop.start()
        bot._toggle_run(bot.toggle_item)  # 有 key 自动开始

    bot.run()


if __name__ == "__main__":
    main()
