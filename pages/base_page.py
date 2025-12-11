from pylenium.driver import Pylenium
from utils.logger import get_logger

LOGGER = get_logger("base_page")

class BasePage:
    def __init__(self, py: Pylenium):
        self.py = py

    def open(self, path: str = ""):
        base = self.py.session.url  # pylenium manages base url; but we keep flexible
        self.py.visit(path)
        LOGGER.info("Opened URL: %s", path)

    def find(self, selector: str):
        """Use Pylenium's .get() or .find by css/xpath"""
        return self.py.get(selector)

    def click(self, selector: str):
        el = self.find(selector)
        el.click()
        LOGGER.info("Clicked: %s", selector)

    def type(self, selector: str, text: str):
        el = self.find(selector)
        el.clear()
        el.type(text)
        LOGGER.info("Typed into %s -> %s", selector, text)

    def is_visible(self, selector: str, timeout: int = 5) -> bool:
        return self.py.should().contain(selector).is_displayed()
