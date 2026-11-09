from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255))

    password_hash: Mapped[str] = mapped_column(String(255))

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    roles: Mapped[list[str]] = mapped_column(
        ARRAY(Text)
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )