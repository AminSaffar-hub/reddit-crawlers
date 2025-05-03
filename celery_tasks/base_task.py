from typing import Optional

from celery import Task

from config.config import settings
from extractors.reddit_extractor import RedditExtractor
from storage.minio_storage import MinIOHandler


class ExtractTask(Task):
    _extractor: Optional[RedditExtractor] = None

    @property
    def extractor(self) -> RedditExtractor:
        if self._extractor is None:
            self._extractor = RedditExtractor()
        return self._extractor


class StorageTask(Task):
    _storage: Optional[MinIOHandler] = None

    @property
    def storage(self) -> MinIOHandler:
        if self._storage is None:
            self._storage = MinIOHandler(
                {
                    "endpoint": f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
                    "access_key": settings.MINIO_ACCESS_KEY,
                    "secret_key": settings.MINIO_SECRET_KEY,
                    "secure": False,
                }
            )
        return self._storage
