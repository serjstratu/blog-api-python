import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings
from app.db.database import get_db
from app.modules.auth.dependencies import ACCESS_COOKIE_NAME

from app.modules.auth import service
from app.modules.auth.schema import AccessTokenResponse, LoginRequest, TokenResponse
from app.modules.users.schema import UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"
ACCESS_COOKIE_PATH = "/api/notifications"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=REFRESH_COOKIE_PATH,
    )


def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=ACCESS_COOKIE_PATH,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = service.authenticate_user(
        db,
        credentials.login,
        credentials.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(str(user.id))
    refresh_token, refresh_token_id, refresh_expires_at = create_refresh_token(str(user.id))
    service.save_refresh_token(
        db,
        token_id=refresh_token_id,
        user_id=user.id,
        expires_at=refresh_expires_at,
    )
    _set_refresh_cookie(response, refresh_token)
    _set_access_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie is missing",
        )

    try:
        payload = decode_refresh_token(refresh_token)
        user_id = int(payload["sub"])
        old_token_id = str(payload["jti"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        ) from None

    new_refresh_token, new_token_id, new_expires_at = create_refresh_token(str(user_id))
    user = service.rotate_refresh_token(
        db,
        old_token_id=old_token_id,
        user_id=user_id,
        new_token_id=new_token_id,
        new_expires_at=new_expires_at,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has already been used or is no longer valid",
        )

    access_token = create_access_token(str(user.id))
    _set_refresh_cookie(response, new_refresh_token)
    _set_access_cookie(response, access_token)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)
            user_id = int(payload["sub"])
            token_id = str(payload["jti"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            pass
        else:
            service.revoke_refresh_token(db, token_id=token_id, user_id=user_id)

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        path=ACCESS_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
