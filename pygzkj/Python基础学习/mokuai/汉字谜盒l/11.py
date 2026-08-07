import os
import uuid
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import httpx

app = FastAPI()

# ---------- 配置 ----------
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = 'https://api.deepseek.com/v1'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = (
    '你是一名可爱的AI女友，你叫小谜，温柔可爱的语气而且不能有嘲讽的语气，请完全代入角色\n'
    '规则如下：\n'
    '1.每次回复简单明了\n'
    '2.像微信聊天一样的\n'
    '3.用符合角色的性格说话\n'
    '4.回复内容充分体现角色特征\n'
    '5.当用户要求解析事情时候可以进一步解释\n'
    '你必须严格遵循上面规则'
)

# ---------- 会话存储：每个会话独立一个 JSON 文件 ----------
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
sessions: dict = {}


def _session_path(session_id: str) -> str:
    """返回某个会话的 JSON 文件路径。"""
    return os.path.join(SESSIONS_DIR, f'{session_id}.json')


def _save_session(session_id: str):
    """将单个会话写入独立的 JSON 文件。"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(_session_path(session_id), 'w', encoding='utf-8') as f:
        json.dump(sessions[session_id], f, ensure_ascii=False, indent=2)


def _load_sessions():
    """启动时从 sessions 文件夹恢复所有会话。"""
    global sessions
    if not os.path.isdir(SESSIONS_DIR):
        return
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions[data['id']] = data
            except (json.JSONDecodeError, IOError, KeyError):
                pass


# 启动时加载已有会话
_load_sessions()


def _new_session_dict(name: str = None) -> dict:
    sid = uuid.uuid4().hex[:8]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {
        'id': sid,
        'name': name or f'谜盒 {now}',
        'created_at': now,
        'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}],
    }


# ---------- 静态文件 ----------
@app.get('/style.css')
async def get_style():
    return FileResponse(os.path.join(BASE_DIR, 'style.css'))


@app.get('/main.js')
async def get_main_js():
    return FileResponse(os.path.join(BASE_DIR, 'main.js'))


@app.get('/')
async def root():
    return FileResponse(os.path.join(BASE_DIR, 'index.html'))


# ---------- 会话 API ----------
@app.get('/api/sessions')
async def list_sessions():
    result = []
    for s in sessions.values():
        result.append({
            'id': s['id'],
            'name': s['name'],
            'created_at': s['created_at'],
            'msg_count': len([m for m in s['messages'] if m['role'] != 'system']),
        })
    result.sort(key=lambda x: x['created_at'], reverse=True)
    return result


@app.post('/api/sessions')
async def create_session():
    s = _new_session_dict()
    sessions[s['id']] = s
    _save_session(s['id'])
    return {
        'id': s['id'],
        'name': s['name'],
        'created_at': s['created_at'],
        'messages': s['messages'],
    }


@app.get('/api/sessions/{session_id}')
async def get_session(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail='会话不存在')
    return s


@app.delete('/api/sessions/{session_id}')
async def delete_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail='会话不存在')
    del sessions[session_id]
    # 同时删除对应的 JSON 文件
    filepath = _session_path(session_id)
    if os.path.exists(filepath):
        os.remove(filepath)
    return {'ok': True}


@app.post('/api/sessions/{session_id}/start')
async def start_game(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail='会话不存在')

    if not DEEPSEEK_API_KEY:
        ai_reply = '嗨～我是小谜，你的AI女友！今天过得怎么样呀？💕'
    else:
        try:
            ai_reply = await _call_deepseek(s['messages'])
        except Exception as e:
            ai_reply = f'哎呀，我走神了…{str(e)}'

    s['messages'].append({'role': 'assistant', 'content': ai_reply})
    _save_session(session_id)
    return {'reply': ai_reply}


# ---------- 聊天 API ----------
@app.post('/api/chat/{session_id}')
async def chat(session_id: str, req: Request):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail='会话不存在')

    body = await req.json()
    user_msg = body.get('message', '').strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail='消息不能为空')

    sessions[session_id]['messages'].append({'role': 'user', 'content': user_msg})

    if not DEEPSEEK_API_KEY:
        ai_reply = _mock_reply(user_msg)
    else:
        try:
            ai_reply = await _call_deepseek(sessions[session_id]['messages'])
        except Exception as e:
            ai_reply = f'哎呀，我走神了…{str(e)}'

    sessions[session_id]['messages'].append({'role': 'assistant', 'content': ai_reply})
    _save_session(session_id)
    return {'reply': ai_reply}


async def _call_deepseek(messages: list) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f'{DEEPSEEK_BASE_URL}/chat/completions',
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': messages,
                'temperature': 0.8,
                'max_tokens': 2000,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']


def _mock_reply(user_msg: str) -> str:
    return f'收到你的消息啦～「{user_msg}」…我现在在离线模式，等我连上大脑再好好回复你哦 😘'


# ---------- 启动 ----------
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
