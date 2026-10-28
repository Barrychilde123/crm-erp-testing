# -*- coding: utf-8 -*-
"""轻量级 CRM/ERP 测试靶场。"""
import os
from datetime import datetime

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from .auth import init_app as init_auth, login_required, role_required
from .constants import ROLE_TEXT, STAGES, STATUS_CLASS, STATUS_TEXT
from .db import close_db, query, scalar


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev-secret-change-me",
        DATABASE=os.path.join(app.instance_path, "crm_erp.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(close_db)
    init_auth(app)

    from .api import api_bp
    from .crm import crm_bp
    from .erp import erp_bp
    from .saas import saas_bp

    app.register_blueprint(crm_bp)
    app.register_blueprint(erp_bp)
    app.register_blueprint(saas_bp)
    app.register_blueprint(api_bp)

    # ---------- 模板过滤器 ----------
    @app.template_filter("money")
    def money(value):
        try:
            return f"{float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "0.00"

    @app.template_filter("date")
    def fmt_date(value):
        return (value or "")[:16]

    @app.template_filter("status_text")
    def status_text(value):
        return STATUS_TEXT.get(value, value or "")

    @app.template_filter("status_class")
    def status_class(value):
        return STATUS_CLASS.get(value, "gray")

    @app.template_filter("role_text")
    def role_text(value):
        return ROLE_TEXT.get(value, value or "")

    # ---------- 登录 / 登出 ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.get("user"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = query(
                "SELECT * FROM users WHERE username=? AND active=1", (username,), one=True
            )
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("用户名或密码错误", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["tenant_id"] = user["tenant_id"]
                flash(f"欢迎回来，{user['full_name']}", "success")
                next_url = request.args.get("next") or request.form.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("已退出登录", "success")
        return redirect(url_for("login"))

    # ---------- 仪表盘 ----------
    @app.route("/")
    @login_required
    def dashboard():
        tid = g.tenant["id"]
        stats = {
            "customers": scalar(
                "SELECT COUNT(*) FROM customers WHERE tenant_id=? AND status='active'", (tid,)
            ),
            "open_opps": scalar(
                "SELECT COALESCE(SUM(amount),0) FROM opportunities "
                "WHERE tenant_id=? AND stage NOT IN ('won','lost')",
                (tid,),
            ),
            "pending_pos": scalar(
                "SELECT COUNT(*) FROM purchase_orders "
                "WHERE tenant_id=? AND status IN ('draft','confirmed')",
                (tid,),
            ),
            "low_stock": scalar(
                "SELECT COUNT(*) FROM products WHERE tenant_id=? AND stock<=safety_stock",
                (tid,),
            ),
            "month_sales": scalar(
                "SELECT COALESCE(SUM(total_amount),0) FROM sales_orders "
                "WHERE tenant_id=? AND status='shipped' "
                "AND strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime')",
                (tid,),
            ),
        }

        pipeline_rows = query(
            "SELECT stage, COUNT(*) cnt, COALESCE(SUM(amount),0) amount "
            "FROM opportunities WHERE tenant_id=? GROUP BY stage",
            (tid,),
        )
        pipeline_map = {row["stage"]: row for row in pipeline_rows}
        max_amount = max([row["amount"] for row in pipeline_rows] or [1]) or 1
        pipeline = []
        for key, label in STAGES:
            row = pipeline_map.get(key)
            amount = row["amount"] if row else 0
            count = row["cnt"] if row else 0
            pipeline.append(
                {
                    "key": key,
                    "label": label,
                    "amount": amount,
                    "count": count,
                    "pct": max(4, int(amount / max_amount * 100)) if amount else 4,
                }
            )

        low_stock_products = query(
            "SELECT * FROM products WHERE tenant_id=? AND stock<=safety_stock "
            "ORDER BY stock ASC, id ASC LIMIT 5",
            (tid,),
        )
        recent_sales = query(
            "SELECT so.*, c.name AS customer_name FROM sales_orders so "
            "JOIN customers c ON so.customer_id=c.id "
            "WHERE so.tenant_id=? ORDER BY so.id DESC LIMIT 5",
            (tid,),
        )
        recent_pos = query(
            "SELECT po.*, s.name AS supplier_name FROM purchase_orders po "
            "JOIN suppliers s ON po.supplier_id=s.id "
            "WHERE po.tenant_id=? ORDER BY po.id DESC LIMIT 5",
            (tid,),
        )
        activity = query(
            "SELECT m.*, p.name AS product_name FROM inventory_moves m "
            "JOIN products p ON m.product_id=p.id "
            "WHERE m.tenant_id=? ORDER BY m.id DESC LIMIT 6",
            (tid,),
        )
        return render_template(
            "dashboard.html",
            stats=stats,
            pipeline=pipeline,
            low_stock_products=low_stock_products,
            recent_sales=recent_sales,
            recent_pos=recent_pos,
            activity=activity,
        )

    # ---------- 租户切换 ----------
    @app.route("/switch-tenant/<int:tid>")
    @role_required("admin")
    def switch_tenant(tid):
        tenant = query("SELECT * FROM tenants WHERE id=?", (tid,), one=True)
        if tenant is None:
            flash("租户不存在", "error")
        else:
            session["tenant_id"] = tid
            flash(f"已切换到 {tenant['name']}", "success")
        return redirect(request.referrer or url_for("dashboard"))

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok", "time": datetime.now().isoformat()})

    # ---------- 错误页 ----------
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="无权访问该页面"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="页面不存在"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", code=500, message="服务器内部错误"), 500

    return app
