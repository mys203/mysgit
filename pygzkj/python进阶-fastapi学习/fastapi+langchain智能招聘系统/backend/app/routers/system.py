from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.common import PaginationQuery
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
from app.security.dependencies import require_any_permissions, require_permissions
from app.security.rate_limit import rate_limit
from app.services.system_service import SystemService

router = APIRouter(tags=["系统管理"])
SystemManager = Annotated[object, Depends(require_permissions("system:manage"))]
JobCategoryReader = Annotated[object, Depends(require_permissions("jobs:read"))]
JobCategoryWriter = Annotated[object, Depends(require_permissions("jobs:write"))]
DepartmentOptionsReader = Annotated[
    object,
    Depends(require_any_permissions("jobs:read", "interviews:read")),
]
UserOptionsReader = Annotated[
    object,
    Depends(require_any_permissions("interviews:read", "interviews:schedule")),
]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/users", dependencies=[Depends(rate_limit("users:list", 120))])
def list_users(
    db: DbSession,
    user: SystemManager,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    status: str | None = Query(None, pattern=r"^(ACTIVE|INACTIVE)$"),
):
    items, total = SystemService(db).list_users(page, page_size, search, status)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/users", dependencies=[Depends(rate_limit("users:create", 30))])
def create_user(payload: UserCreate, db: DbSession, user: SystemManager):
    return success(SystemService(db).create_user(payload, user), status_code=201)


@router.get("/users/options")
def user_options(
    db: DbSession,
    user: UserOptionsReader,
    search: str | None = Query(None, max_length=100),
    role_code: str | None = Query(
        None, pattern=r"^(ADMIN|HR_MANAGER|RECRUITER|INTERVIEWER|VIEWER)$"
    ),
    limit: int = Query(100, ge=1, le=200),
):
    return success(SystemService(db).user_options(search, role_code, limit))


@router.get("/users/{user_id}")
def get_user(user_id: int, db: DbSession, user: SystemManager):
    return success(SystemService(db).get_user(user_id))


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: DbSession, user: SystemManager):
    return success(SystemService(db).update_user(user_id, payload, user))


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: DbSession, user: SystemManager):
    SystemService(db).delete_user(user_id, user)
    return success({"id": user_id, "deleted": True})


@router.get("/roles")
def list_roles(
    db: DbSession,
    user: SystemManager,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = SystemService(db).list_roles(page, page_size)
    from app.routers.helpers import paginated
    from app.schemas.system import RoleResponse

    return paginated([RoleResponse.model_validate(row) for row in rows], total, page, page_size)


@router.post("/roles")
def create_role(payload: RoleCreate, db: DbSession, user: SystemManager):
    role = SystemService(db).create_role(payload, user)
    from app.schemas.system import RoleResponse

    return success(RoleResponse.model_validate(role), status_code=201)


@router.patch("/roles/{role_id}")
def update_role(role_id: int, payload: RoleUpdate, db: DbSession, user: SystemManager):
    role = SystemService(db).update_role(role_id, payload, user)
    from app.schemas.system import RoleResponse

    return success(RoleResponse.model_validate(role))


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: DbSession, user: SystemManager):
    SystemService(db).delete_role(role_id, user)
    return success({"id": role_id, "deleted": True})


@router.get("/departments")
def list_departments(
    db: DbSession,
    user: SystemManager,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = SystemService(db).list_departments(page, page_size)
    from app.routers.helpers import paginated
    from app.schemas.system import DepartmentResponse

    return paginated(
        [DepartmentResponse.model_validate(row) for row in rows], total, page, page_size
    )


@router.get("/departments/options")
def department_options(
    db: DbSession,
    user: DepartmentOptionsReader,
    search: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=200),
):
    return success(SystemService(db).department_options(search, limit))


@router.post("/departments")
def create_department(payload: DepartmentCreate, db: DbSession, user: SystemManager):
    item = SystemService(db).create_department(payload, user)
    from app.schemas.system import DepartmentResponse

    return success(DepartmentResponse.model_validate(item), status_code=201)


@router.patch("/departments/{department_id}")
def update_department(
    department_id: int, payload: DepartmentUpdate, db: DbSession, user: SystemManager
):
    item = SystemService(db).update_department(department_id, payload, user)
    from app.schemas.system import DepartmentResponse

    return success(DepartmentResponse.model_validate(item))


@router.delete("/departments/{department_id}")
def delete_department(department_id: int, db: DbSession, user: SystemManager):
    SystemService(db).delete_department(department_id, user)
    return success({"id": department_id, "deleted": True})


@router.get("/job-categories")
def list_categories(
    db: DbSession,
    user: JobCategoryReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = SystemService(db).list_categories(page, page_size)
    from app.routers.helpers import paginated
    from app.schemas.system import CategoryResponse

    return paginated([CategoryResponse.model_validate(row) for row in rows], total, page, page_size)


@router.post("/job-categories")
def create_category(payload: CategoryCreate, db: DbSession, user: JobCategoryWriter):
    item = SystemService(db).create_category(payload, user)
    from app.schemas.system import CategoryResponse

    return success(CategoryResponse.model_validate(item), status_code=201)


@router.patch("/job-categories/{category_id}")
def update_category(
    category_id: int, payload: CategoryUpdate, db: DbSession, user: JobCategoryWriter
):
    item = SystemService(db).update_category(category_id, payload, user)
    from app.schemas.system import CategoryResponse

    return success(CategoryResponse.model_validate(item))


@router.delete("/job-categories/{category_id}")
def delete_category(category_id: int, db: DbSession, user: JobCategoryWriter):
    SystemService(db).delete_category(category_id, user)
    return success({"id": category_id, "deleted": True})
