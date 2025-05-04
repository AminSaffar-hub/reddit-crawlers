import abc
from datetime import datetime
from pathlib import Path
from typing import List

from models.data_models import Source, ExtractionResult


class BaseExtractor(abc.ABC):

    @abc.abstractmethod
    def extract(self, source_config: Source) -> ExtractionResult:
        """Extract data from a source.

        Args:
            source_config: Configuration for the source to extract from

        Returns:
            ExtractionResult containing the author, posts, and media
        """
        raise NotImplementedError("Method not implemented")
