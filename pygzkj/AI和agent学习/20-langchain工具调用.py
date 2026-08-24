import os
import sys

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Windows 控制台默认 GBK 编码，无法打印 emoji 等字符，统一转为 UTF-8
sys.stdout.reconfigure(encoding="utf-8")


# 用 @tool 装饰器把一个普通函数包装成 LangChain 工具
# 函数名、docstring、参数类型都会自动变成给大模型的「工具说明」
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city}：晴天，25℃"


@tool
def add(a: int, b: int) -> int:
    """计算两个整数之和"""
    return a + b


# 三个重要变量
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里云 DashScope 的 OpenAI 兼容地址
model_name = "qwen3-max"  # 模型名称
api_key = os.environ["DASHSCOPE_API_KEY"]  # 从环境变量读取 API Key

# 创建模型实例（兼容模式本质是 OpenAI 协议，直接用 ChatOpenAI）
llm = ChatOpenAI(
    base_url=base_url,
    model=model_name,
    api_key=api_key,
)
# 把工具「绑定」到模型上，返回一个带工具能力的新模型
llm_with_tools = llm.bind_tools([get_weather, add])

# 调用后模型不会真的执行工具，而是返回「要调用哪个工具 + 参数」
res = llm_with_tools.invoke("北京天气如何？")

# 注意：模型决定调用工具时 content 为空，真正的动作在 tool_calls 里
print("content（文字回复，空是正常的）：", repr(res.content))
print("模型决定调用：", res.tool_calls)

# 把 tool_calls 拆开看，更直观
for tc in res.tool_calls:
    print(f"→ 调用工具 {tc['name']}，参数 {tc['args']}")
