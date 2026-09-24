# 智能招聘系统后端

## 初始化

1. 创建虚拟环境并安装依赖：`python -m venv .venv`，然后执行 `.\.venv\Scripts\pip install -r requirements.txt`。
2. 复制 `.env.example` 为 `.env`，生产环境必须注入 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET_KEY`；本机首次启动如需管理员，请显式设置强 `INITIAL_ADMIN_PASSWORD`。
3. 生产数据库执行 `sql/init.sql`。本机联调可设置 `DATABASE_URL=sqlite:///./recruit_local.db`、`APP_ENV=development`、`REDIS_REQUIRED=false`、`REDIS_FALLBACK_ENABLED=true`。
4. 启动：`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`。
5. 测试：`pytest`。测试使用临时 SQLite 和进程内 Redis 等价实现，不依赖外部服务。

## 大模型配置

- 通用配置 `LLM_*` 的优先级最高。显式配置 `LLM_API_KEY` 时，后端不会切换到 DeepSeek。
- 未配置通用 `LLM_API_KEY` 时，如果环境中存在 `DEEPSEEK_API_KEY`，后端自动使用 `DEEPSEEK_MODEL` 和 `DEEPSEEK_BASE_URL` 构建 LangChain 兼容模型，默认值分别为 `deepseek-chat`、`https://api.deepseek.com/v1`。
- DeepSeek 聊天密钥不会用于 embedding。只有配置 `EMBEDDING_MODEL` 和对应的 `EMBEDDING_API_KEY` 后才启用嵌入；如嵌入服务不是 OpenAI 默认地址，还需配置 `EMBEDDING_BASE_URL`。
- `.env` 或系统环境变量在进程启动时读取。修改后需要重启 uvicorn 服务，运行中的进程不会自动获取新的密钥或地址。

## 分层

- `routers`：参数校验、鉴权依赖、统一响应。
- `services`：业务规则、事务编排、AI 链路调用。
- `dao`：SQLAlchemy 查询与持久化。
- `models`、`schemas`：数据库模型与 Pydantic v2 契约。
- `security`：JWT、密码、角色权限、Redis 限流。
- `ai`：LangChain Provider、固定系统提示词、Prompt 注入边界、本地降级。

## 异步任务

`POST /resumes/{id}/parse`、`POST /ai/matches`、`POST /ai/interview-questions` 返回 `202` 和 `task_no`，客户端使用 `GET /ai/tasks/{task_no}` 轮询结果。面试题统一使用 `GET /interview-questions` 分页查询，指定面试的题目继续使用 `GET /interviews/{id}/questions`。

当前使用 FastAPI `BackgroundTasks`，仅适合单机 MVP：任务与 Web 进程共享生命周期，进程重启会中断任务。启动时只会把超过 `AI_STALE_TASK_SECONDS` 安全时限的 `PENDING/RUNNING` 任务标记为 `FAILED`，不会终止可能仍健康的任务。生产环境应接入 Celery、Arq、RQ 或消息队列，并使用心跳、租约续期、幂等键和死信队列实现持久化恢复与自动重试。
