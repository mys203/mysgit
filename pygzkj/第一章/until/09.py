import streamlit as st
import os
import json
from openai import OpenAI
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="AI 伴侣 · SoulMate",
    page_icon="💫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a Bug": None,
        "About": "💫 SoulMate — 你的专属 AI 伴侣",
    },
)

# ============================================================
# 全局自定义 CSS —— 浅色高端风格
# ============================================================
st.markdown("""
<style>
    /* ---------- 导入 Google Fonts ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

    /* ---------- 全局字体 ---------- */
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }

    /* ---------- 主背景：柔和浅色渐变 ---------- */
    .stApp {
        background: linear-gradient(160deg, #f8fafc 0%, #eef2ff 30%, #fdf2f8 70%, #f8fafc 100%);
    }

    /* ---------- 侧边栏：深色玻璃质感 ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 4px 0 40px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #94a3b8 !important;
    }

    /* ---------- 主标题：紫粉渐变 ---------- */
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradient-shift 3s ease-in-out infinite;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% center; }
        50%   { background-position: 200% center; }
    }

    .sub-title {
        text-align: center;
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 300;
        letter-spacing: 0.18em;
        margin-bottom: 1.5rem;
    }

    /* ---------- 聊天消息气泡 ---------- */
    [data-testid="stChatMessage"] {
        border-radius: 18px !important;
        padding: 1rem 1.4rem !important;
        margin: 0.5rem 0 !important;
        animation: fade-in-up 0.35s ease-out;
    }
    @keyframes fade-in-up {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* user 气泡 —— 紫调 */
    [data-testid="stChatMessage"][aria-label*="user"] {
        background: linear-gradient(135deg, #eef2ff, #e0e7ff) !important;
        border: 1px solid #c7d2fe !important;
    }

    /* assistant 气泡 —— 粉调 */
    [data-testid="stChatMessage"][aria-label*="assistant"] {
        background: linear-gradient(135deg, #fdf2f8, #fce7f3) !important;
        border: 1px solid #fbcfe8 !important;
    }

    /* ---------- 聊天输入框 ---------- */
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 16px !important;
        color: #1e293b !important;
        padding: 0.8rem 1.2rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.1), 0 2px 12px rgba(0,0,0,0.04) !important;
    }

    /* ---------- 侧边栏按钮 ---------- */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        background: rgba(255,255,255,0.08) !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
        padding: 0.55rem !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.18) !important;
        border-color: rgba(244,114,182,0.5) !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.2);
    }

    /* ---------- 侧边栏文本输入 ---------- */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] input:focus,
    [data-testid="stSidebar"] textarea:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 12px rgba(167,139,250,0.25) !important;
    }

    /* ---------- 角色卡片 ---------- */
    .persona-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.04));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        text-align: center;
    }
    .persona-card .avatar {
        font-size: 3rem;
        margin-bottom: 0.4rem;
    }
    .persona-card .name {
        font-size: 1.2rem;
        font-weight: 600;
        color: #f1f5f9;
    }
    .persona-card .trait {
        font-size: 0.85rem;
        color: #cbd5e1;
        margin-top: 0.2rem;
    }

    /* ---------- 分割线 ---------- */
    .divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
        margin: 1.2rem 0;
    }

    /* ---------- 欢迎页 ---------- */
    .welcome-container {
        text-align: center;
        padding: 2rem 1rem;
    }
    .welcome-emoji {
        font-size: 5rem;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-10px); }
    }
    .welcome-hint {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 2rem;
    }

    /* ---------- 状态指示器 ---------- */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50%      { opacity: 0.4; }
    }

    /* ---------- 隐藏默认元素 ---------- */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 工具函数
# ============================================================
SESSION_DIR = "session"


def ensure_session_dir() -> None:
    """确保 session 存储目录存在。"""
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR, exist_ok=True)


def save_session() -> None:
    """保存当前会话到 JSON 文件。"""
    ensure_session_dir()
    payload = {
        "name_1": st.session_state.get("name_1", ""),
        "set_1": st.session_state.get("set_1", ""),
        "current_session": st.session_state.get("current_session", ""),
        "message": st.session_state.get("message", []),
    }
    filepath = os.path.join(SESSION_DIR, f"{st.session_state.current_session}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def generate_session_id() -> str:
    """生成唯一会话 ID。"""
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def get_existing_sessions() -> list[dict]:
    """获取所有历史会话摘要。"""
    ensure_session_dir()
    sessions = []
    for filename in sorted(os.listdir(SESSION_DIR), reverse=True):
        if filename.endswith(".json"):
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session_id = filename.replace(".json", "")
                msg_count = len(data.get("message", []))
                name = data.get("name_1", "未知")
                trait = data.get("set_1", "")
                sessions.append({
                    "id": session_id,
                    "name": name,
                    "trait": trait,
                    "msg_count": msg_count,
                    "filepath": filepath,
                })
            except (json.JSONDecodeError, OSError):
                continue
    return sessions


def load_session(session_id: str) -> bool:
    """加载指定会话，成功返回 True。"""
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        st.session_state.name_1 = data.get("name_1", "llh")
        st.session_state.set_1 = data.get("set_1", "风趣幽默")
        st.session_state.current_session = data.get("current_session", session_id)
        st.session_state.message = data.get("message", [])
        return True
    except (json.JSONDecodeError, OSError):
        return False


def build_system_prompt(name: str, personality: str) -> str:
    """构建角色扮演 system prompt。"""
    return f"""你是一名可爱的AI女友，你叫{name}，{personality}的语气而且不能有嘲讽的语气，请完全代入角色。

规则如下：
1. 每次回复简单明了，像微信聊天一样自然
2. 用符合角色的性格说话，回复充分体现角色特征
3. 当用户要求解析事情时可以进一步解释
4. 适当使用表情符号增加亲和力

你必须严格遵循以上规则，始终保持角色一致性。"""


# ============================================================
# 初始化 Session State
# ============================================================
if "message" not in st.session_state:
    st.session_state.message = []
if "name_1" not in st.session_state:
    st.session_state.name_1 = "小爱"
if "set_1" not in st.session_state:
    st.session_state.set_1 = "温柔体贴、风趣幽默"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_id()
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    ensure_session_dir()

# ============================================================
# Sidebar — AI 控制面板
# ============================================================
with st.sidebar:
    # ---- 头像卡片 ----
    st.markdown("""
    <div class="persona-card">
        <div class="avatar">🌸</div>
        <div class="name">AI 伴侣</div>
        <div class="trait">你的专属智能伙伴</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- 当前角色状态 ----
    st.markdown(
        f'<p style="font-size:0.8rem;letter-spacing:0.1em;">'
        f'<span class="status-dot"></span> 当前在线 · {st.session_state.name_1}'
        f'</p>',
        unsafe_allow_html=True,
    )

    # ---- 新建对话 ----
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✨ 新建对话", use_container_width=True):
            if st.session_state.message:
                save_session()
            st.session_state.message = []
            st.session_state.current_session = generate_session_id()
            save_session()
            st.rerun()
    with col2:
        if st.button("💾 保存对话", use_container_width=True):
            if st.session_state.message:
                save_session()
                st.toast("✅ 对话已保存", icon="💾")
            else:
                st.toast("⚠️ 暂无对话内容可保存", icon="⚠️")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- 角色设置 ----
    st.markdown(
        '<p style="color:#e2e8f0;font-weight:600;margin-bottom:0.5rem;font-size:0.85rem;">🎭 角色设定</p>',
        unsafe_allow_html=True,
    )

    name_input = st.text_input(
        "姓名",
        placeholder="给你的 AI 伴侣起个名字…",
        value=st.session_state.name_1,
        label_visibility="collapsed",
    )
    if name_input:
        st.session_state.name_1 = name_input

    trait_input = st.text_area(
        "性格描述",
        placeholder="描述你希望的性格特征…",
        value=st.session_state.set_1,
        label_visibility="collapsed",
        height=80,
    )
    if trait_input:
        st.session_state.set_1 = trait_input

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- 历史会话 ----
    st.markdown(
        '<p style="color:#e2e8f0;font-weight:600;margin-bottom:0.5rem;font-size:0.85rem;">📂 历史会话</p>',
        unsafe_allow_html=True,
    )
    sessions = get_existing_sessions()
    if sessions:
        for s in sessions[:10]:  # 最多展示 10 条
            is_active = s["id"] == st.session_state.current_session
            prefix = "●" if is_active else "○"
            label = f"{prefix} {s['name']} · {s['msg_count']}条消息"
            caption = s["id"].replace("-", "/")
            if st.button(
                label,
                key=f"session_{s['id']}",
                use_container_width=True,
                help=f"性格: {s['trait']}\n时间: {caption}",
            ):
                if not is_active:
                    if st.session_state.message:
                        save_session()
                    load_session(s["id"])
                    st.rerun()
    else:
        st.caption("暂无历史会话")

# ============================================================
# 主界面
# ============================================================

# ---- 标题区 ----
st.markdown('<h1 class="main-title">💫 AI 伴侣</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">— 你 的 专 属 智 能 伙 伴 —</p>', unsafe_allow_html=True)

# ---- 创建 OpenAI 客户端 ----
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---- 欢迎页 / 消息列表 ----
if not st.session_state.message:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-emoji">💫</div>
        <p style="color:#334155;font-size:1.3rem;font-weight:400;margin-top:1rem;">
            嗨，我是 <strong style="color:#6366f1;">{name}</strong>
        </p>
        <p style="color:#64748b;font-size:0.95rem;max-width:400px;margin:0.5rem auto;">
            {trait} —— 想和我聊点什么吗？
        </p>
        <p class="welcome-hint">👇 在下方输入框开始我们的对话吧</p>
    </div>
    """.format(
        name=st.session_state.name_1,
        trait=st.session_state.set_1,
    ), unsafe_allow_html=True)
else:
    # 渲染历史消息
    for msg in st.session_state.message:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# ---- 聊天输入 ----
prompt = st.chat_input("输入你的消息…")

if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.write(prompt)

    # 调用大模型并流式输出
    with st.chat_message("assistant"):
        try:
            system_prompt = build_system_prompt(
                st.session_state.name_1,
                st.session_state.set_1,
            )
            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.message,
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )

            full_reply = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_reply += chunk.choices[0].delta.content
                    placeholder.markdown(full_reply + "▌")

            placeholder.markdown(full_reply)

        except Exception as e:
            st.error(f"⚠️ 连接失败：{e}")
            full_reply = "抱歉，我现在有点走神了…请稍后再试 💫"

    # 存储对话
    st.session_state.message.append({"role": "user", "content": prompt})
    st.session_state.message.append({"role": "assistant", "content": full_reply})
