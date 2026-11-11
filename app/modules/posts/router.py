from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.posts import service
from app.modules.posts.model import Post
from app.modules.posts.schema import PostCreate, PostPatch, PostReplace, PostResponse
from app.modules.users.model import User


router = APIRouter(prefix="/posts", tags=["Posts"])


def _owned_post(db: Session, post_id: int, user: User) -> Post:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("", response_model=list[PostResponse])
def list_posts(
    db: Session = Depends(get_db),
):
    return service.list_posts(db)


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
