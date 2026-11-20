from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.posts.model import Post
from app.modules.posts.reaction_model import PostReaction
from app.modules.posts.schema import PostCreate, PostPatch, PostReplace, make_slug
from app.modules.notifications.service import create_notification
from app.modules.users.model import User


def list_posts(
    db: Session,
    *,
    limit: int,
    offset: int,
    tag: str | None = None,
) -> tuple[list[Post], int]:
    filters = [Post.status == "published"]
    if tag:
        filters.append(Post.tags.overlap([tag]))

    query = (
        select(Post)
        .where(*filters)
        .order_by(Post.published_at.desc(), Post.id.desc())
        .limit(limit)
        .offset(offset)
    )
    count_query = select(func.count()).select_from(Post).where(*filters)
    posts = list(db.scalars(query).all())
    total_items = db.scalar(count_query) or 0
    return posts, total_items


def get_post(db: Session, post_id: int) -> Post | None:
    post = db.get(Post, post_id)
    if post is None or post.status != "published":
        return None
    return post


def _unique_slug(db: Session, requested: str | None, title: str, *, exclude_id: int | None = None) -> str:
    base = requested or make_slug(title)
    candidate = base
    suffix = 2
    while True:
        query = select(Post.id).where(Post.slug == candidate)
        if exclude_id is not None:
            query = query.where(Post.id != exclude_id)
        if db.scalar(query) is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def _apply_post_input(post: Post, data: PostCreate | PostReplace | PostPatch, db: Session) -> None:
    fields = data.model_dump(exclude_unset=isinstance(data, PostPatch))
    if "title" in fields and fields["title"] is not None:
        post.title = fields["title"]
    if "slug" in fields or "title" in fields:
        post.slug = _unique_slug(
            db,
            fields.get("slug"),
            post.title,
            exclude_id=post.id,
        )
    for name in ("content", "excerpt", "image", "status", "category_id", "tags", "is_featured"):
        can_clear = name in {"excerpt", "image", "category_id"}
        if name in fields and (fields[name] is not None or can_clear):
            setattr(post, name, fields[name])
    if post.status == "published" and post.published_at is None:
        post.published_at = datetime.now(timezone.utc)
    elif post.status != "published":
        post.published_at = None


def create_post(db: Session, data: PostCreate, user: User) -> Post:
    post = Post(
        title=data.title,
        slug="pending",
        content=data.content,
        user_id=user.id,
    )
    _apply_post_input(post, data, db)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def replace_post(db: Session, post: Post, data: PostReplace) -> Post:
    post.title = data.title
    post.content = data.content
    post.excerpt = data.excerpt
    post.image = data.image
    post.status = data.status
    post.category_id = data.category_id
    post.tags = data.tags
    post.is_featured = data.is_featured
    post.slug = _unique_slug(db, data.slug, data.title, exclude_id=post.id)
    if post.status == "published" and post.published_at is None:
        post.published_at = datetime.now(timezone.utc)
    elif post.status != "published":
        post.published_at = None
    db.commit()
    db.refresh(post)
    return post


def patch_post(db: Session, post: Post, data: PostPatch) -> Post:
    _apply_post_input(post, data, db)
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def increment_post_reaction(
    db: Session,
    *,
    post_id: int,
    user: User,
    reaction_value: str,
) -> tuple[Post, str] | None:
    if reaction_value not in {"like", "dislike"}:
        raise ValueError("Unsupported post reaction")

    post = db.scalar(
        select(Post)
        .where(Post.id == post_id, Post.status == "published")
        .with_for_update()
    )
    if post is None:
        return None

    reaction = db.get(PostReaction, (user.id, post_id))
    if reaction is None:
        reaction = PostReaction(
            user_id=user.id,
            post_id=post_id,
            reaction=reaction_value,
        )
        db.add(reaction)
        counter = "likes" if reaction_value == "like" else "dislikes"
        setattr(post, counter, (getattr(post, counter) or 0) + 1)
        reaction_changed = True
    elif reaction.reaction != reaction_value:
        old_counter = "likes" if reaction.reaction == "like" else "dislikes"
        new_counter = "likes" if reaction_value == "like" else "dislikes"
        setattr(post, old_counter, max(0, (getattr(post, old_counter) or 0) - 1))
        setattr(post, new_counter, (getattr(post, new_counter) or 0) + 1)
        reaction.reaction = reaction_value
        reaction_changed = True
    else:
        reaction_changed = False

    if reaction_changed:
        create_notification(
            db,
            recipient_id=post.user_id,
            actor_id=user.id,
            notification_type="reaction",
            entity_type="post",
            entity_id=post.id,
            message="Someone reacted to your post.",
        )

    db.commit()
    db.refresh(post)
    return post, reaction_value


def remove_post_reaction(db: Session, *, post_id: int, user: User) -> Post | None:
    post = db.scalar(
        select(Post)
        .where(Post.id == post_id, Post.status == "published")
        .with_for_update()
    )
    if post is None:
        return None

    reaction = db.get(PostReaction, (user.id, post_id))
    if reaction is not None:
        counter = "likes" if reaction.reaction == "like" else "dislikes"
        setattr(post, counter, max(0, (getattr(post, counter) or 0) - 1))
        db.delete(reaction)

    db.commit()
    db.refresh(post)
    return post
