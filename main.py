import logging
from datetime import datetime, timedelta

from celery_app import app
from celery_tasks import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():

    app.connection().ensure_connection(timeout=3)

    try:
        task = tasks.crawl_reddit_author.delay(
            author_name="CozyBvnnies", date_start=datetime.now() - timedelta(days=21)
        )
        logger.info(f"Started crawling task: {task.id}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()
