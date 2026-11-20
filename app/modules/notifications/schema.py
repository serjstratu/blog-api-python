from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.modules.posts.schema import PaginationMetadata, to_camel


class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    actor_id: int | None
    type: str
    entity_type: str | None
    entity_id: int | None
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class NotificationsPage(BaseModel):
    data: list[NotificationResponse]
    pagination: PaginationMetadata

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UnreadCountResponse(BaseModel):
    unread_count: int

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ReadAllResponse(BaseModel):
    updated_count: int

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
