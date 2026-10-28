# -*- coding: utf-8 -*-
import allure

from ui.pages.base_page import BASE_URL
from ui.pages.login_page import LoginPage


@allure.feature("登录")
@allure.story("正确账号密码")
@allure.title("管理员登录后进入仪表盘")
def test_login_success(driver):
    page = LoginPage(driver)
    page.open_page().login("admin", "admin123").wait_dashboard()
    assert "仪表盘" in driver.title
    assert "活跃客户" in driver.find_element("css selector", "body").text
    page.screenshot("登录成功-仪表盘")


@allure.feature("登录")
@allure.story("错误密码")
@allure.title("错误密码登录失败并提示")
def test_login_wrong_password(driver):
    page = LoginPage(driver)
    page.open_page().login("admin", "wrong-password")
    assert "用户名或密码错误" in page.error_message()
    assert "/login" in driver.current_url
    page.screenshot("登录失败提示")


@allure.feature("权限")
@allure.story("未登录访问")
@allure.title("未登录访问 CRM 被重定向到登录页")
def test_unauthenticated_redirect(driver):
    driver.get(BASE_URL + "/crm/customers")
    assert "/login" in driver.current_url
    assert "登录" in driver.title
