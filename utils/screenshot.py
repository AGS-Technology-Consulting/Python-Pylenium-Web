import os
import allure
from pylenium.driver import Pylenium
from datetime import datetime

def save_screenshot_on_failure(item, report):
    # Find py fixture from test item
    py = item.funcargs.get('py', None)
    if not py:
        return
    os.makedirs("reports/screenshots", exist_ok=True)
    name = f"{item.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("reports/screenshots", name)
     # CORRECT way for Pylenium
    py.screenshot(path)
    # attach to html report via extra if pytest-html is used
    try:
        extra = getattr(report, "extra", [])
        from pytest_html import extras
        extra.append(extras.image(path))
        report.extra = extra
        with open(path, "rb") as image_file:
            allure.attach(image_file.read(), name, allure.attachment_type.PNG)
    except Exception:
        # ignore if pytest-html not installed/available at runtime
        pass
