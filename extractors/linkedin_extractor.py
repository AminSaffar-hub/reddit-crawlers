import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

from extractors.base_extractor import BaseExtractor
from models.data_models import Source
from scrapers.selenium_scraper import WebScraper

logger = logging.getLogger(__name__)


class LinkedinExtractor(BaseExtractor):
    def __init__(self):
        self.scraper = WebScraper()
        self.base_url = "https://www.linkedin.com"

    def extract(self, source_config: Source):
        author_posts_url = f"{self.base_url}/user/{source_config.author}/submitted/?sort=top&t={source_config.time_filter}"
        posts = []
        all_medias = []

        with self.scraper.create_driver() as driver:
            try:
                driver.get(author_posts_url)
                # .//div[@class="scaffold-finite-scroll__content"]//li
                self.scraper.wait_for_element(
                    driver, ".//div[@class='scaffold-finite-scroll__content']"
                )
                self.scraper.scroll_page(driver)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                author = self._parse_author_profile(soup)
                posts_soup = soup.select("div.scaffold-finite-scroll__content li")

                for post_soup in posts_soup[: source_config.limit]:
                    post, medias = self._parse_post(post_soup, author.id)
                    if post and post.timestamp >= source_config.date_start:
                        posts.append(post)
                        all_medias.extend(medias)

            except TimeoutException:
                logger.error(f"Timeout while loading {author_posts_url}")
            except Exception as e:
                logger.error(f"Error extracting data from {author_posts_url}: {e}")

    def _parse_post(self, post_element, author_id):
        pass

    def _parse_author_profile(self, author_profile_soup: BeautifulSoup):
        pass


if __name__ == "__main__":
    extractor = LinkedinExtractor()
    extractor.extract(
        Source(
            author="test",
            date_start=datetime.now() - timedelta(days=21),
            limit=10,
        )
    )
