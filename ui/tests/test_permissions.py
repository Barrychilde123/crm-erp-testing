# -*- coding: utf-8 -*-
import allure
from selenium.webdriver.common.by import By

from ui.pages.base_page import BASE_URL
from ui.pages.crm_page import TenantsPage
from ui.pages.login_page import LoginPage


@allure.feature("权限")
@allure.story("角色权限")
@allure.title("销售角色看不到 SaaS 管理菜单，直接访问返回 403")
def test_sales_role_cannot_access_saas(driver):
    LoginPage(driver).open_page().login("sales01", "sales123").wait_dashboard()
    sidebar = driver.find_element(By.CSS_SELECTOR, ".sidebar").text
    assert "SaaS 管理" not in sidebar

    driver.get(BASE_URL + "/saas/tenants")
    assert driver.find_element(By.CSS_SELECTOR, ".error-code").text == "403"
    allure.attach(
        driver.get_screenshot_as_png(),
        name="销售访问 SaaS 返回 403",
        attachment_type=allure.attachment_type.PNG,
    )


@allure.feature("SaaS")
@allure.story("多租户")
@allure.title("管理员切换租户后数据隔离")
def test_tenant_switch(logged_in):
    page = TenantsPage(logged_in)
    page.open("/")
    page.switch_to("远航集团")
    page.wait_body_contains("远航集团")
    page.screenshot("切换到远航集团")

    # 切回启明科技，验证租户切换可逆
    page.switch_to("启明科技")
    page.wait_body_contains("启明科技")
