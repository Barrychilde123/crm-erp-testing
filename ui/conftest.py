# -*- coding: utf-8 -*-
import os
import time
import uuid

import allure
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
API = BASE_URL + "/api"


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--lang=zh-CN")
    browser = webdriver.Edge(options=options)
    browser.set_window_size(1440, 1000)
    yield browser
    browser.quit()


@pytest.fixture
def logged_in(driver):
    from ui.pages.login_page import LoginPage

    LoginPage(driver).open_page().login("admin", "admin123").wait_dashboard()
    return driver


@pytest.fixture(scope="session")
def api_admin():
    session = requests.Session()
    response = session.post(
        API + "/login", json={"username": "admin", "password": "admin123"}, timeout=10
    )
    assert response.status_code == 200, response.text
    return session


@pytest.fixture
def unique():
    return f"{int(time.time())}-{uuid.uuid4().hex[:6]}"


@pytest.fixture
def customer_factory(api_admin, unique):
    def create(name=None):
        name = name or f"QA-UI-CUST-{unique}-{uuid.uuid4().hex[:4]}"
        response = api_admin.post(
            API + "/customers",
            json={"name": name, "contact": "UI 测试", "phone": "13800006666"},
            timeout=10,
        )
        assert response.status_code == 201, response.text
        return {"id": response.json()["data"]["id"], "name": name}

    return create


@pytest.fixture
def product_factory(api_admin):
    def create(stock=10, price=100.0):
        suffix = uuid.uuid4().hex[:8]
        sku = f"QA-UI-{suffix}"
        name = f"QA-UI-产品-{suffix}"
        response = api_admin.post(
            API + "/products",
            json={
                "sku": sku,
                "name": name,
                "category": "UI 测试",
                "price": price,
                "cost": price * 0.6,
                "stock": stock,
                "safety_stock": 2,
            },
            timeout=10,
        )
        assert response.status_code == 201, response.text
        return {"id": response.json()["data"]["id"], "sku": sku, "name": name}

    return create


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        browser = item.funcargs.get("driver") or item.funcargs.get("logged_in")
        if browser is not None:
            try:
                allure.attach(
                    browser.get_screenshot_as_png(),
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                pass
