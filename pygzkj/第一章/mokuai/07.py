import streamlit as st
import os
import sys
from openai import OpenAI
from streamlit import user_info

st.set_page_config(
   page_title="Ex-stream-ly Cool App",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
   menu_items={
   }
)
st.title("AI伴侣")
st.logo("logo.png")
st.header("人工智能交互")
promt=st.chat_input("请输入要问的的问题")
#创建与大模型交互的客户端对象
system_part="你是一名可爱的ai女友，你叫llh，风趣幽默的语气而且不能有嘲讽的语气"
if "message" not in st.session_state:
   st.session_state.message=[]
for message in st.session_state.message:
      st.chat_message(message["role"]).write(message["content"])


if promt:
   st.chat_message("user").write(promt)
   client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")
   #与大模型进行交互
   #保存用户的提示词
   st.session_state.message.append({"role":"user","content":promt})
   response = client.chat.completions.create(
       model="deepseek-v4-pro",
       messages=[
           {"role": "system", "content": system_part},
           {"role": "user", "content": promt},
       ],
       stream=False,
       reasoning_effort="high",
       extra_body={"thinking": {"type": "enabled"}}
   )
   #输出大模型的返回结果
   st.chat_message("assistant").write(response.choices[0].message.content)
   st.session_state.message.append({"role":"assistant","content":response.choices[0].message.content})