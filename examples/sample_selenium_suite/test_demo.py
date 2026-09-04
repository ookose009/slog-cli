"""
Demo Selenium suite against https://the-internet.herokuapp.com
Includes one intentionally timing-sensitive test to demonstrate flakiness detection.
"""
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://the-internet.herokuapp.com"
WAIT = 10


def test_login_success(driver):
    driver.get(f"{BASE}/login")
    driver.find_element(By.ID, "username").send_keys("tomsmith")
    driver.find_element(By.ID, "password").send_keys("SuperSecretPassword!")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    WebDriverWait(driver, WAIT).until(EC.url_contains("/secure"))
    assert "You logged into a secure area!" in driver.page_source


def test_login_invalid_credentials(driver):
    driver.get(f"{BASE}/login")
    driver.find_element(By.ID, "username").send_keys("bad")
    driver.find_element(By.ID, "password").send_keys("bad")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    assert "Your username is invalid!" in driver.page_source


def test_dynamic_loading(driver):
    driver.get(f"{BASE}/dynamic_loading/1")
    driver.find_element(By.CSS_SELECTOR, "#start button").click()
    WebDriverWait(driver, WAIT).until(
        EC.text_to_be_present_in_element((By.ID, "finish"), "Hello World!")
    )
    assert "Hello World!" in driver.find_element(By.ID, "finish").text


def test_disappearing_element_timing_sensitive(driver):
    """
    Visits a page where elements appear/disappear randomly.
    Intentionally uses a very short timeout to make this occasionally flaky.
    """
    driver.get(f"{BASE}/disappearing_elements")
    # Very short sleep — element may or may not be present, demonstrating flakiness
    time.sleep(0.05)
    elements = driver.find_elements(By.CSS_SELECTOR, "li a")
    # The Gallery link only appears sometimes; this assert will sometimes fail
    nav_texts = [el.text for el in elements]
    assert "Gallery" in nav_texts, f"Gallery not in nav: {nav_texts}"
