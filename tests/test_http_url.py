import pytest
from pydantic import BaseModel, HttpUrl

from formatters.http_url import HttpUrlFormatter


class TestHttpUrlFormatter:

    class TestModel(BaseModel):

        id: str
        url: HttpUrl
        original_url: HttpUrl

    @pytest.fixture
    def formatter(self):
        return HttpUrlFormatter()

    @pytest.fixture
    def test_model(self):
        return self.TestModel(
            id="test",
            url=HttpUrl("https://example.com"),
            original_url=HttpUrl("https://original.com"),
        )

    def test_format_model_converts_urls(self, formatter, test_model):
        result = formatter.format_model(test_model)

        assert isinstance(result["url"], str)
        assert result["url"] == "https://example.com/"
        assert isinstance(result["original_url"], str)
        assert result["original_url"] == "https://original.com/"

    def test_format_models_converts_urls(self, formatter, test_model):
        models = [test_model, test_model]
        result = formatter.format_models(models)

        assert len(result) == 2
        for model_dict in result:
            assert isinstance(model_dict["url"], str)
            assert model_dict["url"] == "https://example.com/"
            assert isinstance(model_dict["original_url"], str)
            assert model_dict["original_url"] == "https://original.com/"

    def test_convert_special_fields_preserves_other_types(self, formatter):
        data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "none": None,
        }

        result = formatter._convert_special_fields(data)

        assert result == data
