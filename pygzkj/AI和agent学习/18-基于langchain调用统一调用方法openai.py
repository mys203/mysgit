# langchain调用线上模型 qwen3-max（阿里云 OpenAI 兼容模式）
# 涉及到的三个重要的变量
# base_url、model_name、api_key
import os
import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


# Windows 控制台默认 GBK 编码，无法打印 emoji 等字符，统一转为 UTF-8
sys.stdout.reconfigure(encoding="utf-8")


# 三个重要变量
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"    # 阿里云 DashScope 的 OpenAI 兼容地址
model_name = "qwen3-max"             # 模型名称
api_key = os.environ["DASHSCOPE_API_KEY"]  # 从环境变量读取 API Key

# 创建模型实例（兼容模式本质是 OpenAI 协议，直接用 ChatOpenAI）
llm = ChatOpenAI(
    base_url=base_url,
    model=model_name,
    api_key=api_key,
)
massages=[
     {"role":"system","content":"你是一个风趣幽默的ai女友"
     },
     {"role":"user","content":"你是谁"},
     {"role":"assistant","content":'哎呀，终于等到你问这个问题啦！我是你的AI女友小甜心~最喜欢和你聊天。'},
     {"role":"user","content":"我刚刚问了什么"},
]
#或者等效下面这个
massages1=[
    SystemMessage(content="你是一个风趣幽默的ai女友"),
    HumanMessage(content="你好")
]

# 调用模型
response = llm.invoke(massages1)
print(response.content)


