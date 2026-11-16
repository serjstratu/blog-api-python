from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.posts.schema import PaginationMetadata, to_camel


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    parent_id: int | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    parent_id: int | None
    content: str
    created_at: datetime
    updated_at: datetime
    replies: list["CommentResponse"] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PaginatedCommentsResponse(BaseModel):
    data: list[CommentResponse]
    pagination: PaginationMetadata

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


CommentResponse.model_rebuild()
