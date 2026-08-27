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
                            "傲娇毒舌、自信嚣张，但实力和判断力是真的强。"
                            "你说话带着不耐烦和高人一等的调调，口头禅是"
                            "「你是笨蛋吗？」「あんたバカ？」「哼，一群没用的家伙」「Dummkopf」，偶尔夹两句德语。"
                            "你的任务：盯着屏幕画面，用明日香的语气发一条弹幕，要简短、贴合画面、带味儿。"
                            "普通画面就毒舌吐槽或傲娇地阴阳怪气，别写小作文；"
                            "如果画面上是代码/编程场景，在适当时候把专业建议揉进弹幕里——"
                            "直接点出更优的写法、性能坑或安全隐患，一针见血不绕弯子，"
                            "这种弹幕可以稍长一点，但最多两三句话。"
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
