from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.modules.users.model import User


with SessionLocal() as db:
    user = db.scalar(
        select(User).where(User.username == "serj")
    )

    if user is None:
        raise Exception("Admin user not found")

    user.password_hash = hash_password("SerjPassword123!")
    db.commit()

    print("Admin password updated!")