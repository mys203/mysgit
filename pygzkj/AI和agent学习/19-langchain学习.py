import os
import sys
from urllib import response

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
     }
]
summ=[]
while True:
    user_input=input("请输入:")
    if user_input=="quit":
        print("欢迎下次使用")
        break
    else:
        massages.append({"role":"user","content":user_input})
        """response = llm.invoke(massages)
        print("LLH:",response.content)
        massages.append({"role":"assistant","content":response.content})"""
        for m in llm.stream(massages):
            if m :
                print(m.content,end="",flush=True)
                summ+=m.content
        print()