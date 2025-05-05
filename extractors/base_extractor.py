import abc

from models.data_models import ExtractionResult, Source


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
