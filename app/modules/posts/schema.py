import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class PostInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9-]+$")
    content: str = Field(min_length=1)
    excerpt: str | None = None
    image: str | None = None
    status: str = Field(default="draft", pattern=r"^(draft|published|archived)$")
    category_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    is_featured: bool = False

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PostCreate(PostInput):
    pass


class PostReplace(PostInput):
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9-]+$")


class PostPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-zA-Z0-9-]+$")
    content: str | None = Field(default=None, min_length=1)
    excerpt: str | None = None
    image: str | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|published|archived)$")
    category_id: int | None = None
    tags: list[str] | None = None
    is_featured: bool | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str | None
    image: str | None
    status: str
    category_id: int | None
    tags: list[str]
    views: int
    likes: int
    dislikes: int
    comments_count: int
    is_featured: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    user_id: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PaginationMetadata(BaseModel):
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PaginatedPostsResponse(BaseModel):
    data: list[PostResponse]
    pagination: PaginationMetadata

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "post"
