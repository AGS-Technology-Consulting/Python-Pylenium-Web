from pages.base_page import BasePage
from pylenium.driver import Pylenium

class SecurePage(BasePage):
    success_message = "#flash"
    logout_button = "a.button.secondary.radius"

    def is_loaded(self):
        return self.py.get(self.success_message).should().be_visible()

    def get_success_message(self) -> str:
        return self.py.get(self.success_message).text().strip()

    def logout(self):
        self.py.get(self.logout_button).click()
