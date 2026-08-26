from functools import cache

from langchain.chat_models import init_chat_model


@cache
def get_model():
    return init_chat_model(
        model="deepseek-v4-flash-vision-exp",
        extra_body={"thinking": {"type": "disabled"}},
    )