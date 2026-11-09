from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.model import User


def get_users(db: Session) -> list[User]:
    query = select(User).order_by(User.id)

    return list(db.scalars(query).all())


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)