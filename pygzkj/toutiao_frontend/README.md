# 头条前端（新闻分类展示）

基于 Vue3 + Vite + axios，展示后端 `GET /api/news/categories` 返回的新闻分类。

## 目录结构

```
toutiao_frontend/
├── index.html
├── vite.config.js          # Vite 配置（含 /api 代理）
├── package.json
└── src/
    ├── main.js             # 入口
    ├── App.vue             # 根组件
    ├── api/
    │   ├── request.js      # axios 封装（拦截器、错误处理）
    │   └── news.js         # 新闻相关接口
    ├── components/
    │   └── CategoryCard.vue# 单个分类卡片
    └── views/
        └── NewsCategories.vue # 分类页（loading / 错误 / 空 / 列表）
```

## 运行

```bash
cd toutiao_frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173 。

## 跨域说明

开发环境通过 Vite 的 `server.proxy` 把 `/api` 开头的请求转发到
`http://localhost:8000`，前端代码里 axios 的 `baseURL` 是 `/api`，
浏览器始终同源访问，因此不存在跨域问题。

同时后端 `main.py` 已添加 `CORSMiddleware`，允许 `http://localhost:5173` 跨域访问，
以兼容前端独立部署（不走代理）的场景。

## 后端接口约定

```
GET /api/news/categories
=> { code: 200, msg: "获取新闻分类成功success", data: [ { id, name, sort_order }, ... ] }
```

响应拦截器约定：`code === 200` 视为成功并直接返回 `data`；否则抛出 `msg` 作为错误信息。
