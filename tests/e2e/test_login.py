import pytest
from pages.login_page import LoginPage
from pages.secure_page import SecurePage
from utils.logger import get_logger

LOGGER = get_logger("test_login")


@pytest.mark.smoke
def test_login_success(py):
    LOGGER.info("Starting test: test_login_success")
    login = LoginPage(py)
    secure = SecurePage(py)

    login.login("tomsmith", "SuperSecretPassword!")
    
    assert secure.is_loaded(), "Secure page should load after valid login"
    assert "You logged into a secure area!" in secure.get_success_message()

    LOGGER.info("Test passed: test_login_success")


@pytest.mark.regression
def test_login_invalid_password(py):
    LOGGER.info("Starting test: test_login_invalid_password")
    login = LoginPage(py)

    login.login("tomsmith", "WrongPassword")

    error = login.get_error_message()

    assert "Your password is invalid!" in error, "Error message should show invalid password"

    LOGGER.info("Test passed: test_login_invalid_password (negative case)")


@pytest.mark.regression
def test_login_invalid_username(py):
    LOGGER.info("Starting test: test_login_invalid_username")
    login = LoginPage(py)

    login.login("wrongUser", "SuperSecretPassword!")

    error = login.get_error_message()

    assert "Your username is invalid!" in error

    LOGGER.info("Negative test passed")


@pytest.mark.skip(reason="Skipping this test based on requirement")
def test_login_skipped():
    pass


def test_expected_fail_case(py):
    """
    This test is intentionally written to FAIL to demonstrate failure reporting,
    screenshots, and logger output.
    """
    LOGGER.info("Starting test: test_expected_fail_case")
    login = LoginPage(py)

    login.login("tomsmith", "SuperSecretPassword!")

    # Intentionally wrong expectation
    assert False, "Intentional failure to validate screenshot-on-failure"

