import os
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    _mgr_available = True
except ImportError:
    _mgr_available = False


@pytest.fixture(scope="function")
def driver(tmp_path):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    if _mgr_available:
        service = Service(ChromeDriverManager().install())
        d = webdriver.Chrome(service=service, options=opts)
    else:
        d = webdriver.Chrome(options=opts)

    d.set_window_size(1280, 800)
    yield d
    d.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        if driver:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = item.name.replace("/", "_")
            screenshot_dir = item.config.rootdir / "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            path = screenshot_dir / f"{name}_{ts}.png"
            driver.save_screenshot(str(path))
            item.user_properties.append(("screenshot", str(path)))
