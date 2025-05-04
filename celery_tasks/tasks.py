import logging
from datetime import datetime
from typing import List, Optional

from celery import shared_task

from celery_tasks.base_task import ExtractTask, StorageTask
from models.data_models import Author, Media, Post, Source

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=ExtractTask, name="crawling:crawl_reddit_author")
def crawl_reddit_author(self, author_name: str, date_start: datetime) -> Optional[str]:
    try:
        logger.info(f"Starting crawl for author: {author_name} from date: {date_start}")
        source_config = Source(author=author_name, date_start=date_start, limit=100)

        author, posts, medias = self.extractor.extract(source_config)

        if author and posts:
            logger.info(f"Successfully extracted data for author: {author_name}")
            author_dict = author.dict()
            posts_dict = [post.dict() for post in posts]
            medias_dict = [
                {**media.dict(), "original_url": str(media.original_url)}
                for media in medias
            ]

            process_reddit_data.delay(author_dict, posts_dict, medias_dict)
            return author.id

        logger.warning(f"No data found for author: {author_name}")
        return None

    except Exception as e:
        logger.error(f"Error crawling author {author_name}: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, name="processing:process_reddit_data")
def process_reddit_data(
    self, author_data: dict, posts_data: List[dict], medias_data: List[dict]
):
    try:
        logger.info(f"Processing Reddit data for author: {author_data.get('id')}")
        store_metadata.delay(author_data, posts_data)
        for media in medias_data:
            process_media.delay(media)
        logger.info(
            f"Successfully queued processing for author: {author_data.get('id')}"
        )
    except Exception as e:
        logger.error(f"Error processing Reddit data: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, base=StorageTask, name="storage:store_metadata")
def store_metadata(self, author_data: dict, posts_data: List[dict]):
    try:
        logger.info(f"Storing metadata for author: {author_data.get('id')}")
        author = Author(**author_data)
        posts = [Post(**post_data) for post_data in posts_data]

        self.storage.store_author(author)
        logger.info(f"Stored author data: {author.id}")

        for post in posts:
            self.storage.store_post(post)
            logger.debug(f"Stored post: {post.id}")

    except Exception as e:
        logger.error(f"Error storing metadata: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, base=StorageTask, name="media:process_media")
def process_media(self, media_data: dict):
    try:
        logger.info(f"Processing media: {media_data.get('id')}")
        media = Media(**media_data)
        self.storage.store_media(media)
        logger.info(f"Successfully stored media: {media.id}")
    except Exception as e:
        logger.error(f"Error processing media: {str(e)}", exc_info=True)
        self.retry(exc=e, countdown=60)
