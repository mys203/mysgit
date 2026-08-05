import streamlit as st
import os
import sys
from openai import OpenAI
from streamlit import user_info
from datetime import datetime
import json
def savef_session():
    saf_list={
        "name_1":st.session_state.name_1,
        "set_1":st.session_state.set_1,
        "current_session":st.session_state.current_session,
        "message":st.session_state.message,
    }
    #如果session 目录不存在，则创建
    if not os.path.exists("session"):
        os.mkdir("session")
    with open("session/"+st.session_state.current_session+".json","w",encoding="utf-8") as f:
        json.dump(saf_list,f,ensure_ascii=False,indent=2)

def generate_session():
    return datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    with open("sessions.json","w",encoding="utf-8") as f:
        json.dump(saf_list,f,ensure_ascii=False,indent=2)

st.set_page_config(
   page_title="人工智能伴侣",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
   menu_items={
   }
)
st.title("AI伴侣")
# st.logo("logo.png")
st.header("人工智能交互")
# st.audio("The truth that you leave（你离开的事实）.mp3")
promt=st.chat_input("请输入要问的的问题")
#创建与大模型交互的客户端对象
system_part="""你是一名可爱的ai女友，你叫%s，%s的语气而且不能有嘲讽的语气，请完全代入角色
    规则如下：
    1.每次回复简单明了，
    2.像微信聊天一样的
    3.用符合角色的性格说话
    4，回复内容充分体现角色特征
    5.当用户要求解析事情时候可以进一步解释
你必须严格遵循上面规则


"""
if "message" not in st.session_state:
   st.session_state.message=[]
if "name_1" not in st.session_state:
    st.session_state.name_1= "llh"
if "set_1" not in st.session_state:
    st.session_state.set_1 ="风趣幽默"
if "current_session" not in st.session_state:
    st.session_state.current_session =datetime.now().strftime("%Y-%m-%d-%H-%M-%S")



for message in st.session_state.message:
      st.chat_message(message["role"]).write(message["content"])
#调用大模型
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")
#侧边栏的创建
with st.sidebar:
    st.header("AI控制面版")
    if st.button("新建对话",width=300,icon="👩‍❤️‍👩"):
        #保存文本
        savef_session()


        #新建一个对话
        if st.session_state.message:
            st.session_state.message=[]
            st.session_state.current_session =generate_session()
            savef_session()
            st.rerun()


    name_1=st.text_input("姓名",placeholder="请输入你想要的的名称",value=st.session_state.name_1)
    if name_1:
        st.session_state.name_1=name_1
    set_1=st.text_area("性格",placeholder="输入你想要的性格",value=st.session_state.set_1)
    if set_1:
        st.session_state.set_1=set_1


if promt:
   st.chat_message("user").write(promt)

   #与大模型进行交互
   #保存用户的提示词
   response = client.chat.completions.create(
       model="deepseek-v4-pro",
       messages=[
           {"role": "system", "content": system_part % (st.session_state.name_1,st.session_state.set_1)},
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
    #存储用户和ai的话
   st.session_state.message.append({"role": "user", "content": promt})
   st.session_state.message.append({"role":"assistant","content":summesay})