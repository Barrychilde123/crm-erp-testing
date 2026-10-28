# -*- coding: utf-8 -*-
"""CRM/ERP 测试靶场接口测试：pytest api/test_api.py -v"""
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
API = BASE_URL + "/api"
ADMIN = ("admin", "admin123")
SALES = ("sales01", "sales123")
ADMIN_B = ("admin_b", "admin123")


def login(username, password):
    session = requests.Session()
    response = session.post(
        API + "/login", json={"username": username, "password": password}, timeout=10
    )
    assert response.status_code == 200, response.text
    assert response.json()["code"] == 0
    return session


@pytest.fixture(scope="session")
def admin():
    return login(*ADMIN)


@pytest.fixture(scope="session")
def admin_b():
    return login(*ADMIN_B)


@pytest.fixture
def unique():
    return f"{int(time.time())}-{uuid.uuid4().hex[:6]}"


def make_customer(session, unique):
    response = session.post(
        API + "/customers",
        json={
            "name": f"QA-API-CUST-{unique}",
            "contact": "接口测试",
            "phone": "13800001234",
            "email": "qa@example.com",
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def make_product(session, unique, stock=10, price=100.0):
    response = session.post(
        API + "/products",
        json={
            "sku": f"QA-API-{unique}",
            "name": f"QA-API-产品-{unique}",
            "category": "测试",
            "price": price,
            "cost": 60,
            "stock": stock,
            "safety_stock": 2,
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def stock_of(session, product_id):
    response = session.get(API + "/inventory", timeout=10)
    assert response.status_code == 200
    for item in response.json()["data"]["items"]:
        if item["id"] == product_id:
            return item["stock"]
    raise AssertionError(f"product {product_id} not found in inventory")


def make_sales_order(session, customer_id, product_id, qty=1, price=100.0):
    response = session.post(
        API + "/sales-orders",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "qty": qty, "price": price}],
        },
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


# ---------------- 基础 ----------------
def test_health():
    response = requests.get(API + "/health", timeout=10)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "up"


def test_login_success():
    response = requests.post(
        API + "/login", json={"username": ADMIN[0], "password": ADMIN[1]}, timeout=10
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["role"] == "admin"
    assert data["tenant"]["code"] == "QM"


def test_login_wrong_password():
    response = requests.post(
        API + "/login", json={"username": "admin", "password": "wrong"}, timeout=10
    )
    assert response.status_code == 401
    assert response.json()["code"] == 401


def test_unauthorized():
    session = requests.Session()
    assert session.get(API + "/customers", timeout=10).status_code == 401
    assert session.post(API + "/customers", json={"name": "x"}, timeout=10).status_code == 401


def test_dashboard(admin):
    response = admin.get(API + "/dashboard", timeout=10)
    assert response.status_code == 200
    data = response.json()["data"]
    assert {"customers", "open_opportunity_amount", "pending_purchase_orders", "low_stock_products"} <= set(data["stats"])
    assert isinstance(data["pipeline"], list)


# ---------------- 客户 ----------------
def test_customer_crud(admin, unique):
    name = f"QA-API-CUST-{unique}"
    response = admin.post(API + "/customers", json={"name": name, "phone": "13800000000"}, timeout=10)
    assert response.status_code == 201
    cid = response.json()["data"]["id"]

    response = admin.get(API + f"/customers/{cid}", timeout=10)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == name

    response = admin.put(API + f"/customers/{cid}", json={"phone": "13911112222"}, timeout=10)
    assert response.status_code == 200
    response = admin.get(API + f"/customers/{cid}", timeout=10)
    assert response.json()["data"]["phone"] == "13911112222"

    response = admin.get(API + "/customers", params={"q": name}, timeout=10)
    assert response.status_code == 200
    assert any(item["id"] == cid for item in response.json()["data"]["items"])

    response = admin.delete(API + f"/customers/{cid}", timeout=10)
    assert response.status_code == 200
    response = admin.get(API + f"/customers/{cid}", timeout=10)
    assert response.json()["data"]["status"] == "inactive"


def test_customer_name_required(admin):
    response = admin.post(API + "/customers", json={"phone": "13800000000"}, timeout=10)
    assert response.status_code == 400
    assert "名称" in response.json()["message"]


def test_customer_update_owner_cross_tenant(admin, unique):
    cid = make_customer(admin, unique)
    # 用户 5 属于租户 B，不应允许设置为租户 A 客户的负责人
    response = admin.put(API + f"/customers/{cid}", json={"owner_id": 5}, timeout=10)
    assert response.status_code == 400
    assert "租户" in response.json()["message"]


# ---------------- 产品 ----------------
def test_product_validation(admin, unique):
    response = admin.post(
        API + "/products",
        json={"sku": f"QA-NEG-{unique}", "name": "负库存产品", "stock": -1},
        timeout=10,
    )
    assert response.status_code == 400

    pid = make_product(admin, unique)
    assert pid > 0
    response = admin.post(
        API + "/products",
        json={"sku": f"QA-API-{unique}", "name": "重复 SKU", "stock": 1},
        timeout=10,
    )
    assert response.status_code == 400


# ---------------- 销售订单 ----------------
def test_sales_order_flow(admin, unique):
    cid = make_customer(admin, unique)
    pid = make_product(admin, unique, stock=10, price=100)
    so_id = make_sales_order(admin, cid, pid, qty=3, price=100)

    response = admin.post(API + f"/sales-orders/{so_id}/confirm", timeout=10)
    assert response.status_code == 200
    response = admin.post(API + f"/sales-orders/{so_id}/ship", timeout=10)
    assert response.status_code == 200

    assert stock_of(admin, pid) == 7
    response = admin.get(API + f"/sales-orders/{so_id}", timeout=10)
    assert response.json()["data"]["order"]["status"] == "shipped"
    assert response.json()["data"]["order"]["total_amount"] == 300

    # 已发货订单不能取消
    response = admin.post(API + f"/sales-orders/{so_id}/cancel", timeout=10)
    assert response.status_code == 400


def test_sales_order_insufficient_stock(admin, unique):
    cid = make_customer(admin, unique)
    pid = make_product(admin, unique, stock=1)
    so_id = make_sales_order(admin, cid, pid, qty=2)

    response = admin.post(API + f"/sales-orders/{so_id}/confirm", timeout=10)
    assert response.status_code == 400
    assert "库存不足" in response.json()["message"]
    assert stock_of(admin, pid) == 1
    response = admin.get(API + f"/sales-orders/{so_id}", timeout=10)
    assert response.json()["data"]["order"]["status"] == "draft"


def test_invoice_flow(admin, unique):
    cid = make_customer(admin, unique)
    pid = make_product(admin, unique, stock=5, price=100)
    so_id = make_sales_order(admin, cid, pid, qty=1, price=100)

    # 未发货不能开票
    assert admin.post(API + f"/sales-orders/{so_id}/invoice", timeout=10).status_code == 400
    assert admin.post(API + f"/sales-orders/{so_id}/confirm", timeout=10).status_code == 200
    assert admin.post(API + f"/sales-orders/{so_id}/ship", timeout=10).status_code == 200

    response = admin.post(API + f"/sales-orders/{so_id}/invoice", timeout=10)
    assert response.status_code == 201, response.text
    invoice_id = response.json()["data"]["id"]

    response = admin.get(API + f"/sales-orders/{so_id}", timeout=10)
    invoice = response.json()["data"]["invoice"]
    assert invoice["id"] == invoice_id
    assert invoice["amount"] == 100

    response = admin.get(API + "/invoices", timeout=10)
    assert any(item["id"] == invoice_id for item in response.json()["data"]["items"])

    # 重复开票被拦截
    response = admin.post(API + f"/sales-orders/{so_id}/invoice", timeout=10)
    assert response.status_code == 400


def test_sales_order_cancel(admin, unique):
    cid = make_customer(admin, unique)
    pid = make_product(admin, unique, stock=5)
    so_id = make_sales_order(admin, cid, pid, qty=1)
    assert admin.post(API + f"/sales-orders/{so_id}/confirm", timeout=10).status_code == 200
    assert admin.post(API + f"/sales-orders/{so_id}/cancel", timeout=10).status_code == 200
    response = admin.get(API + f"/sales-orders/{so_id}", timeout=10)
    assert response.json()["data"]["order"]["status"] == "cancelled"
    assert stock_of(admin, pid) == 5


def test_concurrent_shipping_no_oversell(admin, unique):
    """8 个订单并发发货，库存只有 5，最多只能成功 5 个，且库存不能为负。"""
    cid = make_customer(admin, unique)
    pid = make_product(admin, unique, stock=5)
    so_ids = [make_sales_order(admin, cid, pid, qty=1) for _ in range(8)]
    for so_id in so_ids:
        response = admin.post(API + f"/sales-orders/{so_id}/confirm", timeout=10)
        assert response.status_code == 200, response.text

    def ship(so_id):
        session = login(*ADMIN)
        response = session.post(API + f"/sales-orders/{so_id}/ship", timeout=20)
        return response.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(ship, so_ids))

    assert all(code in (200, 400) for code in results), results
    assert results.count(200) == 5, results
    assert stock_of(admin, pid) == 0

    shipped = 0
    for so_id in so_ids:
        response = admin.get(API + f"/sales-orders/{so_id}", timeout=10)
        if response.json()["data"]["order"]["status"] == "shipped":
            shipped += 1
    assert shipped == 5


# ---------------- 采购订单 ----------------
def test_purchase_order_flow(admin, unique):
    pid = make_product(admin, unique, stock=0, price=50)
    response = admin.post(
        API + "/purchase-orders",
        json={"supplier_id": 1, "items": [{"product_id": pid, "qty": 5, "price": 50}]},
        timeout=10,
    )
    assert response.status_code == 201, response.text
    po_id = response.json()["data"]["id"]

    assert admin.post(API + f"/purchase-orders/{po_id}/confirm", timeout=10).status_code == 200
    assert admin.post(API + f"/purchase-orders/{po_id}/receive", timeout=10).status_code == 200
    assert stock_of(admin, pid) == 5
    response = admin.get(API + f"/purchase-orders/{po_id}", timeout=10)
    assert response.json()["data"]["order"]["status"] == "received"

    # 重复收货、已收货取消都应被拦截
    assert admin.post(API + f"/purchase-orders/{po_id}/receive", timeout=10).status_code == 400
    assert admin.post(API + f"/purchase-orders/{po_id}/cancel", timeout=10).status_code == 400
    assert stock_of(admin, pid) == 5


def test_purchase_order_cancel(admin, unique):
    pid = make_product(admin, unique, stock=0, price=50)
    response = admin.post(
        API + "/purchase-orders",
        json={"supplier_id": 1, "items": [{"product_id": pid, "qty": 1, "price": 50}]},
        timeout=10,
    )
    po_id = response.json()["data"]["id"]
    assert admin.post(API + f"/purchase-orders/{po_id}/confirm", timeout=10).status_code == 200
    assert admin.post(API + f"/purchase-orders/{po_id}/cancel", timeout=10).status_code == 200
    response = admin.get(API + f"/purchase-orders/{po_id}", timeout=10)
    assert response.json()["data"]["order"]["status"] == "cancelled"
    assert admin.post(API + f"/purchase-orders/{po_id}/receive", timeout=10).status_code == 400


# ---------------- 库存 ----------------
def test_inventory_adjust(admin, unique):
    pid = make_product(admin, unique, stock=10)
    response = admin.post(
        API + "/inventory/adjust",
        json={"product_id": pid, "qty_delta": 5, "note": "接口测试入库"},
        timeout=10,
    )
    assert response.status_code == 200
    assert response.json()["data"]["stock"] == 15

    response = admin.post(
        API + "/inventory/adjust",
        json={"product_id": pid, "qty_delta": -3, "note": "接口测试出库"},
        timeout=10,
    )
    assert response.status_code == 200
    assert response.json()["data"]["stock"] == 12

    response = admin.post(
        API + "/inventory/adjust",
        json={"product_id": pid, "qty_delta": -100, "note": "超量出库"},
        timeout=10,
    )
    assert response.status_code == 400
    assert stock_of(admin, pid) == 12


# ---------------- 权限与租户隔离 ----------------
def test_role_permissions():
    sales = login(*SALES)
    assert sales.get(API + "/customers", timeout=10).status_code == 200
    assert sales.post(API + "/customers", json={"name": "QA-销售创建客户"}, timeout=10).status_code == 201
    assert sales.post(API + "/products", json={"sku": "QA-ROLE", "name": "x"}, timeout=10).status_code == 403
    assert sales.post(API + "/purchase-orders", json={"supplier_id": 1, "items": []}, timeout=10).status_code == 403


def test_tenant_isolation(admin, admin_b, unique):
    # 租户 B 只能看到自己的 3 个客户
    response = admin_b.get(API + "/customers", timeout=10)
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["data"]["items"]]
    assert len(names) == 3
    assert all(name.startswith("远航") for name in names)

    # 租户 A 创建客户，租户 B 访问不到
    cid = make_customer(admin, unique)
    assert admin_b.get(API + f"/customers/{cid}", timeout=10).status_code == 404

    # 租户 B 创建客户，租户 A 访问不到
    response = admin_b.post(API + "/customers", json={"name": f"QA-B-{unique}"}, timeout=10)
    assert response.status_code == 201
    bid = response.json()["data"]["id"]
    assert admin.get(API + f"/customers/{bid}", timeout=10).status_code == 404


# ---------------- 线索转化 ----------------
def test_lead_convert(admin, unique):
    response = admin.post(
        API + "/leads",
        json={"name": f"QA-LEAD-{unique}", "contact": "张经理", "phone": "13700009999"},
        timeout=10,
    )
    assert response.status_code == 201, response.text
    lid = response.json()["data"]["id"]

    response = admin.post(API + f"/leads/{lid}/convert", timeout=10)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert admin.get(API + f"/customers/{data['customer_id']}", timeout=10).status_code == 200

    response = admin.get(API + "/opportunities", timeout=10)
    assert any(item["id"] == data["opportunity_id"] for item in response.json()["data"]["items"])

    # 重复转化被拦截
    assert admin.post(API + f"/leads/{lid}/convert", timeout=10).status_code == 400
