from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest
from app.security.dependencies import CurrentUser
from app.security.rate_limit import rate_limit
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", dependencies=[Depends(rate_limit("auth:login", 10))])
def login(payload: LoginRequest, request: Request, db: DbSession):
    return success(AuthService(db).login(payload, request))


@router.post("/refresh", dependencies=[Depends(rate_limit("auth:refresh", 30))])
def refresh(payload: RefreshRequest, db: DbSession):
    return success(AuthService(db).refresh(payload.refresh_token))


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    request: Request,
    user: CurrentUser,
    db: DbSession,
):
    return success(
        AuthService(db).logout(
            user,
            payload.refresh_token,
            payload.all_devices,
            request,
        )
    )


@router.get("/me")
def me(user: CurrentUser, db: DbSession):
    return success(AuthService(db).identity(user))
