# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class SalesOrdersPage(BasePage):
    def create_order(self, customer_id, product_id, qty=1, price=100):
        self.open("/erp/sales-orders/new")
        Select(self.el(By.NAME, "customer_id")).select_by_value(str(customer_id))
        Select(self.el(By.NAME, "product_id")).select_by_value(str(product_id))
        self.fill(By.NAME, "qty", str(qty))
        self.fill(By.NAME, "price", str(price))
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_path(r".*/erp/sales-orders/\d+$")
        return self

    def confirm(self):
        self.click(By.XPATH, "//button[contains(., '确认订单')]")
        self.wait_flash("已确认")
        return self

    def ship(self):
        self.click(By.XPATH, "//button[contains(., '发货出库')]")
        self.accept_alert()
        self.wait_flash("已发货")
        return self

    def issue_invoice(self):
        self.click(By.XPATH, "//button[contains(., '开具发票')]")
        self.wait_flash("发票开具成功")
        return self


class PurchaseOrdersPage(BasePage):
    def create_order(self, supplier_id, product_id, qty=1, price=10):
        self.open("/erp/purchase-orders/new")
        Select(self.el(By.NAME, "supplier_id")).select_by_value(str(supplier_id))
        Select(self.el(By.NAME, "product_id")).select_by_value(str(product_id))
        self.fill(By.NAME, "qty", str(qty))
        self.fill(By.NAME, "price", str(price))
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_path(r".*/erp/purchase-orders/\d+$")
        return self

    def confirm(self):
        self.click(By.XPATH, "//button[contains(., '确认订单')]")
        self.wait_flash("已确认")
        return self

    def receive(self):
        self.click(By.XPATH, "//button[contains(., '收货入库')]")
        self.accept_alert()
        self.wait_flash("已收货")
        return self


class SuppliersPage(BasePage):
    def create(self, name):
        self.open("/erp/suppliers/new")
        self.fill(By.NAME, "name", name)
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_flash("供应商创建成功")
        return self


class ProductsPage(BasePage):
    def update_price(self, product_id, price):
        self.open(f"/erp/products/{product_id}/edit")
        self.fill(By.NAME, "price", str(price))
        self.click(By.CSS_SELECTOR, ".form-actions button[type=submit]")
        self.wait_flash("产品已更新")
        return self


class InventoryPage(BasePage):
    def open_page(self):
        return self.open("/erp/inventory")

    def adjust(self, product_id, qty_delta, note="UI 自动化调整", expect="库存调整成功"):
        self.open("/erp/inventory")
        Select(self.el(By.NAME, "product_id")).select_by_value(str(product_id))
        self.fill(By.NAME, "qty_delta", str(qty_delta))
        self.fill(By.NAME, "note", note)
        self.click(By.CSS_SELECTOR, 'form[action="/erp/inventory/adjust"] button[type=submit]')
        self.wait_flash(expect)
        return self

    def stock_by_sku(self, sku):
        self.open("/erp/inventory")
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table.data tbody tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[0].text.strip() == sku:
                return int(cells[2].text.strip())
        raise AssertionError(f"SKU {sku} not found in inventory table")
