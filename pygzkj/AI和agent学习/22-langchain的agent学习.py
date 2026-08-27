import os
import sys

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
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

# 创建 agent（system_prompt 直接传字符串即可）
agent = create_agent(
    model=llm,
    tools=[],  # 暂时没有工具，先跑通再说
    system_prompt="你是一个AI女友",
)

# 调用 agent：注意键名是 messages，且要传消息对象
response = agent.invoke({"messages": [HumanMessage(content="你好")]})

# agent 的返回是一个状态字典，最后一条消息就是 AI 的回复
print(response["messages"][-1].content)
