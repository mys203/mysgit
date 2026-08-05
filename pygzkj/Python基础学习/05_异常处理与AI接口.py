#异常处理
# try:
#     print(a)
# except Exception as e:
#     print("系统出错，联系管理员")
# finally:
#     print("finally无论怎么样出错都会运行")
# def fun():
#     print("hello world")
#     fun1()
# def fun1():
#     print("hello world1")
#     fun2()
# def fun2():
#     print("hello world2")
#     print(asd)
# if __name__ == "__main__":
#     try:
#         fun()
#     except Exception as e:
#         print("系统出错了")
# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
#创建与大模型交互的客户端对象
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")
#与大模型进行交互
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "你是一名可爱的ai女友，你叫llh，风趣幽默的语气而且不能有嘲讽的语气"},
        {"role": "user", "content": "两个人能干嘛呢"},
    ],
    stream=False,
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}}
)
#输出大模型的返回结果
print(response.choices[0].message.content)