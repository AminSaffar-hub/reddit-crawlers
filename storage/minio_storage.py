import logging
import os
from io import BytesIO
from typing import Dict, Optional

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from minio import Minio
from minio.error import S3Error

from config.config import settings
from models.data_models import Author, Media, Post
from storage.base_storage import BaseStorageHandler

logger = logging.getLogger(__name__)


class MinIOHandler(BaseStorageHandler):
    def __init__(self, minio_config: dict):
        self.client = Minio(**minio_config)
        self.buckets = {"data": "extracts-data", "media": "extracts-media"}
        self.setup_buckets()

    def setup_buckets(self):
        for bucket in self.buckets.values():
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                if e.code == "BucketAlreadyOwnedByYou":
                    logger.info(f"Bucket {bucket} already exists")
                else:
                    logger.error(f"Error setting up bucket {bucket}: {e}")
                    raise

    def store_author(self, author: Author):
        try:
            data = author.model_dump()
            path = f"authors/{author.id}.parquet"
            self._save_parquet(data, path, self.buckets["data"])
        except Exception as e:
            logger.error(f"Error storing author {author.id}: {e}")

    def store_post(self, post: Post):
        try:
            data = post.model_dump()
            path = f"posts/{post.id}.parquet"
            self._save_parquet(data, path, self.buckets["data"])
        except Exception as e:
            logger.error(f"Error storing post {post.id}: {e}")

    def store_media(self, media: Media):
        try:
            path = f"media/metadata/{media.id}.parquet"
            data = media.model_dump()
            self._save_parquet(data, path, self.buckets["data"])
            if media.original_url:
                media_path = self._download_media(media)
                if media_path:
                    media.hosted_url = media_path
                    self._save_parquet(media.model_dump(), path, self.buckets["data"])

        except Exception as e:
            logger.error(f"Error storing media {media.id}: {e}")

    def _save_parquet(self, data: Dict, path: str, bucket: str):
        """Save data as Parquet file and upload to MinIO"""
        try:
            converted_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    converted_data[key] = [str(value)]
                elif hasattr(value, "__str__"):
                    converted_data[key] = [str(value)]
                else:
                    converted_data[key] = [value]

            os.makedirs(os.path.dirname(path), exist_ok=True)

            table = pa.Table.from_pydict(converted_data)
            pq.write_table(table, path)

            self.client.fput_object(
                bucket, path, path, content_type="application/parquet"
            )

            os.remove(path)

        except Exception as e:
            logger.error(f"Error saving Parquet: {str(e)}")
            raise

    def _download_media(self, media: Media) -> Optional[str]:
        try:
            response = requests.get(str(media.original_url))
            response.raise_for_status()

            mime_to_ext = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
                "video/mp4": ".mp4",
                "video/webm": ".webm",
                "video/quicktime": ".mov",
                "application/pdf": ".pdf",
            }

            content_type = (
                response.headers.get("content-type", "").split(";")[0].strip().lower()
            )

            ext = mime_to_ext.get(content_type)

            if not ext:
                if "/" in content_type:
                    ext = f".{content_type.split('/')[-1]}"
                else:
                    ext = ".bin"

            path = f"media/files/{media.id}{ext}"

            data = BytesIO(response.content)
            data.seek(0)

            self.client.put_object(
                self.buckets["media"],
                path,
                data,
                length=len(response.content),
                content_type=content_type,
            )

            return f"https://{settings.MINIO_HOST}:{settings.MINIO_PORT}/{self.buckets['media']}/{path}"

        except Exception as e:
            logger.error(f"Error downloading media {media.id}: {e}")
            return None
