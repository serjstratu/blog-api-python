from datetime import datetime, timezone

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.users.model import User
from app.modules.auth.refresh_model import RefreshToken


def authenticate_user(
    db: Session,
    login: str,
    password: str
) -> User | None:

    normalized_login = login.strip().lower()

    query = select(User).where(
        or_(
            func.lower(User.username) == normalized_login,
            func.lower(User.email) == normalized_login
        )
    ).limit(1)

    user = db.scalar(query)

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    user.last_login = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def save_refresh_token(
    db: Session,
    *,
    token_id: str,
    user_id: int,
    expires_at,
) -> None:
    db.add(RefreshToken(jti=token_id, user_id=user_id, expires_at=expires_at))
    db.commit()


def rotate_refresh_token(
    db: Session,
    *,
    old_token_id: str,
    user_id: int,
    new_token_id: str,
    new_expires_at,
) -> User | None:
    token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.jti == old_token_id)
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    if (
        token is None
        or token.user_id != user_id
        or token.revoked_at is not None
        or token.expires_at <= now
    ):
        return None

    user = db.get(User, user_id)
    if user is None:
        return None

    token.revoked_at = now
    db.add(
        RefreshToken(
            jti=new_token_id,
            user_id=user_id,
            expires_at=new_expires_at,
        )
    )
    db.commit()
    return user


def revoke_refresh_token(db: Session, *, token_id: str, user_id: int) -> None:
    token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.jti == token_id, RefreshToken.user_id == user_id)
        .with_for_update()
    )
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
