# -*- coding: utf-8 -*-
import allure
from selenium.webdriver.common.by import By

from ui.pages.crm_page import CustomersPage, OpportunitiesPage


@allure.feature("CRM")
@allure.story("客户管理")
@allure.title("新建客户并搜索")
def test_customer_create_and_search(logged_in, unique):
    page = CustomersPage(logged_in)
    name = f"QA-UI-CUST-{unique}"
    page.open_page()
    page.screenshot("客户列表")

    page.create(name, contact="张三", phone="13800005555")
    assert "客户创建成功" in page.flash()

    page.search(name)
    assert name in page.table_text()
    page.screenshot("客户创建并搜索成功")


@allure.feature("CRM")
@allure.story("客户管理")
@allure.title("客户名称必填校验")
def test_customer_required_validation(logged_in):
    page = CustomersPage(logged_in)
    page.open("/crm/customers/new")
    assert page.invalid_name() is True

    page.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
    assert "/crm/customers/new" in logged_in.current_url
    page.screenshot("客户名称必填校验")


@allure.feature("CRM")
@allure.story("客户管理")
@allure.title("编辑客户负责人")
def test_customer_edit_owner(logged_in, customer_factory):
    customer = customer_factory()
    page = CustomersPage(logged_in)
    page.edit_owner(customer["id"], 2)
    assert "客户信息已更新" in page.flash()
    assert "李娜" in logged_in.find_element(By.TAG_NAME, "body").text
    page.screenshot("客户负责人已更新")


@allure.feature("CRM")
@allure.story("商机管道")
@allure.title("新建商机并推进阶段")
def test_opportunity_create_and_stage_update(logged_in, customer_factory, unique):
    customer = customer_factory()
    page = OpportunitiesPage(logged_in)
    name = f"QA-UI-OPP-{unique}"

    page.create(customer["id"], name, amount=10000, stage="qualified")
    assert "商机创建成功" in page.flash()

    page.update_stage(name, "proposal")
    assert "商机已更新" in page.flash()

    page.open_page()
    body = logged_in.find_element(By.TAG_NAME, "body").text
    assert name in body
    assert "¥10,000.00" in body
    page.screenshot("商机阶段推进")


@allure.feature("CRM")
@allure.story("商机管道")
@allure.title("商机管道展示 6 个阶段与商机卡片")
def test_opportunity_pipeline(logged_in):
    page = OpportunitiesPage(logged_in)
    page.open_page()
    assert page.column_count() == 6
    assert page.card_count() >= 8
    page.screenshot("商机管道")
