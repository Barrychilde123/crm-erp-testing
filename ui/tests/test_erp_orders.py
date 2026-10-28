# -*- coding: utf-8 -*-
import allure

from ui.pages.erp_page import (
    InventoryPage,
    ProductsPage,
    PurchaseOrdersPage,
    SalesOrdersPage,
    SuppliersPage,
)


@allure.feature("ERP")
@allure.story("销售订单")
@allure.title("销售订单创建-确认-发货并扣减库存")
def test_sales_order_flow(logged_in, customer_factory, product_factory):
    customer = customer_factory()
    product = product_factory(stock=10, price=100)

    page = SalesOrdersPage(logged_in)
    page.create_order(customer["id"], product["id"], qty=2, price=100)
    assert "销售订单创建成功" in page.flash()
    body = logged_in.find_element("tag name", "body").text
    assert customer["name"] in body
    assert product["name"] in body
    assert "200.00" in body
    page.screenshot("销售订单创建成功")

    page.confirm()
    assert "已确认" in page.flash()
    page.ship()
    assert "已发货" in page.flash()
    page.screenshot("销售订单已发货")

    page.issue_invoice()
    assert "已开票" in logged_in.find_element("tag name", "body").text
    page.screenshot("销售订单已开票")

    inventory = InventoryPage(logged_in)
    assert inventory.stock_by_sku(product["sku"]) == 8


@allure.feature("ERP")
@allure.story("基础资料")
@allure.title("新建供应商并修改产品售价")
def test_supplier_and_product_master_data(logged_in, product_factory, unique):
    supplier_name = f"QA-UI-SUP-{unique}"
    SuppliersPage(logged_in).create(supplier_name)
    assert "供应商创建成功" in SuppliersPage(logged_in).flash()
    assert supplier_name in logged_in.find_element("tag name", "body").text

    product = product_factory(stock=3, price=100)
    page = ProductsPage(logged_in)
    page.update_price(product["id"], 120)
    assert "产品已更新" in page.flash()
    assert "120.00" in logged_in.find_element("tag name", "body").text
    page.screenshot("产品售价已更新")


@allure.feature("ERP")
@allure.story("采购订单")
@allure.title("采购订单创建-确认-收货并增加库存")
def test_purchase_order_flow(logged_in, product_factory):
    product = product_factory(stock=0, price=50)

    page = PurchaseOrdersPage(logged_in)
    page.create_order(1, product["id"], qty=5, price=50)
    assert "采购订单创建成功" in page.flash()
    page.screenshot("采购订单创建成功")

    page.confirm()
    assert "已确认" in page.flash()
    page.receive()
    assert "已收货" in page.flash()
    page.screenshot("采购订单已收货")

    inventory = InventoryPage(logged_in)
    assert inventory.stock_by_sku(product["sku"]) == 5
