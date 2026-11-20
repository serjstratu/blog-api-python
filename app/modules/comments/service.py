from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from app.modules.comments.model import Comment
from app.modules.notifications.service import create_notification
from app.modules.posts.model import Post
from app.modules.users.model import User


def list_comments(
    db: Session, post_id: int, *, limit: int, offset: int
) -> tuple[list[Comment], int]:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.status == "published"))
    if post is None:
        return [], -1

    query = (
        select(Comment)
        .where(
            Comment.post_id == post_id,
            Comment.parent_id.is_(None),
            Comment.deleted_at.is_(None),
        )
        .options(
            selectinload(Comment.replies),
            with_loader_criteria(Comment, Comment.deleted_at.is_(None)),
        )
        .order_by(Comment.created_at, Comment.id)
        .limit(limit)
        .offset(offset)
    )
    count_query = select(func.count()).select_from(Comment).where(
        Comment.post_id == post_id,
        Comment.parent_id.is_(None),
        Comment.deleted_at.is_(None),
    )
    comments = list(db.scalars(query).all())
    total_items = db.scalar(count_query) or 0
    return comments, total_items


def get_comment(db: Session, comment_id: int) -> Comment | None:
    return db.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.deleted_at.is_(None))
    )


def create_comment(
    db: Session,
    *,
    post_id: int,
    author: User,
    content: str,
    parent: Comment | None = None,
) -> Comment:
    now = datetime.now(timezone.utc)
    comment = Comment(
        post_id=post_id,
        author_id=author.id,
        parent_id=parent.id if parent else None,
        content=content,
        created_at=now,
        updated_at=now,
    )
    post = db.get(Post, post_id)
    post.comments_count += 1
    db.add(comment)
    db.flush()
    recipient_id = parent.author_id if parent is not None else post.user_id
    create_notification(
        db,
        recipient_id=recipient_id,
        actor_id=author.id,
        notification_type="reply" if parent is not None else "comment",
        entity_type="comment",
        entity_id=comment.id,
        message="Someone replied to your comment." if parent is not None else "Someone commented on your post.",
    )
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment: Comment, content: str) -> Comment:
    comment.content = content
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)
    return comment


def soft_delete_comment(db: Session, comment: Comment) -> None:
    comment.deleted_at = datetime.now(timezone.utc)
    comment.updated_at = comment.deleted_at
    post = db.get(Post, comment.post_id)
    if post is not None:
        post.comments_count = max(0, post.comments_count - 1)
    db.commit()
