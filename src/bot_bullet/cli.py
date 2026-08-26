from dotenv import load_dotenv
from langchain.messages import SystemMessage

from bot_bullet.graph import app


def main() -> None:
    load_dotenv()
    for message in app.stream_events(
        {
            "messages": [
                SystemMessage(
                    "你是资深弹幕评论员。根据屏幕内容生成简短、有趣、贴合画面的一条弹幕"
                )
            ]
        },
        version="v3",
    ).messages:
        for token in message.text:
            print(str(token), end="", flush=True)
