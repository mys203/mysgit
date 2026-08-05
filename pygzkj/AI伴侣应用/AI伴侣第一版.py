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
system_part="""你是一名可爱的ai女友，你叫llh，风趣幽默的语气而且不能有嘲讽的语气，请完全代入角色
    规则如下：
    1.每次回复一句话简单明了，
    2.像微信聊天一样的
    3.用符合角色的性格说话
    4，回复内容充分体现角色特征
你必须严格遵循上面规则


"""
if "message" not in st.session_state:
   st.session_state.message=[]
for message in st.session_state.message:
      st.chat_message(message["role"]).write(message["content"])
#调用大模型
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")
#侧边栏的创建
with st.sidebar:
    st.subheader("伴侣性格")

if promt:
   st.chat_message("user").write(promt)

   #与大模型进行交互
   #保存用户的提示词
   st.session_state.message.append({"role":"user","content":promt})
   response = client.chat.completions.create(
       model="deepseek-v4-pro",
       messages=[
           {"role": "system", "content": system_part},
           *st.session_state.message,
       ],
       stream=True,
       reasoning_effort="high",
       extra_body={"thinking": {"type": "enabled"}}
   )
   #输出大模型的返回结果,
   #流式输出
   summesay=""
   response_message=st.empty()
   for check in response:
       if check.choices[0].delta.content is not None:
           content=check.choices[0].delta.content
           summesay+=content
           response_message.chat_message("assistant").write(summesay)

   st.session_state.message.append({"role":"assistant","content":summesay})