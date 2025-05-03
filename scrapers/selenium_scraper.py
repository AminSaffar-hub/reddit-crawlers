import time
from contextlib import contextmanager

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.config import settings


class WebScraper:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

    @contextmanager
    def create_driver(self):
        driver = webdriver.Remote(
            command_executor=settings.SELENIUM_HUB_URL,
            options=self.chrome_options,
        )

        driver.set_page_load_timeout(45)
        driver.set_script_timeout(45)

        try:
            yield driver
        finally:
            driver.quit()

    def wait_for_element(self, driver, selector, timeout=30):
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, selector))
        )
        time.sleep(2)

    def scroll_page(self, driver, scroll_pause_time=2):
        last_height = 0
        attempt = 0

        while attempt < 5:
            driver.execute_script(
                "window.scrollTo(0, document.documentElement.scrollHeight);"
            )
            time.sleep(3)

            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script(
                        "return document.documentElement.scrollHeight"
                    )
                    > last_height
                )
                last_height = driver.execute_script(
                    "return document.documentElement.scrollHeight"
                )
                attempt = 0
            except TimeoutException:
                attempt += 1
