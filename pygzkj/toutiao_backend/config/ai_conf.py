import os
from openai import AsyncOpenAI

# 大模型配置：key 从环境变量读取，不要写死在代码里
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-v4-pro"
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 系统提示词，让 AI 以助手的角色回答
SYSTEM_PROMPT = "你是一个乐于助人的AI新闻助手，请用中文、简洁地回答问题。"

# 对话控制参数
MAX_HISTORY_ROUNDS = 10   # 最多保留最近 10 轮，更早的压成摘要
TEMPERATURE = 0.5         # 调低温度，回答更收敛、减少幻觉

# 创建异步客户端（配合 FastAPI 的 async 路由，避免阻塞事件循环）
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)
