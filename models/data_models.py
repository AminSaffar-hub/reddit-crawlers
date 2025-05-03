from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Post(BaseModel):
    id: str
    text: str
    title: str
    timestamp: datetime
    score: int
    num_comments: int
    url: Optional[str]
    author_id: str


class Author(BaseModel):
    id: str
    name: str
    birth_date: Optional[datetime] = None
    publication_karma: Optional[int] = Field(default=0, ge=0)
    comment_karma: Optional[int] = Field(default=0, ge=0)


class Media(BaseModel):
    id: str
    post_id: str
    original_url: HttpUrl
    hosted_url: Optional[str] = None


class Source(BaseModel):
    author: str
    time_filter: str = "month"
    limit: int = 100
