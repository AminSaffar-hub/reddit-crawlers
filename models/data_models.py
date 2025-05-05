from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class Post(BaseModel):
    id: str
    text: Optional[str] = None
    title: Optional[str] = None
    timestamp: Optional[datetime] = None
    num_likes: Optional[int] = None
    num_comments: Optional[int] = None
    url: Optional[str] = None
    author_id: str


class Author(BaseModel):
    id: str
    name: str
    headline: Optional[str] = None
    url: Optional[str] = None
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
    source_type: Literal["reddit", "linkedin"]
    limit: int = 100


class ExtractionResult(BaseModel):
    author: Author
    posts: List[Post]
    medias: List[Media]
