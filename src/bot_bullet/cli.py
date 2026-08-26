import time

from dotenv import load_dotenv
from langchain.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig

from bot_bullet.graph import app


def main() -> None:
    load_dotenv()
    config: RunnableConfig = {"configurable": {"thread_id": 1}}
    first = True
    while True:
        try:
            for message in app.stream_events(
                {
                    "messages": [
                        SystemMessage(
                            "你是资深弹幕评论员。根据屏幕内容生成简短、有趣、贴合画面的一条弹幕"
                        )
                    ] if first else []
                },
                config,
                version="v3",
            ).messages:
                print()
                for token in message.text:
                    print(str(token), end="", flush=True)
        except Exception:
            continue
        finally:
            first = False
            time.sleep(15)

