from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.comments import service
from app.modules.comments.schema import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedCommentsResponse,
)
from app.modules.posts.model import Post
from app.modules.posts.schema import PaginationMetadata
from app.modules.users.model import User


router = APIRouter(tags=["Comments"])


def _validate_post(db: Session, post_id: int) -> None:
    post = db.get(Post, post_id)
    if post is None or post.status != "published":
        raise HTTPException(status_code=404, detail="Post not found")


def _list_for_post(db: Session, post_id: int, limit: int, offset: int):
    comments, total_items = service.list_comments(
        db, post_id, limit=limit, offset=offset
    )
    if total_items < 0:
        raise HTTPException(status_code=404, detail="Post not found")

    total_pages = (total_items + limit - 1) // limit
    return PaginatedCommentsResponse(
        data=comments,
        pagination=PaginationMetadata(
            current_page=offset // limit + 1,
            per_page=limit,
            total_items=total_items,
            total_pages=total_pages,
            has_next_page=offset + len(comments) < total_items,
            has_previous_page=offset > 0 and total_items > 0,
        ),
    )


@router.get("/comments", response_model=PaginatedCommentsResponse)
def list_comments_by_query(
    post_id: int = Query(alias="postId"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return _list_for_post(db, post_id, limit, offset)


@router.get("/posts/{post_id}/comments", response_model=PaginatedCommentsResponse)
def list_post_comments(
    post_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return _list_for_post(db, post_id, limit, offset)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post_comment(
    post_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_post(db, post_id)
    parent = None
    if data.parent_id is not None:
        parent = service.get_comment(db, data.parent_id)
        if parent is None or parent.post_id != post_id or parent.parent_id is not None:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    return service.create_comment(
        db,
        post_id=post_id,
        author=current_user,
        content=data.content,
        parent=parent,
    )


@router.post(
    "/comments/{comment_id}/replies",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reply(
    comment_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = service.get_comment(db, comment_id)
    if parent is None or parent.parent_id is not None:
        raise HTTPException(status_code=404, detail="Parent comment not found")
    _validate_post(db, parent.post_id)
    return service.create_comment(
        db,
        post_id=parent.post_id,
        author=current_user,
        content=data.content,
        parent=parent,
    )


@router.patch("/comments/{comment_id}", response_model=CommentResponse)
def edit_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    return service.update_comment(db, comment, data.content)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    is_admin = any(role.lower() == "admin" for role in (current_user.roles or []))
    if comment.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You cannot delete this comment")
    service.soft_delete_comment(db, comment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
