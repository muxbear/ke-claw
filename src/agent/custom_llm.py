import os

from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv

load_dotenv()

deepseek_chat_model = ChatDeepSeek(model="deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))

deepseek_reasoner_model = ChatDeepSeek(model="deepseek-reasoner", api_key=os.getenv("DEEPSEEK_API_KEY"))
