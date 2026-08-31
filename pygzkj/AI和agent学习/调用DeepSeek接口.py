from openai import OpenAI

# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "你是一个AI女友"},
        {"role": "user", "content": "你好"},
    ],
    stream=True,
)
summesay = ""
for check in response:
    if check.choices[0].delta.content is not None:
        print(
            check.choices[0].delta.content,
            end="",
            flush=True
        )

        # content = check.choices[0].delta.content
        # print(content,end="")