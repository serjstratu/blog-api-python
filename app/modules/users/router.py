from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users import service
from app.modules.users.model import User
from app.modules.users.schema import UserProfileUpdate, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AVATAR_DIR = PROJECT_ROOT / "uploads" / "avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024
AVATAR_TYPES = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return service.get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


def require_owner(user_id: int, current_user: User) -> None:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own profile")


@router.patch("/{user_id}", response_model=UserResponse)
def update_profile(
    user_id: int,
    profile: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(user_id, current_user)
    return service.update_user_profile(db, current_user, profile)


@router.post("/{user_id}/avatar", response_model=UserResponse)
async def upload_avatar(
    user_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(user_id, current_user)

    file_type = AVATAR_TYPES.get(file.content_type or "")
    if file_type is None:
        raise HTTPException(status_code=415, detail="Avatar must be JPEG, PNG, or WebP")

    content = await file.read(MAX_AVATAR_SIZE + 1)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=413, detail="Avatar must be 5 MB or smaller")

    extension, signature = file_type
    if not content.startswith(signature) or (
        file.content_type == "image/webp"
        and (len(content) < 12 or content[8:12] != b"WEBP")
    ):
        raise HTTPException(status_code=400, detail="File content does not match its image type")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    destination = AVATAR_DIR / filename
    destination.write_bytes(content)

    old_avatar = current_user.avatar
    current_user.avatar = f"/uploads/avatars/{filename}"
    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        destination.unlink(missing_ok=True)
        db.rollback()
        raise

    _remove_local_avatar(old_avatar)
    return current_user


@router.delete("/{user_id}/avatar", response_model=UserResponse)
def delete_avatar(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_owner(user_id, current_user)
    old_avatar = current_user.avatar
    current_user.avatar = None
    db.commit()
    db.refresh(current_user)
    _remove_local_avatar(old_avatar)
    return current_user


def _remove_local_avatar(avatar_url: str | None) -> None:
    if not avatar_url or not avatar_url.startswith("/uploads/avatars/"):
        return
    filename = avatar_url.removeprefix("/uploads/avatars/")
    if Path(filename).name == filename:
        (AVATAR_DIR / filename).unlink(missing_ok=True)
