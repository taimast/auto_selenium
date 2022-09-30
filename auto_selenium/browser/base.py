import typing

from loguru import logger
from pydantic import BaseModel, Field, validator
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from auto_selenium.browser.settings import BrowserArgs, BrowserSettings, PatchedWebElement, by


class Browser(BaseModel):
    args: BrowserArgs = BrowserArgs()
    settings: BrowserSettings = BrowserSettings()

    options: Options = Options()
    service: Service | None = None
    driver: Chrome | None = None

    class Config:
        arbitrary_types_allowed = True

    @validator("driver", "service")
    def validate_driver(cls, v, field):
        raise ValueError(f"{field.name} is not allowed to be set manually, use create_driver() instead")

    def create_driver(self):
        service = Service(**self.settings.dict(by_alias=True, exclude={"implicit_wait"}))
        for arg in self.args.get_args():
            self.options.add_argument(arg)
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.driver.implicitly_wait(self.settings.implicit_wait)
        return self.driver

    def __enter__(self):
        logger.info("Opening browser")
        self.create_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"Closing browser")
        self.driver.quit()
        logger.info(f"Successfully closed browser")

    def fe(self, by=by.id, value=None) -> PatchedWebElement:
        element = self.driver.find_element(by, value)
        return typing.cast(PatchedWebElement, element)

    def fes(self, by=by.id, value=None) -> list[PatchedWebElement]:
        elements = self.driver.find_elements(by, value)
        return typing.cast(list[PatchedWebElement], elements)

    def switch_to(self, handler: int):
        """
        Switches to the window with the given handler
        :param handler: The handler number of the window to switch to
        """
        self.driver.switch_to.window(self.driver.window_handles[handler])

    def get(self, url: str):
        self.driver.get(url)

    def refresh(self):
        self.driver.refresh()

    def get_ip(self):
        self.get("https://api.ipify.org")
        logger.success(f"IP: {self.fe(by.tag_name, 'body').text}")

    def get_user_agent(self):
        self.get("https://www.whatismybrowser.com/detect/what-is-my-user-agent/")
        logger.success(f"User Agent: {self.fe(by.id, 'detected_value').text}")

    def start(self):
        self.get_ip()
        self.get_user_agent()
