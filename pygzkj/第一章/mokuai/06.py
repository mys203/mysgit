import streamlit as st


st.title("streamlit ai入门")
st.header("一级标题")
st.subheader("二级标题")

st.write("当前全球经济延续温和复苏但动能减弱，IMF预计2026年全球经济增长3.0%，地缘冲突、贸易碎片化等风险持续施压,中国经济则呈现“稳中有进、向新向优”态势。上半年GDP达69.6万亿元，同比增长4.7%，符合全年预期目标。物价温和回升，PPI结束41个月负增长。新动能加快壮大，制造业增加值增长13.3%，对经济增长贡献率超四成。IMF逆势将中国全年增长预期上调至4.6%。不过，国内仍面临“供强需弱”的结构性矛盾，消费复苏偏慢。总体看，中国经济在复杂环境中展现了较强韧性与潜力。")
st.image("./屏幕截图(1).png")
st.audio("./The truth that you leave（你离开的事实）.mp3")

st.logo("./logo.png")
student_a={
    "姓名":["llh","mys","lyy","lxx"],
    "年龄":["1","2","3","4"],
    "成绩":["90","89","80","78"]
}
st.table(student_a)
name = st.text_input("请输入姓名:")
st.write(f"你输入的姓名为：",name)
password = st.text_input("请输入密码:",type="password")
st.write(f"你输入的姓名为：",password)

g=st.radio("请确定性别",["男","女"])
st.write("性别为:",g)