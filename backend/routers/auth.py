from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from core.auth.password import hash_password, verify_password
from core.auth.jwt_handler import create_access_token, create_refresh_token
from core.auth.redis_session import revoke_token, get_current_user_id_from_token
from core.config import settings
from core.exceptions import AppException
from models.user import User
from core.db import get_db
from pydantic import BaseModel
from datetime import timedelta
from jwt import decode as jwt_decode
from core.permissions.dependencies import get_current_user, get_redis
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str


class AuthResponse(BaseModel):
    message: str
    user: UserResponse | None = None


class MeResponse(BaseModel):
    user: UserResponse


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == data.username)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise AppException("USER_EXISTS", "Username already taken", 400)

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    return AuthResponse(message="User registered")


@router.post("/login")
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == data.username)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise AppException("INVALID_CREDENTIALS", "Invalid username or password", 401)

    access_token, access_jti = create_access_token(user.id)
    refresh_token, refresh_jti = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=int(timedelta(days=settings.JWT_REFRESH_EXPIRY_DAYS).total_seconds()),
        path='/',
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=int(timedelta(minutes=settings.JWT_ACCESS_EXPIRY_MINUTES).total_seconds()),
        path='/',
    )

    return AuthResponse(message="Logged in")


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, redis=Depends(get_redis)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise AppException("UNAUTHORIZED", "Missing refresh token", 401)

    user_id = await get_current_user_id_from_token(refresh_token, redis)
    if not user_id:
        raise AppException("INVALID_TOKEN", "Invalid refresh token", 401)

    access_token, access_jti = create_access_token(UUID(user_id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=int(timedelta(minutes=settings.JWT_ACCESS_EXPIRY_MINUTES).total_seconds()),
        path='/',
    )

    return AuthResponse(message="refreshed")


@router.post("/logout")
async def logout(request: Request, response: Response, redis=Depends(get_redis)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = jwt_decode(refresh_token, settings.JWT_SECRET, algorithms=["HS256"])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                import time
                ttl = int(exp - time.time())
                if ttl > 0:
                    await revoke_token(redis, jti, ttl)
        except Exception:
            pass

    response.delete_cookie("refresh_token")
    response.delete_cookie("access_token")
    return AuthResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
async def me(current_user: UUID = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == current_user)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise AppException("UNAUTHORIZED", "User not found", 401)
    return {"user": {"id": str(user.id), "username": user.username}}
