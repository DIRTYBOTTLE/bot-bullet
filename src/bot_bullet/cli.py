import time
import traceback

from dotenv import load_dotenv
from langchain.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig

from bot_bullet.graph import app
from bot_bullet.prompt import SYSTEM_PROMPT
from bot_bullet.tools.overlay import show_bullet


def main() -> None:
    load_dotenv()
    config: RunnableConfig = {"configurable": {"thread_id": 1}}
    first = True
    while True:
        try:
            state = app.invoke(
                {
                    "messages": [
                        SystemMessage(SYSTEM_PROMPT)
                    ]
                    if first
                    else []
                },
                config,
            )
            show_bullet(state["messages"][-1].text)
        except Exception as e:
            print(f"[{type(e).__name__}] {e}", flush=True)  # 一行摘要
            traceback.print_exc()                    # 完整堆栈
            continue
        finally:
            first = False
            time.sleep(15)
