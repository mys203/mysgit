# FastAPI + LangChain 智能招聘系统

这是一个前后端分离的智能招聘管理后台 MVP，覆盖岗位、简历、候选人、人岗匹配、面试题和面试流程。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、TailwindCSS
- 后端：FastAPI、Pydantic v2、SQLAlchemy 2.x、MySQL、Redis、LangChain
- 测试：pytest、Vitest

## 目录

```text
frontend/   Vue 3 管理后台
backend/    FastAPI 后端、数据库脚本和测试
.venv/      本机后端虚拟环境
```

## 已实现能力

- JWT 登录、刷新、退出和会话撤销
- RBAC 角色与权限控制
- 岗位、岗位分类、部门和用户管理
- 简历上传、文本提取、解析任务和人工确认
- 候选人、应聘流程和阶段管理
- 人岗匹配、匹配评分和依据展示
- AI 招聘问答，支持岗位/候选人上下文、连续会话、SSE 流式输出和引用依据
- 面试题生成、审核和面试反馈
- Redis 会话、黑名单、限流、缓存和 AI 任务状态
- 未配置大模型时使用明确标记的本地降级能力

## 本地启动

推荐使用根目录脚本。脚本会自动启动 Redis、后端和前端；如果端口已经占用，会复用已有服务。

```powershell
.\scripts\start-dev.ps1 -AdminPassword "请设置至少12位的强密码"
```

启动地址：

- 管理后台：http://127.0.0.1:5173
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

开发模式默认使用 SQLite：

```text
backend/recruit_local.db
```

生产环境必须通过环境变量注入 MySQL、Redis 和随机 JWT 密钥，禁止使用示例值。

## 测试

后端：

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests -q
```

前端：

```powershell
cd frontend
npm run test:unit
npm run type-check
npm run lint
npm run build
```

## 大模型配置

项目会自动识别本机的 `DEEPSEEK_API_KEY`，并使用 DeepSeek 的 OpenAI 兼容接口：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

通用配置 `LLM_API_KEY`、`LLM_MODEL`、`LLM_BASE_URL` 的优先级更高。Embedding 使用独立的
`EMBEDDING_API_KEY` 和 `EMBEDDING_BASE_URL`，不会把 DeepSeek 对话密钥发送给未知嵌入服务。

修改环境变量后需要重启后端。未配置大模型时，系统会使用本地规则和确定性算法生成可演示结果，
并在响应中标记降级状态。
