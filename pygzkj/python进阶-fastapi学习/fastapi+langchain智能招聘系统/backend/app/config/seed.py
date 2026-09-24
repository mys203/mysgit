from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.settings import settings
from app.dao.repositories import (
    AIChatMessageDAO,
    AITaskDAO,
    PermissionDAO,
    RoleDAO,
    RolePermissionDAO,
    UserDAO,
)
from app.models.entities import SysPermission, SysRole, SysRolePermission
from app.security.password import hash_password

ROLE_DEFINITIONS = {
    "ADMIN": "系统管理员",
    "HR_MANAGER": "招聘负责人",
    "RECRUITER": "招聘专员",
    "INTERVIEWER": "面试官",
    "VIEWER": "只读用户",
}

PERMISSIONS = [
    ("system:manage", "系统管理", "system", "manage"),
    ("jobs:read", "查看岗位", "jobs", "read"),
    ("jobs:write", "管理岗位", "jobs", "write"),
    ("resumes:read", "查看简历", "resumes", "read"),
    ("resumes:write", "管理简历", "resumes", "write"),
    ("candidates:read", "查看候选人", "candidates", "read"),
    ("candidates:write", "管理候选人", "candidates", "write"),
    ("applications:read", "查看应聘记录", "applications", "read"),
    ("applications:write", "管理应聘记录", "applications", "write"),
    ("ai:execute", "执行 AI 能力", "ai", "execute"),
    ("interviews:read", "查看面试", "interviews", "read"),
    ("interviews:write", "管理面试", "interviews", "write"),
    ("interviews:schedule", "安排面试", "interviews", "schedule"),
    ("interviews:manage", "管理面试流程", "interviews", "manage"),
    ("logs:read", "查看操作日志", "logs", "read"),
]

ROLE_PERMISSIONS = {
    "ADMIN": [item[0] for item in PERMISSIONS],
    "HR_MANAGER": [item[0] for item in PERMISSIONS if item[0] != "system:manage"],
    "RECRUITER": [
        "jobs:read",
        "jobs:write",
        "resumes:read",
        "resumes:write",
        "candidates:read",
        "candidates:write",
        "applications:read",
        "applications:write",
        "ai:execute",
        "interviews:read",
        "interviews:write",
        "interviews:schedule",
    ],
    "INTERVIEWER": ["interviews:read", "interviews:write", "candidates:read"],
    "VIEWER": ["jobs:read", "candidates:read", "applications:read"],
}


def seed_system_data(db: Session) -> None:
    roles = RoleDAO(db)
    permissions = PermissionDAO(db)
    role_permissions = RolePermissionDAO(db)
    for code, name in ROLE_DEFINITIONS.items():
        if not roles.get_by_code(code):
            roles.create({"code": code, "name": name, "status": "ACTIVE"})
    permission_map: dict[str, int] = {}
    for code, name, resource, action in PERMISSIONS:
        item = permissions.first(code=code)
        if not item:
            item = permissions.create(
                {"code": code, "name": name, "resource": resource, "action": action}
            )
        permission_map[code] = item.id
    role_map = {item.code: item.id for item in roles.list_all(limit=100)}
    existing = {
        (row.role_id, row.permission_id)
        for row in db.scalars(select(SysRolePermission)).all()
    }
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
            pair = (role_map[role_code], permission_map[permission_code])
            if pair not in existing:
                role_permissions.create(
                    {"role_id": pair[0], "permission_id": pair[1]}
                )

    if settings.initial_admin_username and settings.initial_admin_password:
        users = UserDAO(db)
        username = settings.initial_admin_username.strip().lower()
        if not users.get_by_username(username):
            admin = users.create(
                {
                    "username": username,
                    "password_hash": hash_password(
                        settings.initial_admin_password.get_secret_value()
                    ),
                    "real_name": "系统管理员",
                    "status": "ACTIVE",
                }
            )
            users.replace_roles(admin.id, ["ADMIN"])


def initialize_seed_data() -> None:
    with SessionLocal() as db:
        seed_system_data(db)


def recover_incomplete_ai_tasks() -> int:
    with SessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=settings.ai_stale_task_seconds
        )
        recovered_tasks = AITaskDAO(db).fail_incomplete_tasks(
            "任务超过安全时限仍未完成，已标记失败；请重新提交，任务号不可复用。",
            cutoff,
        )
        recovered_messages = AIChatMessageDAO(db).fail_incomplete_assistants(
            "聊天回答超过安全时限仍未完成，已在服务启动时标记失败；可重新提问或重试。",
            cutoff,
        )
        return recovered_tasks + recovered_messages
