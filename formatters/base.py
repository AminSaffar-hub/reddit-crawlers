from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class BaseFormatter(ABC):
    """Base class for all formatters that handle serialization of Pydantic models."""

    @abstractmethod
    def format_model(self, model: BaseModel) -> Dict[str, Any]:
        pass

    @abstractmethod
    def format_models(self, models: List[BaseModel]) -> List[Dict[str, Any]]:
        pass
