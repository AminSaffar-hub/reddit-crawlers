import argparse
import logging
from datetime import datetime, timedelta

from celery_app import app
from celery_tasks import tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Social Media Scraper")
    parser.add_argument(
        "--source-type",
        type=str,
        choices=["reddit", "linkedin"],
        required=True,
        help="Type of source to scrape (reddit or linkedin)",
    )
    parser.add_argument(
        "--author",
        type=str,
        required=True,
        help="Username of the author to scrape",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=21,
        help="Number of days to look back (default: 21)",
    )
    args = parser.parse_args()

    app.connection().ensure_connection(timeout=3)

    try:
        task = tasks.crawl_author.delay(
            author_name=args.author,
            date_start=datetime.now() - timedelta(days=args.days),
            source_type=args.source_type,
        )
        logger.info(
            f"Started crawling task for {args.source_type} user {args.author}: {task.id}"
        )

    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()
