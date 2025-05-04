import abc
from datetime import datetime
from pathlib import Path
from typing import List

from models.data_models import Source


class BaseExtractor(abc.ABC):

    @abc.abstractmethod
    def extract(self, source_config: Source):
        raise NotImplemented("Method not implemented")
