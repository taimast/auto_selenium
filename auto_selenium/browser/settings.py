from pathlib import Path

from pydantic import BaseModel, Field, StrictStr, FilePath
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

class by:
    id = "id"
    xpath = "xpath"
    link_text = "link text"
    partial_link_text = "partial link text"
    name = "name"
    tag_name = "tag name"
    class_name = "class name"
    css_selector = "css selector"


WebElement.fe = WebElement.find_element
WebElement.fes = WebElement.find_elements


class PatchedWebElement(WebElement):
    def fe(self, by=by.id, value=None) -> "PatchedWebElement":
        pass

    def fes(self, by=by.id, value=None) -> list["PatchedWebElement"]:
        pass


class BrowserArgs(BaseModel):
    no_sandbox: bool = Field(True, alias="--no-sandbox")
    headless: bool = Field(False, alias="--headless")
    disable_blink_features: StrictStr | None = Field(alias="--disable-blink-features", default="AutomationControlled", )
    user_agent: str | None = Field(None, alias="--user-agent")

    class Config:
        allow_population_by_field_name = True

    def get_args(self) -> list[str]:
        settings = []
        for key, value in self.dict(by_alias=True, exclude_none=True).items():
            if isinstance(value, bool):
                if value:
                    settings.append(key)
            else:
                settings.append(f"{key}={value}")
        return settings


class BrowserSettings(BaseModel):
    log_path: Path = Field(default="browser.log")
    driver_path: FilePath = Field(default_factory=ChromeDriverManager().install, alias="executable_path")

    implicit_wait: int = Field(default=10, alias="implicitly_wait")

    class Config:
        arbitrary_types_allowed = True

    def get_settings(self) -> dict:
        return self.dict(exclude_none=True)
