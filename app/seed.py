# -*- coding: utf-8 -*-
"""初始化测试数据：python -m app.seed"""
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from . import create_app
from .db import get_db, init_db


def ts(days=0, hours=0):
    return (datetime.now() - timedelta(days=days, hours=hours)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def seed():
    app = create_app()
    with app.app_context():
        init_db()
        db = get_db()

        # ---------------- 租户 ----------------
        db.executemany(
            "INSERT INTO tenants (name, code, created_at) VALUES (?, ?, ?)",
            [
                ("启明科技", "QM", ts(120)),
                ("远航集团", "YH", ts(90)),
            ],
        )
        tenant_a, tenant_b = 1, 2

        # ---------------- 用户 ----------------
        users = [
            (tenant_a, "admin", "admin123", "周跃明", "admin"),
            (tenant_a, "sales01", "sales123", "李娜", "sales"),
            (tenant_a, "warehouse01", "warehouse123", "王强", "warehouse"),
            (tenant_a, "finance01", "finance123", "陈静", "finance"),
            (tenant_b, "admin_b", "admin123", "赵敏", "admin"),
            (tenant_b, "sales_b", "sales123", "刘洋", "sales"),
        ]
        user_ids = {}
        for tid, username, password, full_name, role in users:
            cur = db.execute(
                """INSERT INTO users (tenant_id, username, password_hash, full_name, role, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (tid, username, generate_password_hash(password), full_name, role, ts(100)),
            )
            user_ids[username] = cur.lastrowid

        admin_a = user_ids["admin"]
        sales_a = user_ids["sales01"]

        # ---------------- 客户 ----------------
        customers_a = [
            ("恒远制造有限公司", "张伟", "13800001001", "zhangwei@hengyuan.com", "战略", "active", admin_a),
            ("星河科技有限公司", "王芳", "13800001002", "wangfang@xinghe.com", "重要", "active", sales_a),
            ("蓝海物流集团", "李强", "13800001003", "liqiang@lanhai.com", "重要", "active", sales_a),
            ("智联电子有限公司", "赵敏", "13800001004", "zhaomin@zhilian.com", "普通", "active", sales_a),
            ("中科自动化", "陈晨", "13800001005", "chenchen@zhongke.com", "战略", "active", admin_a),
            ("云帆软件", "刘洋", "13800001006", "liuyang@yunfan.com", "普通", "active", sales_a),
            ("金桥贸易", "孙丽", "13800001007", "sunli@jinqiao.com", "普通", "active", sales_a),
            ("华信医疗", "周涛", "13800001008", "zhoutao@huaxin.com", "重要", "active", sales_a),
            ("东盛建材", "吴磊", "13800001009", "wulei@dongsheng.com", "普通", "inactive", sales_a),
            ("瑞达能源", "郑洁", "13800001010", "zhengjie@ruida.com", "重要", "active", admin_a),
        ]
        customer_ids = []
        for name, contact, phone, email, level, status, owner in customers_a:
            cur = db.execute(
                """INSERT INTO customers
                   (tenant_id, name, contact, phone, email, level, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_a, name, contact, phone, email, level, status, owner, ts(60)),
            )
            customer_ids.append(cur.lastrowid)

        # 租户 B 的客户（用于隔离测试）
        for name in ["远航一客户", "远航二客户", "远航三客户"]:
            db.execute(
                """INSERT INTO customers (tenant_id, name, contact, phone, email, level, status, owner_id, created_at)
                   VALUES (?, ?, '测试联系人', '13900000000', 'b@example.com', '普通', 'active', ?, ?)""",
                (tenant_b, name, user_ids["sales_b"], ts(40)),
            )

        # ---------------- 线索 ----------------
        leads = [
            ("华东智能仓储项目", "张经理", "13700002001", "zhang@example.com", "展会", "new", sales_a),
            ("西南冷链配送升级", "李经理", "13700002002", "li@example.com", "官网", "contacted", sales_a),
            ("华南电子厂 MES 改造", "王经理", "13700002003", "wang@example.com", "转介绍", "qualified", admin_a),
            ("华北医疗设备采购", "赵经理", "13700002004", "zhao@example.com", "电话营销", "new", sales_a),
            ("东南亚出海项目", "陈经理", "13700002005", "chen@example.com", "展会", "lost", sales_a),
            ("智慧园区一期", "刘经理", "13700002006", "liu@example.com", "广告投放", "new", sales_a),
        ]
        for name, contact, phone, email, source, status, owner in leads:
            db.execute(
                """INSERT INTO leads
                   (tenant_id, name, contact, phone, email, source, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_a, name, contact, phone, email, source, status, owner, ts(30)),
            )

        # ---------------- 商机 ----------------
        opportunities = [
            ("恒远制造 - 智能仓储一期", customer_ids[0], 380000, "proposal", admin_a, "2026-11-30"),
            ("星河科技 - 设备管理平台", customer_ids[1], 220000, "negotiation", sales_a, "2026-11-15"),
            ("蓝海物流 - 冷链监控", customer_ids[2], 156000, "qualified", sales_a, "2026-12-10"),
            ("智联电子 - 产线数据采集", customer_ids[3], 98000, "new", sales_a, "2026-12-20"),
            ("中科自动化 - 边缘计算项目", customer_ids[4], 520000, "won", admin_a, "2026-10-01"),
            ("云帆软件 - 运维管理模块", customer_ids[5], 76000, "lost", sales_a, "2026-09-20"),
            ("华信医疗 - 设备联网", customer_ids[7], 268000, "proposal", sales_a, "2026-11-25"),
            ("瑞达能源 - 能耗监测", customer_ids[9], 410000, "negotiation", admin_a, "2026-12-05"),
        ]
        for name, customer_id, amount, stage, owner, expected in opportunities:
            db.execute(
                """INSERT INTO opportunities
                   (tenant_id, name, customer_id, amount, stage, expected_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_a, name, customer_id, amount, stage, expected, owner, ts(25)),
            )

        # ---------------- 合同 ----------------
        contracts = [
            ("HT20260918001", customer_ids[0], 380000, "signed", "2026-09-18"),
            ("HT20260925002", customer_ids[4], 520000, "signed", "2026-09-25"),
            ("HT20261008003", customer_ids[1], 220000, "draft", "2026-10-08"),
            ("HT20261015004", customer_ids[7], 268000, "signed", "2026-10-15"),
        ]
        for no, customer_id, amount, status, sign_date in contracts:
            db.execute(
                """INSERT INTO contracts
                   (tenant_id, contract_no, customer_id, amount, status, sign_date, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tenant_a, no, customer_id, amount, status, sign_date, ts(20)),
            )

        # ---------------- 产品 ----------------
        products_data = [
            ("QK-GW-001", "智能网关 Pro", "硬件", 1280, 760, 120, 20),
            ("QK-SN-002", "工业传感器 X1", "硬件", 360, 180, 8, 15),
            ("QK-DA-003", "数据采集器 D200", "硬件", 880, 520, 45, 10),
            ("QK-EC-004", "边缘计算盒 E5", "硬件", 2680, 1800, 200, 30),
            ("QK-TC-005", "无线温控器 T3", "硬件", 260, 120, 5, 10),
            ("QK-SC-006", "条码扫描枪 S8", "硬件", 620, 350, 60, 10),
            ("QK-SW-007", "工业交换机 SW-24", "硬件", 1450, 900, 18, 10),
            ("QK-EM-008", "环境监测仪 M2", "硬件", 1980, 1200, 90, 15),
            ("QK-SF-009", "设备管理软件（标准版）", "软件", 6800, 0, 999, 0),
            ("QK-SV-010", "实施服务包", "服务", 12000, 0, 999, 0),
        ]
        product_ids = []
        for sku, name, category, price, cost, stock, safety in products_data:
            cur = db.execute(
                """INSERT INTO products
                   (tenant_id, sku, name, category, price, cost, stock, safety_stock, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_a, sku, name, category, price, cost, stock, safety, ts(80)),
            )
            product_ids.append(cur.lastrowid)

        for sku, name in [("YH-P-001", "远航专用网关"), ("YH-P-002", "远航传感器")]:
            db.execute(
                """INSERT INTO products (tenant_id, sku, name, category, price, cost, stock, safety_stock, created_at)
                   VALUES (?, ?, ?, '硬件', 1000, 600, 30, 5, ?)""",
                (tenant_b, sku, name, ts(50)),
            )

        # ---------------- 供应商 ----------------
        suppliers = [
            ("华芯电子有限公司", "林工", "13600003001", "lin@huaxin.com"),
            ("精工制造", "许经理", "13600003002", "xu@jinggong.com"),
            ("宏达包装", "何经理", "13600003003", "he@hongda.com"),
            ("云启软件", "唐经理", "13600003004", "tang@yunqi.com"),
        ]
        supplier_ids = []
        for name, contact, phone, email in suppliers:
            cur = db.execute(
                """INSERT INTO suppliers (tenant_id, name, contact, phone, email, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (tenant_a, name, contact, phone, email, ts(70)),
            )
            supplier_ids.append(cur.lastrowid)

        # ---------------- 采购订单 ----------------
        def add_po(no, supplier_id, status, items, days, received_days=None):
            total = round(sum(q * p for _pid, q, p in items), 2)
            cur = db.execute(
                """INSERT INTO purchase_orders
                   (tenant_id, po_no, supplier_id, status, total_amount, created_by, created_at, received_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tenant_a,
                    no,
                    supplier_id,
                    status,
                    total,
                    admin_a,
                    ts(days),
                    ts(received_days) if received_days is not None else None,
                ),
            )
            po_id = cur.lastrowid
            for pid, qty, price in items:
                db.execute(
                    "INSERT INTO purchase_items (po_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                    (po_id, pid, qty, price),
                )
                if status == "received":
                    db.execute(
                        """INSERT INTO inventory_moves
                           (tenant_id, product_id, move_type, qty, ref_no, note, created_at)
                           VALUES (?, ?, 'in', ?, ?, '采购收货', ?)""",
                        (tenant_a, pid, qty, no, ts(received_days or days)),
                    )

        add_po("PO20261010001", supplier_ids[0], "received", [(product_ids[1], 30, 180), (product_ids[4], 20, 120)], 15, 13)
        add_po("PO20261022002", supplier_ids[1], "confirmed", [(product_ids[3], 50, 1800)], 3)
        add_po("PO20261026003", supplier_ids[2], "draft", [(product_ids[5], 10, 350)], 1)
        add_po("PO20260928004", supplier_ids[3], "received", [(product_ids[8], 100, 0)], 30, 28)

        # ---------------- 销售订单 ----------------
        def add_so(no, customer_id, status, items, days, shipped_days=None):
            total = round(sum(q * p for _pid, q, p in items), 2)
            cur = db.execute(
                """INSERT INTO sales_orders
                   (tenant_id, so_no, customer_id, status, total_amount, created_by, created_at, shipped_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tenant_a,
                    no,
                    customer_id,
                    status,
                    total,
                    sales_a,
                    ts(days),
                    ts(shipped_days) if shipped_days is not None else None,
                ),
            )
            so_id = cur.lastrowid
            for pid, qty, price in items:
                db.execute(
                    "INSERT INTO sales_items (so_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
                    (so_id, pid, qty, price),
                )
                if status == "shipped":
                    db.execute(
                        """INSERT INTO inventory_moves
                           (tenant_id, product_id, move_type, qty, ref_no, note, created_at)
                           VALUES (?, ?, 'out', ?, ?, '销售发货', ?)""",
                        (tenant_a, pid, qty, no, ts(shipped_days or days)),
                    )

        add_so("SO20261005001", customer_ids[0], "shipped", [(product_ids[0], 2, 1280), (product_ids[2], 1, 880)], 5, 3)
        add_so("SO20261016002", customer_ids[1], "shipped", [(product_ids[3], 5, 2680), (product_ids[5], 2, 620)], 12, 10)
        add_so("SO20261026003", customer_ids[2], "confirmed", [(product_ids[0], 1, 1280), (product_ids[1], 1, 360)], 2)
        add_so("SO20261027004", customer_ids[3], "draft", [(product_ids[4], 2, 260)], 1)
        add_so("SO20261008005", customer_ids[4], "shipped", [(product_ids[6], 3, 1450)], 20, 18)
        add_so("SO20261020006", customer_ids[5], "cancelled", [(product_ids[2], 1, 880)], 8)

        # 已发货订单的发票
        for so_no, invoice_no, days in [
            ("SO20261005001", "INV20261005001", 3),
            ("SO20261016002", "INV20261016002", 10),
            ("SO20261008005", "INV20261008005", 18),
        ]:
            so = db.execute(
                "SELECT * FROM sales_orders WHERE tenant_id=? AND so_no=?",
                (tenant_a, so_no),
            ).fetchone()
            db.execute(
                """INSERT INTO invoices
                   (tenant_id, invoice_no, sales_order_id, customer_id, amount, status, created_by, created_at)
                   VALUES (?, ?, ?, ?, ?, 'issued', ?, ?)""",
                (
                    tenant_a,
                    invoice_no,
                    so["id"],
                    so["customer_id"],
                    so["total_amount"],
                    admin_a,
                    ts(days),
                ),
            )

        # 租户 B 的一笔订单，用于隔离测试
        db.execute(
            """INSERT INTO sales_orders
               (tenant_id, so_no, customer_id, status, total_amount, created_by, created_at)
               VALUES (?, 'SO-B-001', 11, 'draft', 1000, ?, ?)""",
            (tenant_b, user_ids["sales_b"], ts(5)),
        )

        db.commit()
        print("seed done: tenant A/B, users, customers, leads, opportunities, contracts, products, suppliers, orders")
        print("login: admin / admin123")


if __name__ == "__main__":
    seed()
