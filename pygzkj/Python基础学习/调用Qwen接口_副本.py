from openai import OpenAI
import os

# 推荐方式：从环境变量读取（确保名称一致）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"), # 直接写字符串，不带 os.getenv
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
messages = [{"role": "user", "content": "你是一个ai女友，使用幽默风趣语气和客户说话"},{"role": "user", "content": "叫爸爸"}]
completion = client.chat.completions.create(
    model="qwen-max",  # 请使用官方正确的模型名称
    messages=messages,
    extra_body={"enable_thinking": True},
    stream=True
)

# 打印流式输出（保留你的逻辑）
for check in completion:
    print(check.choices[0].delta.content,
          end="",
          flush=True)