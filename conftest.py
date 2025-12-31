import os
import json
import logging
import shutil
from pathlib import Path

import allure
import pytest
import requests
from faker import Faker

from pylenium.a11y import PyleniumAxe
from pylenium.config import PyleniumConfig, TestCase
from pylenium.driver import Pylenium

from utils.logger import get_logger
from utils.screenshot import save_screenshot_on_failure
from utils.api_helper import api_helper

LOGGER = get_logger("conftest")

# -------------------------------------------------------------------------
# CUSTOM ADDITIONS: env, base_url, screenshots on failure
# -------------------------------------------------------------------------

def _load_env_json():
    here = Path(__file__).resolve().parent
    path = here.joinpath("pylenium.json")
    with path.open() as f:
        return json.load(f)


def pytest_addoption(parser):
    # Pylenium built-in options
    parser.addoption("--browser", action="store", default="", help="chrome | firefox")
    parser.addoption("--local_path", action="store", default="", help="Local driver path")
    parser.addoption("--remote_url", action="store", default="", help="Grid URL")
    parser.addoption("--screenshots_on", action="store", default="", help="true | false")
    parser.addoption("--pylenium_json", action="store", default="", help="path to config")
    parser.addoption("--pylog_level", action="store", default="INFO", help="Logging level")
    parser.addoption("--options", action="store", default="", help="Comma-separated browser options")
    parser.addoption("--caps", action="store", default="", help="Browser capabilities as dict")
    parser.addoption("--page_load_wait_time", action="store", default="", help="Timeout for page-load")
    parser.addoption("--extensions", action="store", default="", help="Comma-separated extension paths")

    # CUSTOM addition
    parser.addoption("--env", action="store", default="qa",
                     help="Environment to run tests against (dev/qa/stage/prod)")


@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def base_url(env):
    cfg = _load_env_json()

    if "environments" in cfg and env in cfg["environments"]:
        return cfg["environments"][env]["url"]

    return cfg.get("url", "http://localhost")


# -------------------------------------------------------------------------
# API HELPER HOOKS - Jenkins Integration
# -------------------------------------------------------------------------

def pytest_sessionstart(session):
    """
    Called before test session starts
    API-1: Create Pipeline Run
    """
    LOGGER.info("=" * 63)
    LOGGER.info("🎯 Python Pylenium Framework Starting")
    LOGGER.info("=" * 63)
    LOGGER.info(f"📅 Starting test session")
    LOGGER.info(f"🌍 Environment: {os.getenv('ENV', 'qa')}")
    LOGGER.info(f"💻 Browser: {os.getenv('BROWSER', 'chrome')}")
    LOGGER.info(f"🎭 Headless: {os.getenv('HEADLESS', 'false')}")
    LOGGER.info("=" * 63)
    
    # API-1: Create Pipeline Run
    api_helper.before_all_tests()


def pytest_sessionfinish(session, exitstatus):
    """
    Called after test session finishes
    API-4: Update Pipeline Run
    """
    LOGGER.info("\n" + "=" * 63)
    LOGGER.info("🏁 Python Pylenium Tests Completed")
    LOGGER.info("=" * 63)
    
    # API-4: Update Pipeline Run
    api_helper.after_all_tests()


# -------------------------------------------------------------------------
# PYLENIUM DEFAULT ROOT FIXTURES (FULL OFFICIAL SET)
# -------------------------------------------------------------------------

@pytest.fixture(scope="function")
def fake() -> Faker:
    return Faker()


@pytest.fixture(scope="function")
def api():
    return requests


@pytest.fixture(scope="session", autouse=True)
def project_root() -> Path:
    return Path(__file__).absolute().parent


@pytest.fixture(scope="session", autouse=True)
def test_results_dir(project_root: Path, request) -> Path:
    session = request.node
    test_results_dir = project_root.joinpath("test_results")

    if test_results_dir.exists():
        shutil.rmtree(test_results_dir, ignore_errors=True)

    test_results_dir.mkdir(parents=True, exist_ok=True)

    for test in session.items:
        try:
            test_results_dir.joinpath(test.name).mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass

    return test_results_dir


@pytest.fixture(scope="session")
def _load_pylenium_json(project_root, request) -> PyleniumConfig:
    custom_path = request.config.getoption("pylenium_json")
    config_file = project_root.joinpath(custom_path or "pylenium.json")

    try:
        with config_file.open() as f:
            data = json.load(f)
        return PyleniumConfig(**data)
    except FileNotFoundError:
        logging.warning(f"Config file not found at {config_file}. Using defaults.")
        return PyleniumConfig()


@pytest.fixture(scope="session")
def _override_pylenium_config_values(_load_pylenium_json: PyleniumConfig, request) -> PyleniumConfig:
    config = _load_pylenium_json

    # override CLI values
    r = request.config

    if r.getoption("--remote_url"):
        config.driver.remote_url = r.getoption("--remote_url")

    if r.getoption("--options"):
        config.driver.options = [o.strip() for o in r.getoption("--options").split(",")]

    if r.getoption("--browser"):
        config.driver.browser = r.getoption("--browser")

    if r.getoption("--local_path"):
        config.driver.local_path = r.getoption("--local_path")

    if r.getoption("--caps"):
        config.driver.capabilities = json.loads(r.getoption("--caps"))

    if r.getoption("--page_load_wait_time").isdigit():
        config.driver.page_load_wait_time = int(r.getoption("--page_load_wait_time"))

    if r.getoption("--screenshots_on"):
        config.logging.screenshots_on = r.getoption("--screenshots_on").lower() == "true"

    if r.getoption("--extensions"):
        config.driver.extension_paths = [e.strip() for e in r.getoption("--extensions").split(",")]

    if r.getoption("--pylog_level"):
        config.logging.pylog_level = r.getoption("--pylog_level").upper()

    return config


@pytest.fixture(scope="function")
def py_config(_override_pylenium_config_values) -> PyleniumConfig:
    return _override_pylenium_config_values.copy()


@pytest.fixture(scope="function")
def test_case(test_results_dir: Path, request) -> TestCase:
    test_name = request.node.name
    test_path = test_results_dir.joinpath(test_name)
    return TestCase(name=test_name, file_path=test_path)


# -------------------------------------------------------------------------
# FINAL PY FIXTURE (MERGED CUSTOM + OFFICIAL)
# -------------------------------------------------------------------------

@pytest.fixture(scope="function")
def py(test_case: TestCase, py_config: PyleniumConfig, base_url, request):
    """
    Final merged Py fixture:
    - Initializes Pylenium
    - Automatically navigates to base_url
    - Supports passed/failed/skip with screenshots
    """
    py = Pylenium(py_config)

    # Start from base URL always
    py.visit(base_url)

    yield py

    try:
        if request.node.report.failed:
            if py_config.logging.screenshots_on:
                screenshot = py.screenshot(str(test_case.file_path.joinpath("failed.png")))
                allure.attach(screenshot, "failed.png", allure.attachment_type.PNG)

        # No special handling for passed/skipped cases now

    except Exception:
        logging.error("Failed to capture screenshot.")
    py.quit()


@pytest.fixture(scope="function")
def axe(py) -> PyleniumAxe:
    return PyleniumAxe(py.webdriver)


# -------------------------------------------------------------------------
# PYTEST HOOKS FOR API INTEGRATION
# -------------------------------------------------------------------------

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Capture test results and send to API
    Also handles screenshots on failure
    """
    outcome = yield
    rep = outcome.get_result()
    
    # Store report in item for later access
    setattr(item, "report", rep)
    
    # API-3: Create Test Case (after test execution)
    if rep.when == "call":
        test_name = item.name
        duration = rep.duration
        
        if rep.passed:
            status = "passed"
            error_message = None
        elif rep.failed:
            status = "failed"
            error_message = str(rep.longrepr) if rep.longrepr else "Test failed"
        elif rep.skipped:
            status = "skipped"
            error_message = str(rep.longrepr) if rep.longrepr else "Test skipped"
        else:
            status = "unknown"
            error_message = None
        
        # Send to API
        api_helper.after_each_test(test_name, status, duration, error_message)
        
        # Screenshot on failure
        if rep.failed:
            from utils.screenshot import save_screenshot_on_failure
            save_screenshot_on_failure(item, rep)
    
    return rep