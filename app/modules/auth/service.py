from datetime import datetime, timezone

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.users.model import User


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