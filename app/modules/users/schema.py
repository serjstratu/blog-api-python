from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
