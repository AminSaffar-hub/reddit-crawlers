import importlib
from typing import Optional

from celery import Task

from config.config import settings
from extractors.base_extractor import BaseExtractor
from models.data_models import Source
from storage.minio_storage import MinIOHandler


class ExtractTask(Task):
    _extractors: dict[str, BaseExtractor] = {}

    def get_extractor(self, source_type: str) -> BaseExtractor:
        if source_type not in self._extractors:
            if source_type not in settings.EXTRACTORS:
                raise ValueError(f"Unsupported source type: {source_type}")

            extractor_config = settings.EXTRACTORS[source_type]
            if not extractor_config["enabled"]:
                raise ValueError(
                    f"Extractor {source_type} is disabled in configuration"
                )

            module_path, class_name = extractor_config["class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            extractor_class = getattr(module, class_name)

            self._extractors[source_type] = extractor_class()
        return self._extractors[source_type]


class StorageTask(Task):
    _storage: Optional[MinIOHandler] = None

    @property
    def storage(self) -> MinIOHandler:
        if self._storage is None:
            storage_config = settings.STORAGE["minio"]
            if not storage_config["enabled"]:
                raise ValueError("MinIO storage is disabled in configuration")

            module_path, class_name = storage_config["class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            storage_class = getattr(module, class_name)

            self._storage = storage_class(storage_config["config"])
        return self._storage
