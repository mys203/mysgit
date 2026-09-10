# 管理后台‑主 Agent 协调规范

## 1. 任务分发原则
"""
- 凡是涉及 Frontend 角色的代码改动 → 必须 spawn Frontend 子 Agent，主 Agent 不得直接修改 /frontend 下代码
- 凡是涉及 Backend 角色的代码改动 → 必须 spawn Backend 子 Agent，主 Agent 不得直接修改 /backend 下代码
- 主 Agent 的职责是：协调流程、集成验证、修复配置文件、修复不归属于任何子 Agent 的问题
- 违反此原则视为流程违规
"""
## 2. 质量门禁与自动修复循环

### 2.1 循环流程
"""
Planner（出规划） → Frontend + Backend（并行开发）
→ Reviewer（质量审查）
→ 如果存在 P1/P2 问题
 → 对应子 Agent 修复（Frontend 修前端问题，Backend 修后端问题）
 → Reviewer 重新审查
  → 重复直到 P1 清零、P2 ≤ 2 或达到最大循环次数
→ 通过后进入集成验证
→ 集成验证（主 Agent 执行）
 → 启动前后端服务、联调测试、检查核心流程
 → 如果发现集成问题 → 回退给对应子 Agent 修复 → 回到 Reviewer
→ 通过后结束
"""
### 2.2 回退规则

- **P1问题**：必须修复，阻塞发布
- **P2问题**：建议修复，同一模块循环上限3次后自动降级为建议项
- **P3问题**：记录到待办清单，不阻塞当前循环
- 子Agent修复时只修改自己负责的目录（Frontend只改 /frontend，Backend只改 /backend）
- 修复完成后必须注明修改的文件列表，方便 Reviewer 增量审查

### 2.3 集成验证
"""
代码审查通过后，由主Agent执行集成验证，检查以下内容：

- 前后端启动是否正常（端口、数据库连接、编译）
- 前后端联调是否正常（API代理、CORS、路由）
- 核心流程是否可用（登录、列表加载、数据提交）
- 部署配置是否正确（vite.config.ts代理、后端config.yaml、.env文件）
- 运行环境是否兼容（数据库版本、sql_mode、驱动）

集成验证发现的问题按同等级别回退到修复循环中处理。
"""

### 2.4 人工介入条件
"""
- 同一问题反复出现3次仍未解决 → 标记为需人工介入，跳出循环
- 跨模块/跨目录的架构问题 → 通知主Agent人工决策
- 集成验证发现的环境/配置问题，子Agent无法独立解决 → 主Agent人工处理
"""

## 3. 编码规范（所有子Agent必须遵守）

### 3.1 中文字符编码
- 所有源码文件（.vue、.ts、.js、.css、.html、.go、.yaml等）中的中文文本**必须保存为实际UTF‑8中文字符**，禁止使用Unicode转义序列（\uXXXX）
- 写入文件时，必须确保非ASCII字符原样保持，不被转义为\uXXXX序列
- 所有文件必须使用UTF‑8编码，不含BOM

### 3.2 文本用于界面展示
模板和组件中的中文文本（label、placeholder、message 等）必须是可读的中文字符，而非编码后的转义序列。示例：

<!-- 正确 -->
<el-form-item label="部门名称" prop="name">
  <el-input placeholder="请输入部门名称" />
</el-form-item>

<!-- 错误 -->
<el-form-item label="\u90e8\u95e8\u540d\u79f0" prop="name">
  <el-input placeholder="\u8bf7\u8f93\u5165\u90e8\u95e8\u540d\u79f0" />
</el-form-item>

### 3.3 Reviewer 审查项
Reviewer 在审查代码时，必须检查源码中是否存在 `\uXXXX` 形式的 Unicode 转义序列，将其标记为 P1 问题。
