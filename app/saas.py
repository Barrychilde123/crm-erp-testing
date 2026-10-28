# -*- coding: utf-8 -*-
"""SaaS：租户、用户、角色权限。"""
import sqlite3

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import generate_password_hash

from .auth import role_required, tenant_id
from .db import get_db, query
from .services import ServiceError, create_tenant

saas_bp = Blueprint("saas", __name__, url_prefix="/saas")

ROLE_TEXT = {
    "admin": "管理员",
    "sales": "销售",
    "warehouse": "仓管",
    "finance": "财务",
}


@saas_bp.route("/tenants", methods=["GET", "POST"])
@role_required("admin")
def tenants():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        code = (request.form.get("code") or "").strip().upper()
        admin_username = (request.form.get("admin_username") or "").strip()
        admin_password = request.form.get("admin_password") or ""
        full_name = (request.form.get("full_name") or "租户管理员").strip()
        if not name or not code or not admin_username or not admin_password:
            flash("租户名称、编码、管理员账号和密码不能为空", "error")
        else:
            try:
                create_tenant(name, code, admin_username, admin_password, full_name)
                flash("租户创建成功", "success")
                return redirect(url_for("saas.tenants"))
            except sqlite3.IntegrityError:
                flash("租户编码或管理员账号已存在", "error")
            except ServiceError as exc:
                flash(str(exc), "error")
    rows = query(
        "SELECT t.*, (SELECT COUNT(*) FROM users u WHERE u.tenant_id=t.id) AS user_count, "
        "(SELECT COUNT(*) FROM customers c WHERE c.tenant_id=t.id) AS customer_count "
        "FROM tenants t ORDER BY t.id"
    )
    return render_template("saas/tenants.html", tenants=rows)


@saas_bp.route("/users", methods=["GET"])
@role_required("admin")
def users():
    tid = tenant_id()
    rows = query(
        "SELECT * FROM users WHERE tenant_id=? ORDER BY id", (tid,)
    )
    return render_template(
        "saas/users.html", users=rows, roles=ROLE_TEXT, current_tenant_id=tid
    )


@saas_bp.route("/users/new", methods=["GET", "POST"])
@role_required("admin")
def user_new():
    tid = tenant_id()
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        role = request.form.get("role", "sales")
        if not username or not password or not full_name:
            flash("账号、密码和姓名不能为空", "error")
        elif role not in ROLE_TEXT:
            flash("角色不合法", "error")
        else:
            try:
                get_db().execute(
                    """INSERT INTO users (tenant_id, username, password_hash, full_name, role)
                       VALUES (?, ?, ?, ?, ?)""",
                    (tid, username, generate_password_hash(password), full_name, role),
                )
                get_db().commit()
                flash("用户创建成功", "success")
                return redirect(url_for("saas.users"))
            except sqlite3.IntegrityError:
                flash("该租户下账号已存在", "error")
    return render_template("saas/user_form.html", roles=ROLE_TEXT)


@saas_bp.route("/users/<int:uid>/toggle", methods=["POST"])
@role_required("admin")
def user_toggle(uid):
    tid = tenant_id()
    user = query(
        "SELECT * FROM users WHERE id=? AND tenant_id=?", (uid, tid), one=True
    )
    if user is None:
        flash("用户不存在", "error")
    elif user["id"] == g.user["id"]:
        flash("不能停用当前登录账号", "error")
    else:
        get_db().execute(
            "UPDATE users SET active=? WHERE id=? AND tenant_id=?",
            (0 if user["active"] else 1, uid, tid),
        )
        get_db().commit()
        flash("用户状态已更新", "success")
    return redirect(url_for("saas.users"))


@saas_bp.route("/roles")
@role_required("admin")
def roles():
    matrix = [
        ("客户 / 线索 / 商机", "✓", "✓", "—", "—"),
        ("合同", "✓", "✓", "—", "✓"),
        ("产品 / 库存", "✓", "查看", "✓", "—"),
        ("采购订单", "✓", "—", "✓", "—"),
        ("销售订单", "✓", "✓", "查看", "查看"),
        ("财务 / 报表", "✓", "—", "—", "✓"),
        ("租户 / 用户管理", "✓", "—", "—", "—"),
    ]
    return render_template("saas/roles.html", matrix=matrix)
