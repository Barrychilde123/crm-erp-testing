# -*- coding: utf-8 -*-
"""登录态、角色权限与模板全局变量。"""
from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for

from .db import query


def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    g.tenant = None
    if not user_id:
        return
    user = query(
        "SELECT * FROM users WHERE id=? AND active=1", (user_id,), one=True
    )
    if user is None:
        session.clear()
        return
    g.user = user
    tenant_id = session.get("tenant_id") or user["tenant_id"]
    tenant = query("SELECT * FROM tenants WHERE id=?", (tenant_id,), one=True)
    if tenant is None:
        tenant = query("SELECT * FROM tenants WHERE id=?", (user["tenant_id"],), one=True)
        session["tenant_id"] = user["tenant_id"]
    g.tenant = tenant


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.get("user") is None:
                return redirect(url_for("login", next=request.path))
            if g.user["role"] not in roles:
                from flask import render_template

                return render_template(
                    "error.html", code=403, message="当前角色无权访问该页面"
                ), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return jsonify({"code": 401, "message": "未登录或会话已过期", "data": None}), 401
        return view(*args, **kwargs)

    return wrapped


def tenant_id():
    return g.tenant["id"] if g.get("tenant") else None


def init_app(app):
    app.before_request(load_logged_in_user)

    @app.context_processor
    def inject_globals():
        tenants = []
        if g.get("user") and g.user["role"] == "admin":
            tenants = query("SELECT * FROM tenants ORDER BY id")
        return {
            "current_user": g.get("user"),
            "current_tenant": g.get("tenant"),
            "tenant_list": tenants,
            "is_admin": bool(g.get("user") and g.user["role"] == "admin"),
        }
