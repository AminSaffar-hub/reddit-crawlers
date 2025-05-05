from datetime import datetime, timedelta

import pytest

from extractors.linkedin_extractor import LinkedinExtractor
from extractors.reddit_extractor import RedditExtractor


class TestRedditFormatter:
    @pytest.fixture
    def extractor(self):
        return RedditExtractor()

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("1,234", 1234),
            ("1,234,567", 1234567),
            ("1234", 1234),
            ("0", 0),
            ("", 0),
            ("invalid", 0),
            ("1.234", 0),
            ("1,234.56", 0),
        ],
    )
    def test_format_int(self, extractor, input_text, expected):
        assert extractor._format_int(input_text) == expected


class TestLinkedInFormatters:
    @pytest.fixture
    def extractor(self):
        return LinkedinExtractor()

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("1K", 1000),
            ("1.5K", 1500),
            ("1M", 1000000),
            ("1.5M", 1500000),
            ("123", 123),
            ("0", 0),
            ("", 0),
            ("invalid", 0),
            ("1.5", 0),
            ("1.5B", 0),
        ],
    )
    def test_convert_abbreviated_to_number(self, extractor, input_text, expected):
        assert extractor._convert_abbreviated_to_number(input_text) == expected

    @pytest.mark.parametrize(
        "input_text,expected_delta",
        [
            ("2w", timedelta(weeks=2)),
            ("3d", timedelta(days=3)),
            ("5h", timedelta(hours=5)),
            ("1mo", timedelta(days=30)),
            ("1m", timedelta(days=30)),
            ("invalid", None),
            ("", None),
            ("1y", None),
        ],
    )
    def test_convert_relative_date(self, extractor, input_text, expected_delta):
        result = extractor._convert_relative_date(input_text)
        if expected_delta is None:
            assert result is None
        else:
            expected_time = datetime.now() - expected_delta
            assert abs((result - expected_time).total_seconds()) < 1
