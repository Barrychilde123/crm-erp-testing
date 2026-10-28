# -*- coding: utf-8 -*-
import os

import allure
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def open(self, path=""):
        self.driver.get(BASE_URL + path)
        return self

    def el(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click(self, by, value):
        try:
            self.wait.until(EC.element_to_be_clickable((by, value))).click()
        except UnexpectedAlertPresentException:
            self.driver.switch_to.alert.accept()

    def fill(self, by, value, text):
        element = self.el(by, value)
        element.clear()
        element.send_keys(text)

    def text(self, by, value):
        return self.el(by, value).text

    def flash(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".flash")
        return elements[-1].text if elements else ""

    def wait_css_contains(self, css, text):
        def check(d):
            try:
                return text in d.find_element(By.CSS_SELECTOR, css).text
            except (NoSuchElementException, StaleElementReferenceException):
                return False

        self.wait.until(check)

    def wait_body_contains(self, text):
        self.wait_css_contains("body", text)

    def wait_flash(self, text):
        self.wait_css_contains(".flash-stack", text)

    def wait_path(self, pattern):
        self.wait.until(EC.url_matches(pattern))

    def accept_alert(self):
        try:
            self.wait.until(EC.alert_is_present()).accept()
        except Exception:
            pass

    def screenshot(self, name):
        allure.attach(
            self.driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
