from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

model = init_chat_model(
    model="deepseek-v4-flash-vision-exp",
    extra_body={"thinking": {"type": "disabled"}},
)