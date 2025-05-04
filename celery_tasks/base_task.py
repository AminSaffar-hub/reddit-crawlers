from typing import Optional, Type

from celery import Task

from config.config import settings
from extractors.base_extractor import BaseExtractor
from extractors.linkedin_extractor import LinkedinExtractor
from extractors.reddit_extractor import RedditExtractor
from models.data_models import Source
from storage.minio_storage import MinIOHandler


class ExtractTask(Task):
    _extractors: dict[str, BaseExtractor] = {}

    def get_extractor(self, source_type: str) -> BaseExtractor:
        if source_type not in self._extractors:
            if source_type == "reddit":
                self._extractors[source_type] = RedditExtractor()
            elif source_type == "linkedin":
                self._extractors[source_type] = LinkedinExtractor()
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
        return self._extractors[source_type]


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
