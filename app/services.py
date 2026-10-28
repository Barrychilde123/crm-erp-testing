# -*- coding: utf-8 -*-
"""业务服务层：Web 页面与 API 共用，保证业务流程一致。"""
import random
from datetime import datetime

from werkzeug.security import generate_password_hash

from .db import get_db


class ServiceError(Exception):
    """可直接返回给用户的业务异常。"""


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def next_no(prefix):
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10, 99)}"


def _get_product(db, tenant_id, product_id):
    product = db.execute(
        "SELECT * FROM products WHERE id=? AND tenant_id=?", (product_id, tenant_id)
    ).fetchone()
    if product is None:
        raise ServiceError("产品不存在或不属于当前租户")
    return product


def _validate_items(db, tenant_id, items):
    if not items:
        raise ServiceError("请至少添加一条明细")
    cleaned = []
    for item in items:
        try:
            product_id = int(item.get("product_id"))
            qty = int(item.get("qty"))
            price = float(item.get("price", 0))
        except (TypeError, ValueError):
            raise ServiceError("明细参数格式错误")
        if qty <= 0:
            raise ServiceError("数量必须大于 0")
        if price < 0:
            raise ServiceError("单价不能为负数")
        _get_product(db, tenant_id, product_id)
        cleaned.append({"product_id": product_id, "qty": qty, "price": price})
    return cleaned


def _get_po(db, tenant_id, po_id):
    po = db.execute(
        "SELECT * FROM purchase_orders WHERE id=? AND tenant_id=?", (po_id, tenant_id)
    ).fetchone()
    if po is None:
        raise ServiceError("采购订单不存在")
    return po


def _get_so(db, tenant_id, so_id):
    so = db.execute(
        "SELECT * FROM sales_orders WHERE id=? AND tenant_id=?", (so_id, tenant_id)
    ).fetchone()
    if so is None:
        raise ServiceError("销售订单不存在")
    return so


def create_purchase_order(tenant_id, supplier_id, items, user_id):
    db = get_db()
    supplier = db.execute(
        "SELECT * FROM suppliers WHERE id=? AND tenant_id=?", (supplier_id, tenant_id)
    ).fetchone()
    if supplier is None:
        raise ServiceError("供应商不存在")
    items = _validate_items(db, tenant_id, items)
    total = round(sum(i["qty"] * i["price"] for i in items), 2)
    try:
        cur = db.execute(
            """INSERT INTO purchase_orders
               (tenant_id, po_no, supplier_id, status, total_amount, created_by)
               VALUES (?, ?, ?, 'draft', ?, ?)""",
            (tenant_id, next_no("PO"), supplier_id, total, user_id),
        )
        po_id = cur.lastrowid
        for item in items:
            db.execute(
                "INSERT INTO purchase_items (po_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (po_id, item["product_id"], item["qty"], item["price"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return po_id


def confirm_purchase_order(tenant_id, po_id):
    db = get_db()
    _get_po(db, tenant_id, po_id)
    cur = db.execute(
        "UPDATE purchase_orders SET status='confirmed' "
        "WHERE id=? AND tenant_id=? AND status='draft'",
        (po_id, tenant_id),
    )
    if cur.rowcount == 0:
        db.rollback()
        raise ServiceError("只有草稿状态的采购订单才能确认")
    db.commit()


def receive_purchase_order(tenant_id, po_id):
    db = get_db()
    po = _get_po(db, tenant_id, po_id)
    if po["status"] != "confirmed":
        raise ServiceError("只有已确认的采购订单才能收货")
    items = db.execute("SELECT * FROM purchase_items WHERE po_id=?", (po_id,)).fetchall()
    try:
        # 先做状态迁移，避免并发重复收货导致库存翻倍
        cur = db.execute(
            "UPDATE purchase_orders SET status='received', received_at=? "
            "WHERE id=? AND tenant_id=? AND status='confirmed'",
            (now_str(), po_id, tenant_id),
        )
        if cur.rowcount == 0:
            raise ServiceError("采购订单状态已变化，请刷新后重试")
        for item in items:
            db.execute(
                "UPDATE products SET stock=stock+? WHERE id=? AND tenant_id=?",
                (item["qty"], item["product_id"], tenant_id),
            )
            db.execute(
                """INSERT INTO inventory_moves
                   (tenant_id, product_id, move_type, qty, ref_no, note)
                   VALUES (?, ?, 'in', ?, ?, '采购收货')""",
                (tenant_id, item["product_id"], item["qty"], po["po_no"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise


def cancel_purchase_order(tenant_id, po_id):
    db = get_db()
    po = _get_po(db, tenant_id, po_id)
    if po["status"] == "received":
        raise ServiceError("已收货的采购订单不能取消")
    if po["status"] == "cancelled":
        raise ServiceError("订单已取消")
    cur = db.execute(
        "UPDATE purchase_orders SET status='cancelled' "
        "WHERE id=? AND tenant_id=? AND status IN ('draft','confirmed')",
        (po_id, tenant_id),
    )
    if cur.rowcount == 0:
        db.rollback()
        raise ServiceError("采购订单状态已变化，请刷新后重试")
    db.commit()


def create_sales_order(tenant_id, customer_id, items, user_id):
    db = get_db()
    customer = db.execute(
        "SELECT * FROM customers WHERE id=? AND tenant_id=? AND status='active'",
        (customer_id, tenant_id),
    ).fetchone()
    if customer is None:
        raise ServiceError("客户不存在或已归档")
    items = _validate_items(db, tenant_id, items)
    total = round(sum(i["qty"] * i["price"] for i in items), 2)
    try:
        cur = db.execute(
            """INSERT INTO sales_orders
               (tenant_id, so_no, customer_id, status, total_amount, created_by)
               VALUES (?, ?, ?, 'draft', ?, ?)""",
            (tenant_id, next_no("SO"), customer_id, total, user_id),
        )
        so_id = cur.lastrowid
        for item in items:
            db.execute(
                "INSERT INTO sales_items (so_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                (so_id, item["product_id"], item["qty"], item["price"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return so_id


def _check_stock(db, tenant_id, so_id):
    items = db.execute("SELECT * FROM sales_items WHERE so_id=?", (so_id,)).fetchall()
    required = {}
    for item in items:
        required[item["product_id"]] = required.get(item["product_id"], 0) + item["qty"]
    for product_id, qty in required.items():
        product = _get_product(db, tenant_id, product_id)
        if product["stock"] < qty:
            raise ServiceError(
                f"库存不足：{product['name']} 当前库存 {product['stock']}，需要 {qty}"
            )
    return items, required


def confirm_sales_order(tenant_id, so_id):
    db = get_db()
    _get_so(db, tenant_id, so_id)
    _check_stock(db, tenant_id, so_id)
    cur = db.execute(
        "UPDATE sales_orders SET status='confirmed' "
        "WHERE id=? AND tenant_id=? AND status='draft'",
        (so_id, tenant_id),
    )
    if cur.rowcount == 0:
        db.rollback()
        raise ServiceError("只有草稿状态的销售订单才能确认")
    db.commit()


def ship_sales_order(tenant_id, so_id):
    db = get_db()
    so = _get_so(db, tenant_id, so_id)
    if so["status"] != "confirmed":
        raise ServiceError("只有已确认的销售订单才能发货")
    items, required = _check_stock(db, tenant_id, so_id)
    try:
        # 先做状态迁移，避免并发重复发货
        cur = db.execute(
            "UPDATE sales_orders SET status='shipped', shipped_at=? "
            "WHERE id=? AND tenant_id=? AND status='confirmed'",
            (now_str(), so_id, tenant_id),
        )
        if cur.rowcount == 0:
            raise ServiceError("销售订单状态已变化，请刷新后重试")
        for product_id, qty in required.items():
            # 原子扣减：stock>=qty 才更新，防止并发超卖
            cur = db.execute(
                "UPDATE products SET stock=stock-? "
                "WHERE id=? AND tenant_id=? AND stock>=?",
                (qty, product_id, tenant_id, qty),
            )
            if cur.rowcount == 0:
                raise ServiceError(f"库存不足：产品 {product_id} 当前库存不足以发货")
            db.execute(
                """INSERT INTO inventory_moves
                   (tenant_id, product_id, move_type, qty, ref_no, note)
                   VALUES (?, ?, 'out', ?, ?, '销售发货')""",
                (tenant_id, product_id, qty, so["so_no"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise


def cancel_sales_order(tenant_id, so_id):
    db = get_db()
    so = _get_so(db, tenant_id, so_id)
    if so["status"] == "shipped":
        raise ServiceError("已发货的销售订单不能取消")
    if so["status"] == "cancelled":
        raise ServiceError("订单已取消")
    cur = db.execute(
        "UPDATE sales_orders SET status='cancelled' "
        "WHERE id=? AND tenant_id=? AND status IN ('draft','confirmed')",
        (so_id, tenant_id),
    )
    if cur.rowcount == 0:
        db.rollback()
        raise ServiceError("销售订单状态已变化，请刷新后重试")
    db.commit()


def adjust_stock(tenant_id, product_id, qty_delta, note, user_id=None):
    db = get_db()
    product = _get_product(db, tenant_id, product_id)
    try:
        cur = db.execute(
            "UPDATE products SET stock=stock+? "
            "WHERE id=? AND tenant_id=? AND stock+?>=0",
            (qty_delta, product_id, tenant_id, qty_delta),
        )
        if cur.rowcount == 0:
            raise ServiceError("调整后库存不能为负数")
        db.execute(
            """INSERT INTO inventory_moves
               (tenant_id, product_id, move_type, qty, ref_no, note)
               VALUES (?, ?, 'adjust', ?, ?, ?)""",
            (tenant_id, product_id, qty_delta, next_no("ADJ"), note or "库存调整"),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return product["stock"] + qty_delta


def convert_lead(tenant_id, lead_id, user_id):
    db = get_db()
    lead = db.execute(
        "SELECT * FROM leads WHERE id=? AND tenant_id=?", (lead_id, tenant_id)
    ).fetchone()
    if lead is None:
        raise ServiceError("线索不存在")
    if lead["status"] == "converted":
        raise ServiceError("线索已转化，不能重复转化")
    try:
        cur = db.execute(
            """INSERT INTO customers
               (tenant_id, name, contact, phone, email, level, status, owner_id)
               VALUES (?, ?, ?, ?, ?, '普通', 'active', ?)""",
            (tenant_id, lead["name"], lead["contact"], lead["phone"], lead["email"], lead["owner_id"] or user_id),
        )
        customer_id = cur.lastrowid
        cur = db.execute(
            """INSERT INTO opportunities
               (tenant_id, name, customer_id, amount, stage, owner_id)
               VALUES (?, ?, ?, 0, 'new', ?)""",
            (tenant_id, f"{lead['name']} - 商机", customer_id, lead["owner_id"] or user_id),
        )
        opportunity_id = cur.lastrowid
        cur = db.execute(
            "UPDATE leads SET status='converted', customer_id=? "
            "WHERE id=? AND tenant_id=? AND status!='converted'",
            (customer_id, lead_id, tenant_id),
        )
        if cur.rowcount == 0:
            raise ServiceError("线索已转化，不能重复转化")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return customer_id, opportunity_id


def create_tenant(name, code, admin_username, admin_password, full_name):
    db = get_db()
    try:
        cur = db.execute("INSERT INTO tenants (name, code) VALUES (?, ?)", (name, code))
        tenant_id = cur.lastrowid
        db.execute(
            """INSERT INTO users (tenant_id, username, password_hash, full_name, role)
               VALUES (?, ?, ?, ?, 'admin')""",
            (tenant_id, admin_username, generate_password_hash(admin_password), full_name),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return tenant_id


def create_invoice(tenant_id, so_id, user_id=None):
    db = get_db()
    so = _get_so(db, tenant_id, so_id)
    if so["status"] != "shipped":
        raise ServiceError("只有已发货的销售订单才能开具发票")
    existing = db.execute(
        "SELECT * FROM invoices WHERE tenant_id=? AND sales_order_id=?",
        (tenant_id, so_id),
    ).fetchone()
    if existing is not None:
        raise ServiceError("该销售订单已开具发票")
    try:
        cur = db.execute(
            """INSERT INTO invoices
               (tenant_id, invoice_no, sales_order_id, customer_id, amount, status, created_by)
               VALUES (?, ?, ?, ?, ?, 'issued', ?)""",
            (
                tenant_id,
                next_no("INV"),
                so_id,
                so["customer_id"],
                so["total_amount"],
                user_id,
            ),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return cur.lastrowid
