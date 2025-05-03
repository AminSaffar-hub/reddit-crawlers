from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from minio import Minio
from pydantic import BaseModel, HttpUrl

from models.data_models import Author, Media, Post
from storage.minio_storage import MinIOHandler


@pytest.fixture(autouse=True)
def mock_minio():
    with patch('storage.minio_storage.Minio') as mock:
        client = MagicMock(spec=Minio)
        client.bucket_exists.return_value = False
        client.make_bucket.return_value = None
        client.fput_object.return_value = None
        client.put_object.return_value = None
        mock.return_value = client
        yield client


@pytest.fixture
def minio_handler():
    config = {
        "endpoint": "localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "secure": False,
    }
    return MinIOHandler(config)


@pytest.fixture
def sample_author():
    return Author(
        id="test_author",
        name="Test Author",
        publication_karma=100,
        comment_karma=50
    )


@pytest.fixture
def sample_post():
    return Post(
        id="test_post",
        title="Test Post",
        text="This is a test post",
        timestamp=datetime.now(),
        score=100,
        num_comments=50,
        url="https://example.com",
        author_id="test_author"
    )


@pytest.fixture
def sample_media():
    return Media(
        id="test_media",
        post_id="test_post",
        original_url=HttpUrl("https://example.com/test.jpg")
    )


def test_setup_buckets_new(minio_handler, mock_minio):
    mock_minio.reset_mock()
    
    minio_handler.setup_buckets()

    assert mock_minio.bucket_exists.call_count == 2
    mock_minio.bucket_exists.assert_any_call("reddit-data")
    mock_minio.bucket_exists.assert_any_call("reddit-media")
    
    assert mock_minio.make_bucket.call_count == 2
    mock_minio.make_bucket.assert_any_call("reddit-data")
    mock_minio.make_bucket.assert_any_call("reddit-media")


def test_setup_buckets_existing(minio_handler, mock_minio):
    mock_minio.reset_mock()
    
    mock_minio.bucket_exists.return_value = True
    minio_handler.setup_buckets()

    mock_minio.make_bucket.assert_not_called()


def test_store_author_success(minio_handler, mock_minio, sample_author):
    with patch("pyarrow.Table") as mock_table_class, patch(
        "pyarrow.parquet.write_table"
    ), patch("os.remove"), patch("tempfile.mktemp") as mock_mktemp:

        mock_table = MagicMock()
        mock_table_class.from_pydict.return_value = mock_table
        
        mock_mktemp.return_value = "authors/test_author.parquet"

        minio_handler.store_author(sample_author)

        mock_minio.fput_object.assert_called_once()
        mock_minio.fput_object.assert_called_with(
            "reddit-data",
            "authors/test_author.parquet",
            "authors/test_author.parquet",
            content_type="application/parquet"
        )


def test_store_post_success(minio_handler, mock_minio, sample_post):
    with patch("pyarrow.Table") as mock_table_class, patch(
        "pyarrow.parquet.write_table"
    ), patch("os.remove") , patch("tempfile.mktemp") as mock_mktemp:
        mock_table = MagicMock()
        mock_table_class.from_pydict.return_value = mock_table
        
        mock_mktemp.return_value = "posts/test_post.parquet"

        minio_handler.store_post(sample_post)

        mock_minio.fput_object.assert_called_once()
        mock_minio.fput_object.assert_called_with(
            "reddit-data",
            "posts/test_post.parquet",
            "posts/test_post.parquet",
            content_type="application/parquet"
        )


def test_store_media_success(minio_handler, mock_minio, sample_media):
    with patch("pyarrow.Table") as mock_table_class, patch(
        "pyarrow.parquet.write_table"
    ), patch("os.remove") , patch(
        "requests.get"
    ) as mock_get:

        mock_table = MagicMock()
        mock_table_class.from_pydict.return_value = mock_table

        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_get.return_value = mock_response

        minio_handler.store_media(sample_media)

        assert mock_minio.fput_object.call_count == 2
        assert mock_minio.put_object.call_count == 1


def test_store_media_different_types(minio_handler, mock_minio):
    media_types = [
        ("image/jpeg", ".jpg"),
        ("image/png", ".png"),
        ("video/mp4", ".mp4"),
        ("application/pdf", ".pdf"),
        ("unknown/type", ".type"),
    ]

    for content_type, expected_ext in media_types:
        media = Media(
            id=f"test_media_{content_type}",
            post_id="test_post",
            original_url=HttpUrl(f"https://example.com/test{expected_ext}")
        )

        with patch("pyarrow.Table") as mock_table_class, patch(
            "pyarrow.parquet.write_table"
        ) as mock_write, patch("os.remove") as mock_remove, patch(
            "requests.get"
        ) as mock_get:

            mock_table = MagicMock()
            mock_table_class.from_pydict.return_value = mock_table

            mock_response = MagicMock()
            mock_response.content = b"test content"
            mock_response.headers = {"content-type": content_type}
            mock_get.return_value = mock_response
            minio_handler.store_media(media)

            assert mock_minio.fput_object.call_count == 2
            mock_minio.fput_object.assert_called_with(
                "reddit-data",
                f"media/metadata/test_media_{content_type}.parquet",
                f"media/metadata/test_media_{content_type}.parquet",
                content_type="application/parquet"
            )

            put_object_call = mock_minio.put_object.call_args
            assert put_object_call.args[0] == "reddit-media"
            assert put_object_call.args[1] == f"media/files/test_media_{content_type}{expected_ext}"
            assert put_object_call.kwargs["length"] == len(b"test content")
            assert put_object_call.kwargs["content_type"] == content_type

            mock_minio.reset_mock()


def test_download_media_error(minio_handler, mock_minio, sample_media):
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Download failed")

        result = minio_handler._download_media(sample_media)

        assert result is None
        mock_minio.put_object.assert_not_called()