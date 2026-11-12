from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.posts import service
from app.modules.posts.model import Post
from app.modules.posts.schema import (
    PaginatedPostsResponse,
    PaginationMetadata,
    PostCreate,
    PostPatch,
    PostReplace,
    PostResponse,
)
from app.modules.users.model import User


router = APIRouter(prefix="/posts", tags=["Posts"])


def _owned_post(db: Session, post_id: int, user: User) -> Post:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("", response_model=PaginatedPostsResponse)
def list_posts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    posts, total_items = service.list_posts(db, limit=limit, offset=offset)
    current_page = offset // limit + 1
    total_pages = (total_items + limit - 1) // limit

    return PaginatedPostsResponse(
        data=posts,
        pagination=PaginationMetadata(
            current_page=current_page,
            per_page=limit,
            total_items=total_items,
            total_pages=total_pages,
            has_next_page=offset + len(posts) < total_items,
            has_previous_page=offset > 0 and total_items > 0,
        ),
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = service.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_post(db, data, current_user)


@router.put("/{post_id}", response_model=PostResponse)
def replace_post(
    post_id: int,
    data: PostReplace,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = _owned_post(db, post_id, current_user)
    return service.replace_post(db, post, data)


@router.patch("/{post_id}", response_model=PostResponse)
def patch_post(
    post_id: int,
    data: PostPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = _owned_post(db, post_id, current_user)
    return service.patch_post(db, post, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = _owned_post(db, post_id, current_user)
    service.delete_post(db, post)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
