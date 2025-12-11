from pages.base_page import BasePage
from pylenium.driver import Pylenium

class LoginPage(BasePage):
    username = "#username"
    password = "#password"
    login_button = "button[type='submit']"
    error_message = "#flash"

    def __init__(self, py: Pylenium):
        super().__init__(py)

    def login(self, username: str, password: str):
        self.type(self.username, username)
        self.type(self.password, password)
        self.click(self.login_button)

    def get_error_message(self) -> str:
        return self.py.get(self.error_message).text().strip()
