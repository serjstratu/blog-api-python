from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = None
    phone: str | None = Field(default=None, max_length=30)


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    avatar: str | None
    bio: str | None
    phone: str | None
    roles: list[str]
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
