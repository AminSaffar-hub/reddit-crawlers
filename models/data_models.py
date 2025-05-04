from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Post(BaseModel):
    id: str
    text: str
    title: str
    timestamp: datetime
    num_likes: int
    num_comments: int
    url: Optional[str]
    author_id: str


class Author(BaseModel):
    id: str
    name: str
    joined_date: Optional[datetime] = None
    publication_score: Optional[int] = Field(default=0, ge=0)
    comment_score: Optional[int] = Field(default=0, ge=0)


class Media(BaseModel):
    id: str
    post_id: str
    original_url: HttpUrl
    hosted_url: Optional[str] = None


class Source(BaseModel):
    author: str
    date_start: datetime
    limit: int = 100
