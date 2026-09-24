# 数据库模式来源

- `backend/app/models/entities.py` 是 ORM 与字段约束的唯一事实来源。
- `sql/init.sql` 用于首次部署的 MySQL 基线初始化，主键和外键统一使用 `BIGINT`。
- 生产环境后续结构变更应使用 Alembic 生成迁移，不直接手改线上表；基线脚本与 ORM 的差异必须通过模型测试或迁移审查消除。
- SQLite 仅用于本地和测试，ORM 的 `ID_TYPE` 会自动映射为 SQLite `INTEGER`，保证自动增主键行为。

