import logging
import re
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from nanoid import generate
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from config.config import settings
from extractors.base_extractor import BaseExtractor
from models.data_models import Author, ExtractionResult, Media, Post, Source
from scrapers.selenium_scraper import WebScraper

logger = logging.getLogger(__name__)


class LinkedinExtractor(BaseExtractor):
    def __init__(self):
        self.scraper = WebScraper()
        self.base_url = "https://www.linkedin.com"

    def extract(self, source_config: Source) -> ExtractionResult:
        author_posts_url = (
            f"{self.base_url}/in/{source_config.author}/recent-activity/all/"
        )
        posts = []
        all_medias = []

        with self.scraper.create_driver() as driver:
            try:
                self._login(driver)
                driver.get(author_posts_url)
                self.scraper.wait_for_element(
                    driver, ".//div[@class='scaffold-finite-scroll__content']"
                )
                self.scraper.scroll_page(driver)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                author = self._parse_author_profile(soup, source_config.author)
                posts_soup = soup.select("div.scaffold-finite-scroll__content li")
                for post_soup in posts_soup[: source_config.limit]:
                    try:
                        result = self._parse_post(post_soup, author.id)
                        if result:
                            post, medias = result
                            if (
                                post
                                and post.timestamp
                                and post.timestamp >= source_config.date_start
                            ):
                                posts.append(post)
                                all_medias.extend(medias)
                    except Exception as e:
                        logger.warning(f"Failed to extract post: {str(e)}")
                        continue

                return ExtractionResult(author=author, posts=posts, medias=all_medias)

            except TimeoutException:
                logger.error(f"Timeout while loading {author_posts_url}")
                raise
            except Exception as e:
                logger.error(f"Error extracting data from {author_posts_url}: {e}")
                raise

    def _login(self, driver):
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.execute_script(
            "document.getElementById('rememberMeOptIn-checkbox').checked = false;"
        )
        email = driver.find_element(By.ID, "username")
        email.send_keys(settings.LINKEDIN_EMAIL)

        password = driver.find_element(By.ID, "password")
        password.send_keys(settings.LINKEDIN_PASSWORD)

        password.submit()

    def _parse_post(self, post_element, author_id):

        post_id = generate(size=8)

        post_url = None
        post_div = post_element.find("div", attrs={"data-urn": True})
        if post_div:
            activity_urn = post_div["data-urn"]
            post_url = f"https://www.linkedin.com/feed/update/{activity_urn}"

        post_time = None
        actor_container = post_element.find(
            "div", {"class": "update-components-actor__container"}
        )
        if actor_container:
            time_tag = actor_container.find(
                "span", {"class": "update-components-actor__sub-description"}
            )
            if time_tag:
                post_time = self._convert_relative_date(time_tag.get_text(strip=True))

        post_content = None
        content_div = post_element.find("div", {"class": "update-components-text"})
        if content_div:
            post_content = content_div.get_text(separator="\n", strip=True)

        post_reactions = 0
        post_comments = 0
        social_counts_div = post_element.find(
            "div", {"class": "social-details-social-counts"}
        )
        if social_counts_div:
            reaction_item = social_counts_div.find(
                "li", {"class": "social-details-social-counts__reactions"}
            )
            if reaction_item:
                button_tag = reaction_item.find("button")
                if button_tag and button_tag.has_attr("aria-label"):
                    raw_reactions = button_tag["aria-label"].split(" ")[0]
                    post_reactions = self._convert_abbreviated_to_number(raw_reactions)

            comment_item = social_counts_div.find(
                "li", {"class": "social-details-social-counts__comments"}
            )
            if comment_item:
                cbutton_tag = comment_item.find("button")
                if cbutton_tag and cbutton_tag.has_attr("aria-label"):
                    raw_comments = cbutton_tag["aria-label"].split(" ")[0]
                    post_comments = self._convert_abbreviated_to_number(raw_comments)

        medias = [
            Media(id=f"{post_id}-{i}", post_id=post_id, original_url=img["src"])
            for i, img in enumerate(post_element.find_all("img"))
            if img.get("src")
        ]

        post = Post(
            id=post_id,
            url=post_url,
            text=post_content,
            timestamp=post_time,
            num_likes=post_reactions,
            num_comments=post_comments,
            author_id=author_id,
        )

        return post, medias

    def _parse_author_profile(self, author_profile_soup: BeautifulSoup, author_id: str):
        author_name = (
            author_profile_soup.select_one('a[href*="/in/"] h3').get_text(strip=True)
            if author_profile_soup.select_one('a[href*="/in/"] h3')
            else None
        )

        author_path = author_profile_soup.select_one('a[href*="/in/"]')["href"]
        author_url = f"{self.base_url}{author_path}" if author_path else None

        author_headline = (
            author_profile_soup.select_one('div[class*="break-words"] h4').get_text(
                strip=True
            )
            if author_profile_soup.select_one('div[class*="break-words"] h4')
            else None
        )

        return Author(
            id=author_id, name=author_name, url=author_url, headline=author_headline
        )

    def _convert_abbreviated_to_number(self, s):
        s = s.upper().strip()
        if "K" in s:
            return int(float(s.replace("K", "")) * 1000)
        elif "M" in s:
            return int(float(s.replace("M", "")) * 1000000)
        else:
            try:
                return int(s)
            except ValueError:
                return 0

    def _convert_relative_date(self, relative_str: str) -> datetime | None:

        match = re.search(r"(\d+)\s*(w|d|h|mo?)", relative_str.lower())
        if not match:
            return None

        number = int(match.group(1))
        unit = match.group(2)
        now = datetime.now()

        if unit == "w":
            return now - timedelta(weeks=number)
        elif unit == "d":
            return now - timedelta(days=number)
        elif unit == "h":
            return now - timedelta(hours=number)
        elif unit in ["mo", "m"]:
            return now - timedelta(days=number * 30)

        return None


if __name__ == "__main__":
    extractor = LinkedinExtractor()
    result = extractor.extract(
        Source(
            author="etnikhalili",
            date_start=datetime.now() - timedelta(days=45),
            source_type="linkedin",
            limit=100,
        )
    )
