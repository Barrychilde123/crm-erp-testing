# -*- coding: utf-8 -*-
"""ERP：产品、供应商、采购、销售、库存。"""
import sqlite3

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import login_required, tenant_id
from .db import get_db, query
from .services import (
    ServiceError,
    adjust_stock,
    cancel_purchase_order,
    cancel_sales_order,
    confirm_purchase_order,
    confirm_sales_order,
    create_invoice,
    create_purchase_order,
    create_sales_order,
    receive_purchase_order,
    ship_sales_order,
)

erp_bp = Blueprint("erp", __name__, url_prefix="/erp")


def _int_or_none(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_items(form):
    product_ids = form.getlist("product_id")
    qtys = form.getlist("qty")
    prices = form.getlist("price")
    items = []
    for product_id, qty, price in zip(product_ids, qtys, prices):
        if not product_id:
            continue
        items.append({"product_id": product_id, "qty": qty, "price": price})
    return items


# ---------------- 产品 ----------------
@erp_bp.route("/products")
@login_required
def products():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    category = request.args.get("category") or ""
    sql = "SELECT * FROM products WHERE tenant_id=?"
    params = [tid]
    if q:
        sql += " AND (name LIKE ? OR sku LIKE ?)"
        params += [f"%{q}%"] * 2
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY id DESC LIMIT 100"
    rows = query(sql, params)
    categories = [
        r["category"]
        for r in query(
            "SELECT DISTINCT category FROM products WHERE tenant_id=? AND category IS NOT NULL",
            (tid,),
        )
        if r["category"]
    ]
    return render_template(
        "erp/products.html", products=rows, q=q, category=category, categories=categories
    )


@erp_bp.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    tid = tenant_id()
    if request.method == "POST":
        sku = (request.form.get("sku") or "").strip()
        name = (request.form.get("name") or "").strip()
        if not sku or not name:
            flash("SKU 和产品名称不能为空", "error")
        else:
            try:
                get_db().execute(
                    """INSERT INTO products
                       (tenant_id, sku, name, category, price, cost, stock, safety_stock)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tid,
                        sku,
                        name,
                        request.form.get("category", "").strip(),
                        _float(request.form.get("price")),
                        _float(request.form.get("cost")),
                        int(request.form.get("stock") or 0),
                        int(request.form.get("safety_stock") or 10),
                    ),
                )
                get_db().commit()
                flash("产品创建成功", "success")
                return redirect(url_for("erp.products"))
            except sqlite3.IntegrityError:
                flash("SKU 已存在，请更换", "error")
            except ValueError:
                flash("库存和安全库存必须是整数", "error")
    return render_template("erp/product_form.html", product=None)


@erp_bp.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def product_edit(pid):
    tid = tenant_id()
    product = query(
        "SELECT * FROM products WHERE id=? AND tenant_id=?", (pid, tid), one=True
    )
    if product is None:
        abort(404)
    if request.method == "POST":
        sku = (request.form.get("sku") or "").strip()
        name = (request.form.get("name") or "").strip()
        if not sku or not name:
            flash("SKU 和产品名称不能为空", "error")
        else:
            try:
                get_db().execute(
                    """UPDATE products SET sku=?, name=?, category=?, price=?, cost=?,
                       safety_stock=? WHERE id=? AND tenant_id=?""",
                    (
                        sku,
                        name,
                        request.form.get("category", "").strip(),
                        _float(request.form.get("price")),
                        _float(request.form.get("cost")),
                        int(request.form.get("safety_stock") or 10),
                        pid,
                        tid,
                    ),
                )
                get_db().commit()
                flash("产品已更新", "success")
                return redirect(url_for("erp.products"))
            except sqlite3.IntegrityError:
                flash("SKU 已存在，请更换", "error")
            except ValueError:
                flash("安全库存必须是整数", "error")
    return render_template("erp/product_form.html", product=product)


@erp_bp.route("/products/<int:pid>/adjust", methods=["POST"])
@login_required
def product_adjust(pid):
    tid = tenant_id()
    try:
        delta = int(request.form.get("qty_delta") or 0)
        if delta == 0:
            raise ServiceError("调整数量不能为 0")
        adjust_stock(tid, pid, delta, request.form.get("note", "").strip(), g.user["id"])
        flash("库存调整成功", "success")
    except (ServiceError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("erp.inventory"))


# ---------------- 供应商 ----------------
@erp_bp.route("/suppliers")
@login_required
def suppliers():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    sql = "SELECT * FROM suppliers WHERE tenant_id=?"
    params = [tid]
    if q:
        sql += " AND (name LIKE ? OR contact LIKE ? OR phone LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY id DESC LIMIT 100"
    return render_template("erp/suppliers.html", suppliers=query(sql, params), q=q)


@erp_bp.route("/suppliers/new", methods=["GET", "POST"])
@login_required
def supplier_new():
    tid = tenant_id()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("供应商名称不能为空", "error")
        else:
            get_db().execute(
                """INSERT INTO suppliers (tenant_id, name, contact, phone, email)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    tid,
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                ),
            )
            get_db().commit()
            flash("供应商创建成功", "success")
            return redirect(url_for("erp.suppliers"))
    return render_template("erp/supplier_form.html", supplier=None)


@erp_bp.route("/suppliers/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def supplier_edit(sid):
    tid = tenant_id()
    supplier = query(
        "SELECT * FROM suppliers WHERE id=? AND tenant_id=?", (sid, tid), one=True
    )
    if supplier is None:
        abort(404)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("供应商名称不能为空", "error")
        else:
            get_db().execute(
                """UPDATE suppliers SET name=?, contact=?, phone=?, email=?
                   WHERE id=? AND tenant_id=?""",
                (
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                    sid,
                    tid,
                ),
            )
            get_db().commit()
            flash("供应商已更新", "success")
            return redirect(url_for("erp.suppliers"))
    return render_template("erp/supplier_form.html", supplier=supplier)


# ---------------- 采购订单 ----------------
@erp_bp.route("/purchase-orders")
@login_required
def purchase_orders():
    tid = tenant_id()
    status = request.args.get("status") or ""
    sql = (
        "SELECT po.*, s.name AS supplier_name FROM purchase_orders po "
        "JOIN suppliers s ON po.supplier_id=s.id WHERE po.tenant_id=?"
    )
    params = [tid]
    if status:
        sql += " AND po.status=?"
        params.append(status)
    sql += " ORDER BY po.id DESC LIMIT 100"
    return render_template(
        "erp/purchase_orders.html", orders=query(sql, params), status=status
    )


@erp_bp.route("/purchase-orders/new", methods=["GET", "POST"])
@login_required
def purchase_order_new():
    tid = tenant_id()
    suppliers = query(
        "SELECT * FROM suppliers WHERE tenant_id=? ORDER BY name", (tid,)
    )
    products = query(
        "SELECT * FROM products WHERE tenant_id=? ORDER BY name", (tid,)
    )
    if request.method == "POST":
        supplier_id = _int_or_none(request.form.get("supplier_id"))
        items = _parse_items(request.form)
        try:
            if not supplier_id:
                raise ServiceError("请选择供应商")
            po_id = create_purchase_order(tid, supplier_id, items, g.user["id"])
            flash("采购订单创建成功", "success")
            return redirect(url_for("erp.purchase_order_detail", po_id=po_id))
        except ServiceError as exc:
            flash(str(exc), "error")
    return render_template(
        "erp/purchase_order_form.html", suppliers=suppliers, products=products
    )


@erp_bp.route("/purchase-orders/<int:po_id>")
@login_required
def purchase_order_detail(po_id):
    tid = tenant_id()
    po = query(
        "SELECT po.*, s.name AS supplier_name, s.contact AS supplier_contact, "
        "s.phone AS supplier_phone, u.full_name AS creator_name "
        "FROM purchase_orders po JOIN suppliers s ON po.supplier_id=s.id "
        "LEFT JOIN users u ON po.created_by=u.id "
        "WHERE po.id=? AND po.tenant_id=?",
        (po_id, tid),
        one=True,
    )
    if po is None:
        abort(404)
    items = query(
        "SELECT pi.*, p.name AS product_name, p.sku FROM purchase_items pi "
        "JOIN products p ON pi.product_id=p.id WHERE pi.po_id=?",
        (po_id,),
    )
    return render_template("erp/purchase_order_detail.html", po=po, items=items)


@erp_bp.route("/purchase-orders/<int:po_id>/confirm", methods=["POST"])
@login_required
def purchase_order_confirm(po_id):
    try:
        confirm_purchase_order(tenant_id(), po_id)
        flash("采购订单已确认", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.purchase_order_detail", po_id=po_id))


@erp_bp.route("/purchase-orders/<int:po_id>/receive", methods=["POST"])
@login_required
def purchase_order_receive(po_id):
    try:
        receive_purchase_order(tenant_id(), po_id)
        flash("采购订单已收货，库存已增加", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.purchase_order_detail", po_id=po_id))


@erp_bp.route("/purchase-orders/<int:po_id>/cancel", methods=["POST"])
@login_required
def purchase_order_cancel(po_id):
    try:
        cancel_purchase_order(tenant_id(), po_id)
        flash("采购订单已取消", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.purchase_order_detail", po_id=po_id))


# ---------------- 销售订单 ----------------
@erp_bp.route("/sales-orders")
@login_required
def sales_orders():
    tid = tenant_id()
    status = request.args.get("status") or ""
    sql = (
        "SELECT so.*, c.name AS customer_name FROM sales_orders so "
        "JOIN customers c ON so.customer_id=c.id WHERE so.tenant_id=?"
    )
    params = [tid]
    if status:
        sql += " AND so.status=?"
        params.append(status)
    sql += " ORDER BY so.id DESC LIMIT 100"
    return render_template(
        "erp/sales_orders.html", orders=query(sql, params), status=status
    )


@erp_bp.route("/sales-orders/new", methods=["GET", "POST"])
@login_required
def sales_order_new():
    tid = tenant_id()
    customers = query(
        "SELECT * FROM customers WHERE tenant_id=? AND status='active' ORDER BY name",
        (tid,),
    )
    products = query(
        "SELECT * FROM products WHERE tenant_id=? ORDER BY name", (tid,)
    )
    if request.method == "POST":
        customer_id = _int_or_none(request.form.get("customer_id"))
        items = _parse_items(request.form)
        try:
            if not customer_id:
                raise ServiceError("请选择客户")
            so_id = create_sales_order(tid, customer_id, items, g.user["id"])
            flash("销售订单创建成功", "success")
            return redirect(url_for("erp.sales_order_detail", so_id=so_id))
        except ServiceError as exc:
            flash(str(exc), "error")
    return render_template(
        "erp/sales_order_form.html", customers=customers, products=products
    )


@erp_bp.route("/sales-orders/<int:so_id>")
@login_required
def sales_order_detail(so_id):
    tid = tenant_id()
    so = query(
        "SELECT so.*, c.name AS customer_name, c.contact AS customer_contact, "
        "c.phone AS customer_phone, u.full_name AS creator_name "
        "FROM sales_orders so JOIN customers c ON so.customer_id=c.id "
        "LEFT JOIN users u ON so.created_by=u.id "
        "WHERE so.id=? AND so.tenant_id=?",
        (so_id, tid),
        one=True,
    )
    if so is None:
        abort(404)
    items = query(
        "SELECT si.*, p.name AS product_name, p.sku FROM sales_items si "
        "JOIN products p ON si.product_id=p.id WHERE si.so_id=?",
        (so_id,),
    )
    invoice = query(
        "SELECT * FROM invoices WHERE tenant_id=? AND sales_order_id=?",
        (tid, so_id),
        one=True,
    )
    return render_template(
        "erp/sales_order_detail.html", so=so, items=items, invoice=invoice
    )


@erp_bp.route("/sales-orders/<int:so_id>/invoice", methods=["POST"])
@login_required
def sales_order_invoice(so_id):
    try:
        create_invoice(tenant_id(), so_id, g.user["id"])
        flash("发票开具成功", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.sales_order_detail", so_id=so_id))


@erp_bp.route("/sales-orders/<int:so_id>/confirm", methods=["POST"])
@login_required
def sales_order_confirm(so_id):
    try:
        confirm_sales_order(tenant_id(), so_id)
        flash("销售订单已确认", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.sales_order_detail", so_id=so_id))


@erp_bp.route("/sales-orders/<int:so_id>/ship", methods=["POST"])
@login_required
def sales_order_ship(so_id):
    try:
        ship_sales_order(tenant_id(), so_id)
        flash("销售订单已发货，库存已扣减", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.sales_order_detail", so_id=so_id))


@erp_bp.route("/sales-orders/<int:so_id>/cancel", methods=["POST"])
@login_required
def sales_order_cancel(so_id):
    try:
        cancel_sales_order(tenant_id(), so_id)
        flash("销售订单已取消", "success")
    except ServiceError as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.sales_order_detail", so_id=so_id))


# ---------------- 发票 ----------------
@erp_bp.route("/invoices")
@login_required
def invoices():
    tid = tenant_id()
    rows = query(
        "SELECT i.*, so.so_no, c.name AS customer_name FROM invoices i "
        "JOIN sales_orders so ON i.sales_order_id=so.id "
        "JOIN customers c ON i.customer_id=c.id "
        "WHERE i.tenant_id=? ORDER BY i.id DESC LIMIT 100",
        (tid,),
    )
    return render_template("erp/invoices.html", invoices=rows)


# ---------------- 库存 ----------------
@erp_bp.route("/inventory")
@login_required
def inventory():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    sql = "SELECT * FROM products WHERE tenant_id=?"
    params = [tid]
    if q:
        sql += " AND (name LIKE ? OR sku LIKE ?)"
        params += [f"%{q}%"] * 2
    sql += " ORDER BY stock ASC, id DESC LIMIT 100"
    products = query(sql, params)
    moves = query(
        "SELECT m.*, p.name AS product_name, p.sku FROM inventory_moves m "
        "JOIN products p ON m.product_id=p.id WHERE m.tenant_id=? "
        "ORDER BY m.id DESC LIMIT 30",
        (tid,),
    )
    low_stock_count = sum(1 for p in products if p["stock"] <= p["safety_stock"])
    total_stock = sum(p["stock"] for p in products)
    return render_template(
        "erp/inventory.html",
        products=products,
        moves=moves,
        q=q,
        low_stock_count=low_stock_count,
        total_stock=total_stock,
    )


@erp_bp.route("/inventory/adjust", methods=["POST"])
@login_required
def inventory_adjust():
    tid = tenant_id()
    product_id = _int_or_none(request.form.get("product_id"))
    try:
        if not product_id:
            raise ServiceError("请选择产品")
        delta = int(request.form.get("qty_delta") or 0)
        if delta == 0:
            raise ServiceError("调整数量不能为 0")
        adjust_stock(tid, product_id, delta, request.form.get("note", "").strip(), g.user["id"])
        flash("库存调整成功", "success")
    except (ServiceError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("erp.inventory"))
