# -*- coding: utf-8 -*-
"""REST API：供 Postman / pytest / JMeter 调用。"""
from datetime import datetime

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash

from .auth import api_login_required, tenant_id
from .db import get_db, query
from .services import (
    ServiceError,
    adjust_stock,
    cancel_purchase_order,
    cancel_sales_order,
    confirm_purchase_order,
    confirm_sales_order,
    convert_lead,
    create_invoice,
    create_purchase_order,
    create_sales_order,
    receive_purchase_order,
    ship_sales_order,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def ok(data=None, message="ok", status=200):
    return jsonify({"code": 0, "message": message, "data": data}), status


def fail(message, status=400):
    return jsonify({"code": status, "message": message, "data": None}), status


def body():
    return request.get_json(silent=True) or {}


def rows_to_list(rows):
    return [dict(row) for row in rows]


def _forbid(*roles):
    if g.user["role"] not in roles:
        return fail("当前角色无权执行该操作", 403)
    return None


# ---------------- 基础 ----------------
@api_bp.route("/health", methods=["GET"])
def health():
    return ok({"status": "up", "time": datetime.now().isoformat()})


@api_bp.route("/login", methods=["POST"])
def login():
    data = body()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = query(
        "SELECT * FROM users WHERE username=? AND active=1", (username,), one=True
    )
    if user is None or not check_password_hash(user["password_hash"], password):
        return fail("用户名或密码错误", 401)
    session.clear()
    session["user_id"] = user["id"]
    session["tenant_id"] = user["tenant_id"]
    tenant = query("SELECT * FROM tenants WHERE id=?", (user["tenant_id"],), one=True)
    return ok(
        {
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
            },
            "tenant": {"id": tenant["id"], "name": tenant["name"], "code": tenant["code"]},
        },
        "登录成功",
    )


@api_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return ok(None, "已退出登录")


@api_bp.route("/me", methods=["GET"])
@api_login_required
def me():
    return ok(
        {
            "id": g.user["id"],
            "username": g.user["username"],
            "full_name": g.user["full_name"],
            "role": g.user["role"],
            "tenant": {"id": g.tenant["id"], "name": g.tenant["name"], "code": g.tenant["code"]},
        }
    )


@api_bp.route("/dashboard", methods=["GET"])
@api_login_required
def dashboard():
    tid = tenant_id()
    stats = {
        "customers": query(
            "SELECT COUNT(*) AS c FROM customers WHERE tenant_id=? AND status='active'",
            (tid,),
            one=True,
        )["c"],
        "open_opportunity_amount": query(
            "SELECT COALESCE(SUM(amount),0) AS s FROM opportunities "
            "WHERE tenant_id=? AND stage NOT IN ('won','lost')",
            (tid,),
            one=True,
        )["s"],
        "pending_purchase_orders": query(
            "SELECT COUNT(*) AS c FROM purchase_orders "
            "WHERE tenant_id=? AND status IN ('draft','confirmed')",
            (tid,),
            one=True,
        )["c"],
        "low_stock_products": query(
            "SELECT COUNT(*) AS c FROM products WHERE tenant_id=? AND stock<=safety_stock",
            (tid,),
            one=True,
        )["c"],
    }
    pipeline = rows_to_list(
        query(
            "SELECT stage, COUNT(*) AS count, COALESCE(SUM(amount),0) AS amount "
            "FROM opportunities WHERE tenant_id=? GROUP BY stage",
            (tid,),
        )
    )
    return ok({"stats": stats, "pipeline": pipeline})


# ---------------- 客户 ----------------
@api_bp.route("/customers", methods=["GET"])
@api_login_required
def customers_list():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or ""
    limit = min(int(request.args.get("limit") or 50), 100)
    sql = (
        "SELECT c.*, u.full_name AS owner_name FROM customers c "
        "LEFT JOIN users u ON c.owner_id=u.id WHERE c.tenant_id=?"
    )
    params = [tid]
    if q:
        sql += " AND (c.name LIKE ? OR c.contact LIKE ? OR c.phone LIKE ?)"
        params += [f"%{q}%"] * 3
    if status:
        sql += " AND c.status=?"
        params.append(status)
    sql += " ORDER BY c.id DESC LIMIT ?"
    params.append(limit)
    rows = query(sql, params)
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/customers", methods=["POST"])
@api_login_required
def customers_create():
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    data = body()
    name = (data.get("name") or "").strip()
    if not name:
        return fail("客户名称不能为空")
    owner_id = data.get("owner_id")
    if owner_id and not query(
        "SELECT 1 FROM users WHERE id=? AND tenant_id=?", (owner_id, tenant_id()), one=True
    ):
        owner_id = None
    cur = get_db().execute(
        """INSERT INTO customers
           (tenant_id, name, contact, phone, email, level, status, owner_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tenant_id(),
            name,
            data.get("contact", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("level", "普通"),
            data.get("status", "active"),
            owner_id,
        ),
    )
    get_db().commit()
    return ok({"id": cur.lastrowid}, "客户创建成功", 201)


@api_bp.route("/customers/<int:cid>", methods=["GET"])
@api_login_required
def customers_get(cid):
    row = query(
        "SELECT c.*, u.full_name AS owner_name FROM customers c "
        "LEFT JOIN users u ON c.owner_id=u.id WHERE c.id=? AND c.tenant_id=?",
        (cid, tenant_id()),
        one=True,
    )
    if row is None:
        return fail("客户不存在", 404)
    return ok(dict(row))


@api_bp.route("/customers/<int:cid>", methods=["PUT", "PATCH"])
@api_login_required
def customers_update(cid):
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    row = query(
        "SELECT * FROM customers WHERE id=? AND tenant_id=?",
        (cid, tenant_id()),
        one=True,
    )
    if row is None:
        return fail("客户不存在", 404)
    data = body()
    name = (data.get("name") or row["name"]).strip()
    if not name:
        return fail("客户名称不能为空")
    owner_id = data.get("owner_id", row["owner_id"])
    if owner_id not in (None, "") and not query(
        "SELECT 1 FROM users WHERE id=? AND tenant_id=?", (owner_id, tenant_id()), one=True
    ):
        return fail("负责人不属于当前租户")
    get_db().execute(
        """UPDATE customers SET name=?, contact=?, phone=?, email=?, level=?, status=?, owner_id=?
           WHERE id=? AND tenant_id=?""",
        (
            name,
            data.get("contact", row["contact"]),
            data.get("phone", row["phone"]),
            data.get("email", row["email"]),
            data.get("level", row["level"]),
            data.get("status", row["status"]),
            owner_id,
            cid,
            tenant_id(),
        ),
    )
    get_db().commit()
    return ok({"id": cid}, "客户更新成功")


@api_bp.route("/customers/<int:cid>", methods=["DELETE"])
@api_login_required
def customers_delete(cid):
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    row = query(
        "SELECT * FROM customers WHERE id=? AND tenant_id=?",
        (cid, tenant_id()),
        one=True,
    )
    if row is None:
        return fail("客户不存在", 404)
    get_db().execute(
        "UPDATE customers SET status='inactive' WHERE id=? AND tenant_id=?",
        (cid, tenant_id()),
    )
    get_db().commit()
    return ok({"id": cid}, "客户已归档")


# ---------------- 线索 / 商机 ----------------
@api_bp.route("/leads", methods=["GET"])
@api_login_required
def leads_list():
    rows = query(
        "SELECT * FROM leads WHERE tenant_id=? ORDER BY id DESC LIMIT 100",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/leads", methods=["POST"])
@api_login_required
def leads_create():
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    data = body()
    name = (data.get("name") or "").strip()
    if not name:
        return fail("线索名称不能为空")
    cur = get_db().execute(
        """INSERT INTO leads
           (tenant_id, name, contact, phone, email, source, status, owner_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            tenant_id(),
            name,
            data.get("contact", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("source", ""),
            data.get("status", "new"),
            data.get("owner_id"),
        ),
    )
    get_db().commit()
    return ok({"id": cur.lastrowid}, "线索创建成功", 201)


@api_bp.route("/leads/<int:lid>/convert", methods=["POST"])
@api_login_required
def leads_convert(lid):
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    try:
        customer_id, opportunity_id = convert_lead(tenant_id(), lid, g.user["id"])
    except ServiceError as exc:
        return fail(str(exc))
    return ok(
        {"customer_id": customer_id, "opportunity_id": opportunity_id}, "线索转化成功"
    )


@api_bp.route("/opportunities", methods=["GET"])
@api_login_required
def opportunities_list():
    rows = query(
        "SELECT o.*, c.name AS customer_name FROM opportunities o "
        "JOIN customers c ON o.customer_id=c.id WHERE o.tenant_id=? ORDER BY o.id DESC",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


# ---------------- 产品 / 供应商 ----------------
@api_bp.route("/products", methods=["GET"])
@api_login_required
def products_list():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    low_stock = request.args.get("low_stock") in ("1", "true", "yes")
    sql = "SELECT * FROM products WHERE tenant_id=?"
    params = [tid]
    if q:
        sql += " AND (name LIKE ? OR sku LIKE ?)"
        params += [f"%{q}%"] * 2
    if low_stock:
        sql += " AND stock<=safety_stock"
    sql += " ORDER BY id DESC LIMIT 100"
    rows = query(sql, params)
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/products", methods=["POST"])
@api_login_required
def products_create():
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    data = body()
    sku = (data.get("sku") or "").strip()
    name = (data.get("name") or "").strip()
    if not sku or not name:
        return fail("SKU 和产品名称不能为空")
    try:
        price = float(data.get("price", 0))
        cost = float(data.get("cost", 0))
        stock = int(data.get("stock", 0))
        safety_stock = int(data.get("safety_stock", 10))
    except (TypeError, ValueError):
        return fail("价格、成本、库存必须是数字")
    if min(price, cost, stock, safety_stock) < 0:
        return fail("价格、成本、库存不能为负数")
    try:
        cur = get_db().execute(
            """INSERT INTO products
               (tenant_id, sku, name, category, price, cost, stock, safety_stock)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tenant_id(),
                sku,
                name,
                data.get("category", ""),
                price,
                cost,
                stock,
                safety_stock,
            ),
        )
        get_db().commit()
    except Exception as exc:
        get_db().rollback()
        return fail(f"产品创建失败：{exc}")
    return ok({"id": cur.lastrowid}, "产品创建成功", 201)


@api_bp.route("/suppliers", methods=["GET"])
@api_login_required
def suppliers_list():
    rows = query(
        "SELECT * FROM suppliers WHERE tenant_id=? ORDER BY id DESC", (tenant_id(),)
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/suppliers", methods=["POST"])
@api_login_required
def suppliers_create():
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    data = body()
    name = (data.get("name") or "").strip()
    if not name:
        return fail("供应商名称不能为空")
    cur = get_db().execute(
        "INSERT INTO suppliers (tenant_id, name, contact, phone, email) VALUES (?, ?, ?, ?, ?)",
        (
            tenant_id(),
            name,
            data.get("contact", ""),
            data.get("phone", ""),
            data.get("email", ""),
        ),
    )
    get_db().commit()
    return ok({"id": cur.lastrowid}, "供应商创建成功", 201)


# ---------------- 采购订单 ----------------
@api_bp.route("/purchase-orders", methods=["GET"])
@api_login_required
def purchase_orders_list():
    rows = query(
        "SELECT po.*, s.name AS supplier_name FROM purchase_orders po "
        "JOIN suppliers s ON po.supplier_id=s.id WHERE po.tenant_id=? ORDER BY po.id DESC",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/purchase-orders", methods=["POST"])
@api_login_required
def purchase_orders_create():
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    data = body()
    try:
        po_id = create_purchase_order(
            tenant_id(), data.get("supplier_id"), data.get("items", []), g.user["id"]
        )
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": po_id}, "采购订单创建成功", 201)


@api_bp.route("/purchase-orders/<int:po_id>", methods=["GET"])
@api_login_required
def purchase_orders_get(po_id):
    po = query(
        "SELECT * FROM purchase_orders WHERE id=? AND tenant_id=?",
        (po_id, tenant_id()),
        one=True,
    )
    if po is None:
        return fail("采购订单不存在", 404)
    items = query("SELECT * FROM purchase_items WHERE po_id=?", (po_id,))
    return ok({"order": dict(po), "items": rows_to_list(items)})


@api_bp.route("/purchase-orders/<int:po_id>/confirm", methods=["POST"])
@api_login_required
def purchase_orders_confirm(po_id):
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    try:
        confirm_purchase_order(tenant_id(), po_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": po_id}, "采购订单已确认")


@api_bp.route("/purchase-orders/<int:po_id>/receive", methods=["POST"])
@api_login_required
def purchase_orders_receive(po_id):
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    try:
        receive_purchase_order(tenant_id(), po_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": po_id}, "采购订单已收货")


@api_bp.route("/purchase-orders/<int:po_id>/cancel", methods=["POST"])
@api_login_required
def purchase_orders_cancel(po_id):
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    try:
        cancel_purchase_order(tenant_id(), po_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": po_id}, "采购订单已取消")


# ---------------- 销售订单 ----------------
@api_bp.route("/sales-orders", methods=["GET"])
@api_login_required
def sales_orders_list():
    rows = query(
        "SELECT so.*, c.name AS customer_name FROM sales_orders so "
        "JOIN customers c ON so.customer_id=c.id WHERE so.tenant_id=? ORDER BY so.id DESC",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/sales-orders", methods=["POST"])
@api_login_required
def sales_orders_create():
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    data = body()
    try:
        so_id = create_sales_order(
            tenant_id(), data.get("customer_id"), data.get("items", []), g.user["id"]
        )
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": so_id}, "销售订单创建成功", 201)


@api_bp.route("/sales-orders/<int:so_id>", methods=["GET"])
@api_login_required
def sales_orders_get(so_id):
    so = query(
        "SELECT * FROM sales_orders WHERE id=? AND tenant_id=?",
        (so_id, tenant_id()),
        one=True,
    )
    if so is None:
        return fail("销售订单不存在", 404)
    items = query("SELECT * FROM sales_items WHERE so_id=?", (so_id,))
    invoice = query(
        "SELECT * FROM invoices WHERE tenant_id=? AND sales_order_id=?",
        (tenant_id(), so_id),
        one=True,
    )
    return ok(
        {
            "order": dict(so),
            "items": rows_to_list(items),
            "invoice": dict(invoice) if invoice else None,
        }
    )


@api_bp.route("/sales-orders/<int:so_id>/confirm", methods=["POST"])
@api_login_required
def sales_orders_confirm(so_id):
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    try:
        confirm_sales_order(tenant_id(), so_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": so_id}, "销售订单已确认")


@api_bp.route("/sales-orders/<int:so_id>/ship", methods=["POST"])
@api_login_required
def sales_orders_ship(so_id):
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    try:
        ship_sales_order(tenant_id(), so_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": so_id}, "销售订单已发货")


@api_bp.route("/sales-orders/<int:so_id>/cancel", methods=["POST"])
@api_login_required
def sales_orders_cancel(so_id):
    denied = _forbid("admin", "sales")
    if denied:
        return denied
    try:
        cancel_sales_order(tenant_id(), so_id)
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": so_id}, "销售订单已取消")


@api_bp.route("/sales-orders/<int:so_id>/invoice", methods=["POST"])
@api_login_required
def sales_orders_invoice(so_id):
    denied = _forbid("admin", "sales", "finance")
    if denied:
        return denied
    try:
        invoice_id = create_invoice(tenant_id(), so_id, g.user["id"])
    except ServiceError as exc:
        return fail(str(exc))
    return ok({"id": invoice_id}, "发票开具成功", 201)


@api_bp.route("/invoices", methods=["GET"])
@api_login_required
def invoices_list():
    rows = query(
        "SELECT i.*, so.so_no, c.name AS customer_name FROM invoices i "
        "JOIN sales_orders so ON i.sales_order_id=so.id "
        "JOIN customers c ON i.customer_id=c.id "
        "WHERE i.tenant_id=? ORDER BY i.id DESC",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


# ---------------- 库存 ----------------
@api_bp.route("/inventory", methods=["GET"])
@api_login_required
def inventory_list():
    rows = query(
        "SELECT id, sku, name, stock, safety_stock, price, cost "
        "FROM products WHERE tenant_id=? ORDER BY stock ASC",
        (tenant_id(),),
    )
    return ok({"items": rows_to_list(rows), "total": len(rows)})


@api_bp.route("/inventory/adjust", methods=["POST"])
@api_login_required
def inventory_adjust():
    denied = _forbid("admin", "warehouse")
    if denied:
        return denied
    data = body()
    try:
        new_stock = adjust_stock(
            tenant_id(),
            int(data.get("product_id") or 0),
            int(data.get("qty_delta") or 0),
            data.get("note", "API 库存调整"),
            g.user["id"],
        )
    except (ServiceError, ValueError) as exc:
        return fail(str(exc))
    return ok({"stock": new_stock}, "库存调整成功")
