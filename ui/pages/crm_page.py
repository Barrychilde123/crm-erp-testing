# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class CustomersPage(BasePage):
    def open_page(self):
        return self.open("/crm/customers")

    def create(self, name, contact="UI 自动化", phone="13800007777"):
        self.open("/crm/customers/new")
        self.fill(By.NAME, "name", name)
        self.fill(By.NAME, "contact", contact)
        self.fill(By.NAME, "phone", phone)
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_path(r".*/crm/customers$")
        return self

    def search(self, keyword):
        self.fill(By.NAME, "q", keyword)
        self.click(By.CSS_SELECTOR, ".search-form button[type=submit]")
        self.wait.until(EC.url_contains("q="))
        self.wait_css_contains("table.data tbody", keyword)
        return self

    def table_text(self):
        return self.text(By.CSS_SELECTOR, "table.data tbody")

    def edit_owner(self, customer_id, owner_id):
        self.open(f"/crm/customers/{customer_id}/edit")
        Select(self.el(By.NAME, "owner_id")).select_by_value(str(owner_id))
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_flash("客户信息已更新")
        return self

    def invalid_name(self):
        return self.driver.execute_script(
            "return !document.querySelector('input[name=name]').checkValidity()"
        )


class OpportunitiesPage(BasePage):
    def open_page(self):
        return self.open("/crm/opportunities")

    def column_count(self):
        return len(self.driver.find_elements(By.CSS_SELECTOR, ".pipeline-col"))

    def card_count(self):
        return len(self.driver.find_elements(By.CSS_SELECTOR, ".pipeline-card"))

    def create(self, customer_id, name, amount=10000, stage="qualified", expected_date="2026-12-31"):
        self.open("/crm/opportunities/new")
        self.fill(By.NAME, "name", name)
        Select(self.el(By.NAME, "customer_id")).select_by_value(str(customer_id))
        self.fill(By.NAME, "amount", str(amount))
        Select(self.el(By.NAME, "stage")).select_by_value(stage)
        self.fill(By.NAME, "expected_date", expected_date)
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_flash("商机创建成功")
        return self

    def update_stage(self, name, stage="proposal"):
        self.open_page()
        self.click(
            By.XPATH,
            f"//a[contains(@class,'pipeline-card')][contains(., '{name}')]",
        )
        self.wait.until(lambda d: d.find_elements(By.NAME, "stage"))
        Select(self.el(By.NAME, "stage")).select_by_value(stage)
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_flash("商机已更新")
        return self


class TenantsPage(BasePage):
    def switch_to(self, tenant_name):
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".tenant-switch select"))
        select = Select(self.driver.find_element(By.CSS_SELECTOR, ".tenant-switch select"))
        select.select_by_visible_text(tenant_name)
        self.wait_css_contains(".page-sub", tenant_name)
        return self
