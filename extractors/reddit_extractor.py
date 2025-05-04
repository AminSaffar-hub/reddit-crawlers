import logging
from datetime import datetime, timedelta
from typing import List, Tuple

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

from extractors.base_extractor import BaseExtractor
from models.data_models import Author, Media, Post, Source
from scrapers.selenium_scraper import WebScraper
from storage import minio_storage

logger = logging.getLogger(__name__)


class RedditExtractor(BaseExtractor):
    def __init__(self):
        self.scraper = WebScraper()
        self.base_url = "https://www.reddit.com"

    def extract(self, source_config: Source):

        author_posts_url = (
            f"{self.base_url}/user/{source_config.author}/submitted/?sort=top&t=month"
        )
        posts = []
        all_medias = []

        with self.scraper.create_driver() as driver:
            try:
                driver.get(author_posts_url)
                self.scraper.wait_for_element(driver, ".//shreddit-feed")

                self.scraper.scroll_page(driver)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                author = self._parse_author_profile(soup)
                posts_soup = soup.find_all("shreddit-post")
                for post_soup in posts_soup[: source_config.limit]:
                    post, medias = self._parse_post(post_soup, author.id)
                    if post and post.timestamp >= source_config.date_start:
                        posts.append(post)
                        all_medias.extend(medias)
            except TimeoutException:
                logger.error(f"Timeout while loading {author_posts_url}")
            except Exception as e:
                logger.error(f"Error extracting data from {author_posts_url}: {e}")

        return author, posts, all_medias

    def _parse_post(self, post_element, author_id) -> Tuple[Post, List[Media]]:
        try:
            base_attributes = {
                "timestamp": post_element.get("created-timestamp"),
                "post_id": post_element.get("id"),
                "num_likes": int(post_element.get("num_likes") or 0),
                "comments": int(post_element.get("comment-count") or 0),
                "permalink": post_element.get("permalink"),
                "subreddit": post_element.get("subreddit-name"),
            }

            title_element = post_element.find(
                "a", id=lambda x: x and x.startswith("post-title-")
            )
            title = title_element.text.strip() if title_element else ""

            content_element = post_element.find(
                "div", id=lambda x: x and x.endswith("-post-rtjson-content")
            )
            content_text = ""
            if content_element:
                paragraphs = content_element.find_all(["p", "li"])
                content_text = "\n".join(p.text.strip() for p in paragraphs)

            img_elements = post_element.find_all("img", class_="media-lightbox-img")
            media_urls = [
                img_element.get("src")
                for img_element in img_elements
                if img_element.get("src")
                and any(
                    format in img_element.get("src")
                    for format in [".jpg", ".jpeg", ".png", ".gif"]
                )
            ]

            timestamp = datetime.fromisoformat(
                base_attributes["timestamp"].replace("+0000", "+00:00")
            ).replace(tzinfo=None)

            post = Post(
                id=base_attributes["post_id"],
                text=content_text,
                title=title,
                timestamp=timestamp,
                num_likes=int(base_attributes["score"]),
                num_comments=int(base_attributes["comments"]),
                url=f"https://reddit.com{base_attributes['permalink']}",
                author_id=author_id,
            )

            medias = []
            for i, media_url in enumerate(media_urls):
                medias.append(
                    Media(
                        id=f"{post.id}_{i}",
                        post_id=post.id,
                        original_url=media_url,
                        hosted_url=None,
                    )
                )

            return post, medias

        except Exception as e:
            logger.error(f"Error parsing post: {str(e)}")
            return None

    def _parse_author_profile(self, author_profile_soup: BeautifulSoup) -> Author:
        author_id = author_profile_soup.find("shreddit-post").get("author-id")
        author_name = author_profile_soup.find("shreddit-post").get("author")
        joined_date = author_profile_soup.find("time", {"data-testid": "cake-day"}).get(
            "datetime"
        )
        karma = author_profile_soup.find_all("span", {"data-testid": "karma-number"})

        return Author(
            id=author_id,
            name=author_name,
            joined_date=datetime.strptime(joined_date, "%Y-%m-%dT%H:%M:%S.%fZ"),
            publication_score=self._format_int(karma[0].text),
            comment_score=self._format_int(karma[1].text),
        )

    def _format_int(self, text: str) -> int:
        try:
            return int(text.strip().replace(",", ""))
        except ValueError:
            return 0


if __name__ == "__main__":
    extractor = RedditExtractor()
    results = extractor.extract(
        Source(
            author="CozyBvnnies",
            date_start=datetime.now() - timedelta(days=21),
            limit=10,
        ),
    )
    minio_s = minio_storage.MinIOHandler(
        {
            "endpoint": "localhost:9000",
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "secure": False,
        }
    )
    minio_s.store_author(results[0])
    for post in results[1]:
        minio_s.store_post(post)
    for media in results[2]:
        minio_s.store_media(media)
