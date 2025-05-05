from typing import Any, Dict, List

from pydantic import BaseModel, HttpUrl

from formatters.base import BaseFormatter


class HttpUrlFormatter(BaseFormatter):

    def format_model(self, model: BaseModel) -> Dict[str, Any]:
        model_dict = model.model_dump()
        return self._convert_special_fields(model_dict)

    def format_models(self, models: List[BaseModel]) -> List[Dict[str, Any]]:
        return [self.format_model(model) for model in models]

    def _convert_special_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = data.copy()

        # Handle URL fields
        for key in ["url", "original_url"]:
            if key in result and isinstance(result[key], (HttpUrl, str)):
                result[key] = str(result[key])

        return result
