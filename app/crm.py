# -*- coding: utf-8 -*-
"""CRM：客户、线索、商机、合同。"""
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
from .constants import STAGES
from .db import get_db, query
from .services import ServiceError, convert_lead, next_no, today_str

crm_bp = Blueprint("crm", __name__, url_prefix="/crm")


def _owners(tid):
    return query(
        "SELECT * FROM users WHERE tenant_id=? AND active=1 AND role IN ('admin','sales') "
        "ORDER BY id",
        (tid,),
    )


def _customer_or_404(tid, cid):
    customer = query(
        "SELECT c.*, u.full_name AS owner_name FROM customers c "
        "LEFT JOIN users u ON c.owner_id=u.id "
        "WHERE c.id=? AND c.tenant_id=?",
        (cid, tid),
        one=True,
    )
    if customer is None:
        abort(404)
    return customer


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


# ---------------- 客户 ----------------
@crm_bp.route("/customers")
@login_required
def customers():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or ""
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
    sql += " ORDER BY c.id DESC LIMIT 100"
    rows = query(sql, params)
    return render_template(
        "crm/customers.html", customers=rows, q=q, status=status, owners=_owners(tid)
    )


@crm_bp.route("/customers/new", methods=["GET", "POST"])
@login_required
def customer_new():
    tid = tenant_id()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("客户名称不能为空", "error")
        else:
            owner_id = _int_or_none(request.form.get("owner_id"))
            if owner_id is not None and not query(
                "SELECT 1 FROM users WHERE id=? AND tenant_id=?", (owner_id, tid), one=True
            ):
                owner_id = None
            db = get_db()
            db.execute(
                """INSERT INTO customers
                   (tenant_id, name, contact, phone, email, level, status, owner_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid,
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("level", "普通"),
                    request.form.get("status", "active"),
                    owner_id,
                ),
            )
            db.commit()
            flash("客户创建成功", "success")
            return redirect(url_for("crm.customers"))
    return render_template(
        "crm/customer_form.html", customer=None, owners=_owners(tid)
    )


@crm_bp.route("/customers/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def customer_edit(cid):
    tid = tenant_id()
    customer = _customer_or_404(tid, cid)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("客户名称不能为空", "error")
        else:
            owner_id = _int_or_none(request.form.get("owner_id"))
            if owner_id is not None and not query(
                "SELECT 1 FROM users WHERE id=? AND tenant_id=?", (owner_id, tid), one=True
            ):
                owner_id = None
            db = get_db()
            db.execute(
                """UPDATE customers SET name=?, contact=?, phone=?, email=?,
                   level=?, status=?, owner_id=? WHERE id=? AND tenant_id=?""",
                (
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("level", "普通"),
                    request.form.get("status", "active"),
                    owner_id,
                    cid,
                    tid,
                ),
            )
            db.commit()
            flash("客户信息已更新", "success")
            return redirect(url_for("crm.customer_detail", cid=cid))
    return render_template(
        "crm/customer_form.html", customer=customer, owners=_owners(tid)
    )


@crm_bp.route("/customers/<int:cid>")
@login_required
def customer_detail(cid):
    tid = tenant_id()
    customer = _customer_or_404(tid, cid)
    opportunities = query(
        "SELECT * FROM opportunities WHERE tenant_id=? AND customer_id=? ORDER BY id DESC",
        (tid, cid),
    )
    contracts = query(
        "SELECT * FROM contracts WHERE tenant_id=? AND customer_id=? ORDER BY id DESC",
        (tid, cid),
    )
    orders = query(
        "SELECT * FROM sales_orders WHERE tenant_id=? AND customer_id=? ORDER BY id DESC",
        (tid, cid),
    )
    return render_template(
        "crm/customer_detail.html",
        customer=customer,
        opportunities=opportunities,
        contracts=contracts,
        orders=orders,
    )


@crm_bp.route("/customers/<int:cid>/archive", methods=["POST"])
@login_required
def customer_archive(cid):
    tid = tenant_id()
    _customer_or_404(tid, cid)
    get_db().execute(
        "UPDATE customers SET status='inactive' WHERE id=? AND tenant_id=?", (cid, tid)
    )
    get_db().commit()
    flash("客户已归档", "success")
    return redirect(url_for("crm.customers"))


# ---------------- 线索 ----------------
@crm_bp.route("/leads")
@login_required
def leads():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or ""
    sql = (
        "SELECT l.*, u.full_name AS owner_name FROM leads l "
        "LEFT JOIN users u ON l.owner_id=u.id WHERE l.tenant_id=?"
    )
    params = [tid]
    if q:
        sql += " AND (l.name LIKE ? OR l.contact LIKE ? OR l.phone LIKE ?)"
        params += [f"%{q}%"] * 3
    if status:
        sql += " AND l.status=?"
        params.append(status)
    sql += " ORDER BY l.id DESC LIMIT 100"
    return render_template(
        "crm/leads.html", leads=query(sql, params), q=q, status=status
    )


@crm_bp.route("/leads/new", methods=["GET", "POST"])
@login_required
def lead_new():
    tid = tenant_id()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("线索名称不能为空", "error")
        else:
            owner_id = _int_or_none(request.form.get("owner_id"))
            get_db().execute(
                """INSERT INTO leads
                   (tenant_id, name, contact, phone, email, source, status, owner_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid,
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("source", "").strip(),
                    request.form.get("status", "new"),
                    owner_id,
                ),
            )
            get_db().commit()
            flash("线索创建成功", "success")
            return redirect(url_for("crm.leads"))
    return render_template("crm/lead_form.html", lead=None, owners=_owners(tid))


@crm_bp.route("/leads/<int:lid>/edit", methods=["GET", "POST"])
@login_required
def lead_edit(lid):
    tid = tenant_id()
    lead = query(
        "SELECT * FROM leads WHERE id=? AND tenant_id=?", (lid, tid), one=True
    )
    if lead is None:
        abort(404)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("线索名称不能为空", "error")
        else:
            owner_id = _int_or_none(request.form.get("owner_id"))
            get_db().execute(
                """UPDATE leads SET name=?, contact=?, phone=?, email=?,
                   source=?, status=?, owner_id=? WHERE id=? AND tenant_id=?""",
                (
                    name,
                    request.form.get("contact", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("email", "").strip(),
                    request.form.get("source", "").strip(),
                    request.form.get("status", "new"),
                    owner_id,
                    lid,
                    tid,
                ),
            )
            get_db().commit()
            flash("线索已更新", "success")
            return redirect(url_for("crm.leads"))
    return render_template("crm/lead_form.html", lead=lead, owners=_owners(tid))


@crm_bp.route("/leads/<int:lid>/convert", methods=["POST"])
@login_required
def lead_convert(lid):
    tid = tenant_id()
    try:
        _customer_id, opportunity_id = convert_lead(tid, lid, g.user["id"])
    except ServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("crm.leads"))
    flash("线索已转化为客户和商机", "success")
    return redirect(url_for("crm.opportunity_edit", oid=opportunity_id))


# ---------------- 商机 ----------------
@crm_bp.route("/opportunities")
@login_required
def opportunities():
    tid = tenant_id()
    q = (request.args.get("q") or "").strip()
    sql = (
        "SELECT o.*, c.name AS customer_name, u.full_name AS owner_name "
        "FROM opportunities o JOIN customers c ON o.customer_id=c.id "
        "LEFT JOIN users u ON o.owner_id=u.id WHERE o.tenant_id=?"
    )
    params = [tid]
    if q:
        sql += " AND (o.name LIKE ? OR c.name LIKE ?)"
        params += [f"%{q}%"] * 2
    sql += " ORDER BY o.id DESC"
    rows = query(sql, params)
    board = {key: [] for key, _label in STAGES}
    for row in rows:
        board.setdefault(row["stage"], []).append(row)
    return render_template(
        "crm/opportunities.html", board=board, stages=STAGES, q=q, total=len(rows)
    )


@crm_bp.route("/opportunities/new", methods=["GET", "POST"])
@login_required
def opportunity_new():
    tid = tenant_id()
    customers = query(
        "SELECT * FROM customers WHERE tenant_id=? AND status='active' ORDER BY name",
        (tid,),
    )
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        customer_id = _int_or_none(request.form.get("customer_id"))
        if not name:
            flash("商机名称不能为空", "error")
        elif not customer_id or not query(
            "SELECT 1 FROM customers WHERE id=? AND tenant_id=?", (customer_id, tid), one=True
        ):
            flash("请选择有效的客户", "error")
        else:
            get_db().execute(
                """INSERT INTO opportunities
                   (tenant_id, name, customer_id, amount, stage, expected_date, owner_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    tid,
                    name,
                    customer_id,
                    _float(request.form.get("amount")),
                    request.form.get("stage", "new"),
                    request.form.get("expected_date") or None,
                    _int_or_none(request.form.get("owner_id")),
                ),
            )
            get_db().commit()
            flash("商机创建成功", "success")
            return redirect(url_for("crm.opportunities"))
    return render_template(
        "crm/opportunity_form.html",
        opportunity=None,
        customers=customers,
        owners=_owners(tid),
        stages=STAGES,
    )


@crm_bp.route("/opportunities/<int:oid>/edit", methods=["GET", "POST"])
@login_required
def opportunity_edit(oid):
    tid = tenant_id()
    opportunity = query(
        "SELECT * FROM opportunities WHERE id=? AND tenant_id=?", (oid, tid), one=True
    )
    if opportunity is None:
        abort(404)
    customers = query(
        "SELECT * FROM customers WHERE tenant_id=? AND status='active' ORDER BY name",
        (tid,),
    )
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        customer_id = _int_or_none(request.form.get("customer_id"))
        if not name:
            flash("商机名称不能为空", "error")
        elif not customer_id or not query(
            "SELECT 1 FROM customers WHERE id=? AND tenant_id=?", (customer_id, tid), one=True
        ):
            flash("请选择有效的客户", "error")
        else:
            get_db().execute(
                """UPDATE opportunities SET name=?, customer_id=?, amount=?, stage=?,
                   expected_date=?, owner_id=? WHERE id=? AND tenant_id=?""",
                (
                    name,
                    customer_id,
                    _float(request.form.get("amount")),
                    request.form.get("stage", "new"),
                    request.form.get("expected_date") or None,
                    _int_or_none(request.form.get("owner_id")),
                    oid,
                    tid,
                ),
            )
            get_db().commit()
            flash("商机已更新", "success")
            return redirect(url_for("crm.opportunities"))
    return render_template(
        "crm/opportunity_form.html",
        opportunity=opportunity,
        customers=customers,
        owners=_owners(tid),
        stages=STAGES,
    )


# ---------------- 合同 ----------------
@crm_bp.route("/contracts")
@login_required
def contracts():
    tid = tenant_id()
    rows = query(
        "SELECT ct.*, c.name AS customer_name FROM contracts ct "
        "JOIN customers c ON ct.customer_id=c.id "
        "WHERE ct.tenant_id=? ORDER BY ct.id DESC LIMIT 100",
        (tid,),
    )
    return render_template("crm/contracts.html", contracts=rows)


@crm_bp.route("/contracts/new", methods=["GET", "POST"])
@login_required
def contract_new():
    tid = tenant_id()
    customers = query(
        "SELECT * FROM customers WHERE tenant_id=? AND status='active' ORDER BY name",
        (tid,),
    )
    if request.method == "POST":
        customer_id = _int_or_none(request.form.get("customer_id"))
        if not customer_id or not query(
            "SELECT 1 FROM customers WHERE id=? AND tenant_id=?", (customer_id, tid), one=True
        ):
            flash("请选择有效的客户", "error")
        else:
            contract_no = (request.form.get("contract_no") or "").strip() or next_no("HT")
            get_db().execute(
                """INSERT INTO contracts
                   (tenant_id, contract_no, customer_id, amount, status, sign_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    tid,
                    contract_no,
                    customer_id,
                    _float(request.form.get("amount")),
                    request.form.get("status", "draft"),
                    request.form.get("sign_date") or today_str(),
                ),
            )
            get_db().commit()
            flash("合同创建成功", "success")
            return redirect(url_for("crm.contracts"))
    return render_template(
        "crm/contract_form.html", customers=customers, today=today_str()
    )
