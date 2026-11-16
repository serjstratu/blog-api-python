from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent",
        order_by=lambda: (Comment.created_at, Comment.id),
        foreign_keys=[parent_id],
    )
    parent: Mapped["Comment | None"] = relationship(
        back_populates="replies",
        remote_side=[id],
        foreign_keys=[parent_id],
    )
