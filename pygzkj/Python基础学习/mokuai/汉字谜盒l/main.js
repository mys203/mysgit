// ========== DOM 引用 ==========
const sessionListEl = document.getElementById("sessionList");
const newSessionBtn = document.getElementById("newSessionBtn");
const chatArea = document.getElementById("chatArea");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const sessionNameEl = document.getElementById("sessionName");

// ========== 状态 ==========
let currentSessionId = null;   // 当前选中会话 ID
let sessionsCache = [];        // 会话摘要列表
let isLoading = false;         // 是否正在等待 AI 回复

// ========== 初始化 ==========
async function init() {
    await loadSessionList();
    bindEvents();
}

// ========== 事件绑定 ==========
function bindEvents() {
    newSessionBtn.addEventListener("click", createSession);
    sendBtn.addEventListener("click", sendMessage);
    msgInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// ========== 会话列表 API ==========
async function loadSessionList() {
    try {
        const res = await fetch("/api/sessions");
        sessionsCache = await res.json();
        renderSessionList();
    } catch (err) {
        console.error("加载会话列表失败:", err);
    }
}

function renderSessionList() {
    sessionListEl.innerHTML = "";
    if (sessionsCache.length === 0) {
        sessionListEl.innerHTML = '<li style="color:#666;font-size:13px;padding:8px;">暂无会话</li>';
        return;
    }
    sessionsCache.forEach((s) => {
        const li = document.createElement("li");
        li.className = "session-item";
        if (s.id === currentSessionId) li.classList.add("active");

        li.innerHTML = `
            <span class="session-item-name" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
            <button class="session-item-delete" data-id="${s.id}" title="删除">×</button>
        `;

        // 点击加载会话
        li.querySelector(".session-item-name").addEventListener("click", () => loadSession(s.id));
        // 删除按钮
        li.querySelector(".session-item-delete").addEventListener("click", (e) => {
            e.stopPropagation();
            deleteSession(s.id);
        });

        sessionListEl.appendChild(li);
    });
}

// ========== 会话 CRUD ==========
async function createSession() {
    try {
        const res = await fetch("/api/sessions", { method: "POST" });
        const s = await res.json();
        currentSessionId = s.id;
        await loadSessionList();
        await loadSessionIntoChat(s.id);
        enableInput();
    } catch (err) {
        console.error("创建会话失败:", err);
    }
}

async function loadSession(sessionId) {
    if (currentSessionId === sessionId) return; // 已经是当前会话
    currentSessionId = sessionId;
    renderSessionList();
    await loadSessionIntoChat(sessionId);
    enableInput();
}

async function deleteSession(sessionId) {
    if (!confirm("确定删除这个会话吗？")) return;
    try {
        await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            chatArea.innerHTML = '<div class="empty-hint">👋 欢迎来到汉字谜盒！<br>点击左侧「新建游戏」开始猜字谜吧～</div>';
            sessionNameEl.textContent = "— 选择一个会话或新建";
            disableInput();
        }
        await loadSessionList();
    } catch (err) {
        console.error("删除会话失败:", err);
    }
}

async function loadSessionIntoChat(sessionId) {
    try {
        const res = await fetch(`/api/sessions/${sessionId}`);
        const s = await res.json();
        sessionNameEl.textContent = `— ${escapeHtml(s.name)}`;
        renderMessages(s.messages);
    } catch (err) {
        console.error("加载会话失败:", err);
    }
}

// ========== 消息渲染 ==========
function renderMessages(messages) {
    chatArea.innerHTML = "";
    const displayMsgs = messages.filter((m) => m.role !== "system");
    if (displayMsgs.length === 0) {
        chatArea.innerHTML = '<div class="empty-hint">🎯 新游戏开始！<br>AI 正在出题中…</div>';
        // 自动触发 AI 出第一道题
        sendFirstMessage();
        return;
    }
    displayMsgs.forEach((m) => {
        appendMessageBubble(m.role, m.content);
    });
    scrollToBottom();
}

function appendMessageBubble(role, content) {
    const div = document.createElement("div");
    div.className = `msg-bubble ${role === "user" ? "msg-user" : "msg-ai"}`;
    // 简单 Markdown 换行处理
    div.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");
    chatArea.appendChild(div);
    scrollToBottom();
}

function appendLoading() {
    const div = document.createElement("div");
    div.className = "msg-loading";
    div.id = "loadingBubble";
    div.textContent = "🤔 AI 正在思考…";
    chatArea.appendChild(div);
    scrollToBottom();
}

function removeLoading() {
    const el = document.getElementById("loadingBubble");
    if (el) el.remove();
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

// ========== 开局：AI 自动出第一道题 ==========
async function sendFirstMessage() {
    if (isLoading) return;
    isLoading = true;
    disableInput();
    appendLoading();
    try {
        const res = await fetch(`/api/sessions/${currentSessionId}/start`, {
            method: "POST",
        });
        const data = await res.json();
        removeLoading();
        appendMessageBubble("assistant", data.reply);
        resetEmptyHint();
    } catch (err) {
        removeLoading();
        appendMessageBubble("assistant", "网络错误，请重试 😢");
    } finally {
        isLoading = false;
        enableInput();
        msgInput.focus();
    }
}

async function sendMessage() {
    if (isLoading || !currentSessionId) return;
    const text = msgInput.value.trim();
    if (!text) return;

    // 显示用户消息
    appendMessageBubble("user", text);
    msgInput.value = "";
    resetEmptyHint();

    isLoading = true;
    disableInput();
    appendLoading();

    try {
        const res = await fetch(`/api/chat/${currentSessionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "请求失败");
        }
        const data = await res.json();
        removeLoading();
        appendMessageBubble("assistant", data.reply);
    } catch (err) {
        removeLoading();
        appendMessageBubble("assistant", `😢 出错了：${err.message}`);
    } finally {
        isLoading = false;
        enableInput();
        msgInput.focus();
    }
}

// ========== 工具函数 ==========
function enableInput() {
    msgInput.disabled = false;
    sendBtn.disabled = false;
    msgInput.placeholder = "输入你的答案…";
}

function disableInput() {
    msgInput.disabled = true;
    sendBtn.disabled = true;
    msgInput.placeholder = "AI 正在思考…";
}

function resetEmptyHint() {
    // 移除空状态提示（如果有的话）
    const hint = chatArea.querySelector(".empty-hint");
    if (hint) hint.remove();
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ========== 启动 ==========
init();
