"""弹幕 SC 悬浮窗子进程（PySide6 实现）。

由 ``overlay.py`` 通过 ``python -m bot_bullet.tools.overlay_server`` 拉起，
从 stdin 逐行读取 JSON 消息并在屏幕左下角显示 SC 风格弹幕卡片。

用独立子进程 + Qt 事件循环的原因：

- ``WindowStaysOnTopHint`` 在 macOS 上能真正跨 App 置顶，切窗口不会被盖；
- ``WA_TranslucentBackground`` 实现真·透明圆角，不会有 Tk 那种空白框/方形窗口；
- 动画在 Qt 事件循环里跑，完全不阻塞宿主进程。

消息格式（每行一个 JSON）::

    {"type": "bullet", "text": "...", "name": "...", "price": 1000}
"""

from __future__ import annotations

import json
import sys
import threading
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

CARD_W = 240
MARGIN = 16
CARD_GAP = 8
BOTTOM_OFFSET = 40  # 卡片距屏幕底部的距离（往上一些）
LIFETIME_MS = 60_000
FONT_FAMILY = "PingFang SC"
TIERS: list[tuple[int, str]] = [
    (30, "#f3f3f3"),
    (50, "#4aa8ff"),
    (100, "#5dd0c2"),
    (500, "#ff9d35"),
    (1000, "#ff5c5c"),
    (2000, "#b877ff"),
]


class Card(QWidget):
    """一张 SC 卡片：浅色头部(昵称/价格/时间) + 价位色消息区。"""

    def __init__(self, text: str, name: str, price: int, ts: str) -> None:
        super().__init__()
        accent = min(TIERS, key=lambda t: abs(t[0] - price))[1]
        header_bg = _lighten(accent, 0.85)
        text_color = "#1a1a1a" if _luminance(accent) > 150 else "#ffffff"
        self.deadline = time.monotonic() + LIFETIME_MS / 1000

        self.setFixedWidth(CARD_W)
        # 关键：普通 QWidget 必须设置 WA_StyledBackground 才会真正绘制背景色
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background:{_rgba(header_bg, 0.8)}; border-radius:12px;")

        box = QVBoxLayout(self)
        box.setContentsMargins(10, 8, 10, 10)
        box.setSpacing(5)

        top = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("background:transparent; color:#1a1a1a; font-weight:bold; font-size:12px;")
        price_label = QLabel(f"CN ¥ {price}")
        price_label.setStyleSheet("background:transparent; color:#1a1a1a; font-weight:bold; font-size:12px;")
        top.addWidget(name_label)
        top.addStretch(1)
        top.addWidget(price_label)
        box.addLayout(top)

        ts_label = QLabel(ts)
        ts_label.setStyleSheet("background:transparent; color:#8a8a8a; font-size:10px;")
        box.addWidget(ts_label)

        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(
            f"background:{_rgba(accent, 0.85)}; color:{text_color}; border-radius:8px; padding:8px 10px; font-size:13px;"
        )
        box.addWidget(msg_label)


class Overlay(QWidget):
    """容纳所有卡片、锚定左下角、随卡片数量自动向上生长的悬浮窗。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 不拦截鼠标点击
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(CARD_GAP)
        self._cards: list[Card] = []

    def add_bullet(self, text: str, name: str, price: int) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        card = Card(text, name, price, ts)
        self._cards.append(card)
        self._layout.addWidget(card)  # 新卡片在最下面，窗口整体向上增长
        self._relayout()

    def _relayout(self) -> None:
        # 显式按每张卡片在固定宽度下的真实高度累加，避免 word-wrap 高度被低估导致裁剪
        gap = CARD_GAP * max(0, len(self._cards) - 1)
        total_h = sum(_card_height(c) for c in self._cards) + gap
        screen = QGuiApplication.primaryScreen().geometry()
        # 卡片堆放在屏幕底部、往上 BOTTOM_OFFSET 处；新卡片加入时整体向上增长
        y = screen.bottom() - BOTTOM_OFFSET - total_h
        self.setGeometry(MARGIN, y, CARD_W, total_h)

    def tick(self) -> None:
        """清理到期的卡片。"""
        now = time.monotonic()
        for card in list(self._cards):
            if card.deadline <= now:
                self._cards.remove(card)
                card.deleteLater()
                self._relayout()


def _card_height(card: Card) -> int:
    """卡片在固定宽度下的真实高度（正确考虑 word-wrap 换行）。"""
    h = card.heightForWidth(CARD_W)
    if h <= 0:
        h = card.sizeHint().height()
    return h


def _rgba(hex_color: str, alpha: float) -> str:
    """把 #rrggbb 转成 rgba(r,g,b,alpha) 样式串，用于半透明背景。"""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _luminance(hex_color: str) -> float:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _lighten(hex_color: str, factor: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> int:
    app = QApplication(sys.argv)
    # 把进程设为 Accessory（后台）应用：不显示 Dock 图标，也不出现在 Cmd-Tab 里
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )
    except Exception:
        pass
    app.setFont(QFont(FONT_FAMILY))
    window = Overlay()
    window.show()

    # stdin 读取线程：把 JSON 行放入队列，由 Qt 定时器在 GUI 线程取用
    from queue import Queue

    queue: Queue[dict] = Queue()

    def reader() -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                queue.put(json.loads(line))
            except json.JSONDecodeError:
                pass

    threading.Thread(target=reader, daemon=True).start()

    def drain() -> None:
        while not queue.empty():
            msg = queue.get()
            if msg.get("type") == "bullet":
                window.add_bullet(msg["text"], msg["name"], msg["price"])
            elif msg.get("type") == "visible":
                window.setVisible(bool(msg.get("visible", True)))

    poller = QTimer()
    poller.timeout.connect(drain)
    poller.start(50)

    expire = QTimer()
    expire.timeout.connect(window.tick)
    expire.start(1000)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
