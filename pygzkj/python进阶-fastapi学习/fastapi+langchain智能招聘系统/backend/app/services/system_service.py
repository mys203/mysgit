from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.dao.repositories import DepartmentDAO, JobCategoryDAO, RoleDAO, UserDAO
from app.schemas.system import (
    CategoryCreate,
    CategoryUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from app.security.dependencies import UserPrincipal
from app.security.password import hash_password
from app.security.sessions import bump_session_version
from app.services.helpers import model_dict, record_operation


class SystemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserDAO(db)
        self.roles = RoleDAO(db)
        self.departments = DepartmentDAO(db)
        self.categories = JobCategoryDAO(db)

    def list_users(self, page: int, page_size: int, search: str | None, status: str | None):
        filters: dict[str, Any] = {"is_deleted": False}
        if status:
            filters["status"] = status
        rows, total = self.users.paginate(
            page, page_size, filters=filters, search=search,
            search_fields=("username", "real_name", "email"),
        )
        items = []
        for user in rows:
            item = model_dict(user, {"password_hash", "is_deleted"})
            item["roles"] = self.users.get_roles(user.id)
            items.append(item)
        return items, total

    def user_options(
        self,
        search: str | None = None,
        role_code: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self.users.list_options(search=search, role_code=role_code, limit=limit)
        return [
            {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "department_id": user.department_id,
                "roles": self.users.get_roles(user.id),
            }
            for user in rows
        ]

    def department_options(
        self, search: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        rows = self.departments.list_options(search=search, limit=limit)
        return [
            {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "parent_id": department.parent_id,
            }
            for department in rows
        ]

    def get_user(self, user_id: int) -> dict[str, Any]:
        user = self.users.get(user_id)
        if not user or user.is_deleted:
            raise NotFoundError("用户不存在")
        item = model_dict(user, {"password_hash", "is_deleted"})
        item["roles"] = self.users.get_roles(user.id)
        return item

    def create_user(self, payload: UserCreate, current: UserPrincipal) -> dict[str, Any]:
        if self.users.get_by_username(payload.username):
            raise ConflictError("用户名已存在")
        values = payload.model_dump(exclude={"password", "role_codes"})
        values["password_hash"] = hash_password(payload.password)
        user = self.users.create(values)
        self.users.replace_roles(user.id, payload.role_codes)
        record_operation(
            self.db,
            current,
            method="POST",
            path="/api/v1/users",
            action="CREATE",
            resource_type="user",
            resource_id=user.id,
        )
        return self.get_user(user.id)

    def update_user(
        self, user_id: int, payload: UserUpdate, current: UserPrincipal
    ) -> dict[str, Any]:
        user = self.users.get(user_id)
        if not user or user.is_deleted:
            raise NotFoundError("用户不存在")
        existing_roles = self.users.get_roles(user.id)
        resulting_roles = (
            payload.role_codes
            if payload.role_codes is not None
            else existing_roles
        )
        resulting_status = (
            payload.status
            if "status" in payload.model_fields_set and payload.status is not None
            else user.status
        )
        if user.id == current.id:
            if resulting_status != "ACTIVE":
                raise ConflictError("不能停用当前登录用户")
            if "ADMIN" in existing_roles and "ADMIN" not in resulting_roles:
                raise ConflictError("不能移除当前登录用户的管理员角色")
        self._ensure_active_admin_survives(
            user,
            existing_roles,
            resulting_status,
            resulting_roles,
        )
        values = payload.model_dump(exclude_unset=True, exclude={"password", "role_codes"})
        password_changed = bool(payload.password)
        if payload.password:
            values["password_hash"] = hash_password(payload.password)
        if values:
            self.users.update(user, values)
        if payload.role_codes is not None:
            self.users.replace_roles(user.id, payload.role_codes)
        if password_changed:
            bump_session_version(user.id)
        record_operation(
            self.db,
            current,
            method="PATCH",
            path=f"/api/v1/users/{user_id}",
            action="UPDATE",
            resource_type="user",
            resource_id=user_id,
        )
        return self.get_user(user_id)

    def delete_user(self, user_id: int, current: UserPrincipal) -> None:
        user = self.users.get(user_id)
        if not user or user.is_deleted:
            raise NotFoundError("用户不存在")
        if user.id == current.id:
            raise ConflictError("不能删除当前登录用户")
        existing_roles = self.users.get_roles(user.id)
        self._ensure_active_admin_survives(
            user,
            existing_roles,
            "INACTIVE",
            existing_roles,
        )
        self.users.update(user, {"is_deleted": True, "status": "INACTIVE"})
        record_operation(
            self.db,
            current,
            method="DELETE",
            path=f"/api/v1/users/{user_id}",
            action="DELETE",
            resource_type="user",
            resource_id=user_id,
        )

    def list_roles(self, page: int, page_size: int):
        return self.roles.paginate(page, page_size)

    def create_role(self, payload: RoleCreate, current: UserPrincipal):
        if self.roles.get_by_code(payload.code):
            raise ConflictError("角色编码已存在")
        role = self.roles.create(payload.model_dump())
        record_operation(
            self.db,
            current,
            method="POST",
            path="/api/v1/roles",
            action="CREATE",
            resource_type="role",
            resource_id=role.id,
        )
        return role

    def update_role(self, role_id: int, payload: RoleUpdate, current: UserPrincipal):
        role = self.roles.get(role_id)
        if not role:
            raise NotFoundError("角色不存在")
        if role.code == "ADMIN" and payload.status == "INACTIVE":
            raise ConflictError("不能停用管理员角色，系统必须保留至少一名有效管理员")
        result = self.roles.update(role, payload.model_dump(exclude_unset=True))
        record_operation(
            self.db,
            current,
            method="PATCH",
            path=f"/api/v1/roles/{role_id}",
            action="UPDATE",
            resource_type="role",
            resource_id=role_id,
        )
        return result

    def delete_role(self, role_id: int, current: UserPrincipal) -> None:
        role = self.roles.get(role_id)
        if not role:
            raise NotFoundError("角色不存在")
        if role.code == "ADMIN":
            raise ConflictError("管理员角色不可删除")
        self.roles.delete(role)
        record_operation(
            self.db,
            current,
            method="DELETE",
            path=f"/api/v1/roles/{role_id}",
            action="DELETE",
            resource_type="role",
            resource_id=role_id,
        )

    def _ensure_active_admin_survives(
        self,
        user,
        existing_roles: list[str],
        resulting_status: str,
        resulting_roles: list[str],
    ) -> None:
        currently_active_admin = (
            user.status == "ACTIVE"
            and not user.is_deleted
            and "ADMIN" in existing_roles
        )
        remains_active_admin = (
            resulting_status == "ACTIVE" and "ADMIN" in resulting_roles
        )
        if not currently_active_admin or remains_active_admin:
            return
        if self.users.count_active_admins(exclude_user_id=user.id) < 1:
            raise ConflictError("系统必须至少保留一名启用状态的管理员")

    def list_departments(self, page: int, page_size: int):
        return self.departments.paginate(page, page_size, filters={"is_deleted": False})

    def create_department(self, payload: DepartmentCreate, current: UserPrincipal):
        if self.departments.get_by_code(payload.code):
            raise ConflictError("部门编码已存在")
        item = self.departments.create(payload.model_dump())
        record_operation(
            self.db,
            current,
            method="POST",
            path="/api/v1/departments",
            action="CREATE",
            resource_type="department",
            resource_id=item.id,
        )
        return item

    def update_department(
        self, item_id: int, payload: DepartmentUpdate, current: UserPrincipal
    ):
        item = self.departments.get(item_id)
        if not item or item.is_deleted:
            raise NotFoundError("部门不存在")
        result = self.departments.update(item, payload.model_dump(exclude_unset=True))
        record_operation(
            self.db,
            current,
            method="PATCH",
            path=f"/api/v1/departments/{item_id}",
            action="UPDATE",
            resource_type="department",
            resource_id=item_id,
        )
        return result

    def delete_department(self, item_id: int, current: UserPrincipal) -> None:
        item = self.departments.get(item_id)
        if not item or item.is_deleted:
            raise NotFoundError("部门不存在")
        self.departments.update(item, {"is_deleted": True, "status": "INACTIVE"})
        record_operation(
            self.db,
            current,
            method="DELETE",
            path=f"/api/v1/departments/{item_id}",
            action="DELETE",
            resource_type="department",
            resource_id=item_id,
        )

    def list_categories(self, page: int, page_size: int):
        return self.categories.paginate(page, page_size)

    def create_category(self, payload: CategoryCreate, current: UserPrincipal):
        if self.categories.get_by_code(payload.code):
            raise ConflictError("岗位分类编码已存在")
        item = self.categories.create(payload.model_dump())
        record_operation(
            self.db,
            current,
            method="POST",
            path="/api/v1/job-categories",
            action="CREATE",
            resource_type="job_category",
            resource_id=item.id,
        )
        return item

    def update_category(
        self, item_id: int, payload: CategoryUpdate, current: UserPrincipal
    ):
        item = self.categories.get(item_id)
        if not item:
            raise NotFoundError("岗位分类不存在")
        result = self.categories.update(item, payload.model_dump(exclude_unset=True))
        record_operation(
            self.db,
            current,
            method="PATCH",
            path=f"/api/v1/job-categories/{item_id}",
            action="UPDATE",
            resource_type="job_category",
            resource_id=item_id,
        )
        return result

    def delete_category(self, item_id: int, current: UserPrincipal) -> None:
        item = self.categories.get(item_id)
        if not item:
            raise NotFoundError("岗位分类不存在")
        self.categories.delete(item)
        record_operation(
            self.db,
            current,
            method="DELETE",
            path=f"/api/v1/job-categories/{item_id}",
            action="DELETE",
            resource_type="job_category",
            resource_id=item_id,
        )
