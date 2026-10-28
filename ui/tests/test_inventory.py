# -*- coding: utf-8 -*-
import allure

from ui.pages.erp_page import InventoryPage


@allure.feature("ERP")
@allure.story("库存管理")
@allure.title("库存调整：入库、出库与超量出库拦截")
def test_inventory_adjust(logged_in, product_factory):
    product = product_factory(stock=10)
    page = InventoryPage(logged_in)

    page.adjust(product["id"], 5)
    assert "库存调整成功" in page.flash()
    assert page.stock_by_sku(product["sku"]) == 15

    page.adjust(product["id"], -3)
    assert page.stock_by_sku(product["sku"]) == 12

    page.adjust(product["id"], -100, expect="调整后库存不能为负数")
    assert page.stock_by_sku(product["sku"]) == 12
    page.screenshot("库存调整")
