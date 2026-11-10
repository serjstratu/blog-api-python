from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.modules.users.schema import UserProfileUpdate


def get_users(db: Session) -> list[User]:
    query = select(User).order_by(User.id)

    return list(db.scalars(query).all())


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user_profile(
    db: Session,
    user: User,
    profile: UserProfileUpdate
) -> User:
    for field, value in profile.model_dump(exclude_unset=True).items():
        if field == "name" and value is None:
            continue
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
