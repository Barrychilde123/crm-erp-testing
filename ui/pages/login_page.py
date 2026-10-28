# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By

from .base_page import BasePage


class LoginPage(BasePage):
    def open_page(self):
        return self.open("/login")

    def login(self, username, password):
        self.fill(By.ID, "username", username)
        self.fill(By.ID, "password", password)
        self.click(By.CSS_SELECTOR, "button[type=submit]")
        return self

    def wait_dashboard(self):
        self.wait.until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".kpi-grid")
        )
        return self

    def error_message(self):
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".flash"))
        return self.flash()
