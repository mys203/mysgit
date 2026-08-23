# langchain调用线上模型deepseek
# 涉及到的三个重要的变量
# base_url、model_name、api_key
import os
import sys
from langchain_deepseek import ChatDeepSeek

# Windows 控制台默认 GBK 编码，无法打印 emoji 等字符，统一转为 UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# 三个重要变量
base_url = "https://api.deepseek.com"    # DeepSeek 官方 API 地址
model_name = "deepseek-v4-pro"             # 模型名称
api_key = os.environ["DEEPSEEK_API_KEY"]  # 从环境变量读取 API Key

# 创建模型实例
llm = ChatDeepSeek(
    base_url=base_url,
    model=model_name,
    api_key=api_key,
)

# 调用模型
response = llm.invoke("你好")
print(response.content)
