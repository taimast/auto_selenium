import base64
import io
import json
import zipfile
from pathlib import Path

import yaml
from loguru import logger
from pydantic import BaseModel, FilePath, AnyUrl
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


class CookieMixin(BaseModel):
    """Миксин для сохранения и загрузки кук"""
    driver: Chrome
    cookies_file: FilePath

    class Config:
        arbitrary_types_allowed = True

    def save_cookies(self):
        cookies = self.driver.get_cookies()
        if cookies:
            logger.debug("Saving cookies")
            with open(self.cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
        else:
            logger.debug(f"Not have cookies")

    def load_cookies(self):
        if self.cookies_file.exists():
            logger.debug("Loading cookies")
            with open(self.cookies_file, "r") as f:
                cookies: list = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
        else:
            logger.debug("Cookie file not found")


class ProxyMixin(BaseModel):
    """Миксин для установки прокси"""
    options: Options
    proxy: AnyUrl

    class Config:
        arbitrary_types_allowed = True

    def prepare_extension(self) -> str:
        """Подготовка расширения для авторизации прокси

        :return: base64 строка
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zp:
            data = yaml.safe_load(Path('../proxy_config.yaml').read_text())

            zp.writestr("manifest.json", data['manifest_json'])
            zp.writestr("background.js", data['background_js'] % (
                self.proxy.scheme,
                self.proxy.host,
                self.proxy.port,
                self.proxy.user,
                self.proxy.password
            ))
        return base64.b64encode(zip_buffer.getvalue()).decode("utf-8")

    def set_proxy(self) -> None:
        """Установка прокси"""
        if self.proxy.host and self.proxy.port:
            if self.proxy.user and self.proxy.password:
                self.options.add_encoded_extension(self.prepare_extension())
            else:
                self.options.add_argument(f"--proxy-server={self.proxy}")
                logger.success(f"Proxy server: {self.proxy}")
        else:
            logger.debug(f"Прокси {self.proxy} не найден")
            raise ValueError("Неверный формат прокси. Пример: http://ip:port или http://user:password@ip:port")
