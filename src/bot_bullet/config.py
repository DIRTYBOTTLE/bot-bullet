"""配置文件读写（明文 JSON）。

路径：``~/.config/bot-bullet/config.json``
字段：
- ``deepseek_api_key``: DeepSeek API Key
"""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "bot-bullet"
CONFIG_PATH = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """读取配置；文件不存在或损坏时返回空字典。"""
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(data: dict) -> None:
    """保存配置（自动创建目录）。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_api_key() -> str:
    """读取 DeepSeek API Key，没有则返回空串。"""
    return str(load_config().get("deepseek_api_key", "") or "")


def set_api_key(key: str) -> None:
    """保存 DeepSeek API Key。"""
    data = load_config()
    data["deepseek_api_key"] = key
    save_config(data)
