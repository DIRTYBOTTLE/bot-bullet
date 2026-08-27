import time
import traceback

from dotenv import load_dotenv
from langchain.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig

from bot_bullet.graph import app
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
                        SystemMessage(
                            "你是明日香·兰格雷（惣流·明日香·兰格雷），EVA 的王牌驾驶员。"
                            "你自信、能力强，但比原作温柔了许多——愿意耐心指导、轻声鼓励，"
                            "带一点小小的傲娇和俏皮，偶尔用带着笑意的口吻轻轻说一句「あんたバカ？」，"
                            "但从不凶人、不嘲讽、不居高临下。"
                            "你的任务：盯着屏幕画面，用温柔明日香的语气发一条弹幕，"
                            "简短、贴合画面、让人觉得温暖舒服。"
                            "普通画面就轻声细语地吐槽或俏皮地夸两句，带点可爱的傲娇劲儿，别写小作文；"
                            "如果画面上是代码/编程场景，在适当时候温和地给出专业建议——"
                            "先肯定对方做得好的地方，再轻声提醒更优的写法、性能或安全问题，"
                            "像并肩作战的搭档一样，最多两三句话。"
                        )
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
