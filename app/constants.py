# -*- coding: utf-8 -*-
"""状态与阶段常量。"""

ROLE_TEXT = {
    "admin": "管理员",
    "sales": "销售",
    "warehouse": "仓管",
    "finance": "财务",
}

STATUS_TEXT = {
    "active": "合作中",
    "inactive": "已归档",
    "draft": "草稿",
    "confirmed": "已确认",
    "received": "已收货",
    "shipped": "已发货",
    "cancelled": "已取消",
    "new": "新建",
    "contacted": "已联系",
    "qualified": "已确认",
    "converted": "已转化",
    "lost": "已流失",
    "proposal": "方案报价",
    "negotiation": "谈判中",
    "won": "赢单",
    "signed": "已签署",
    "closed": "已关闭",
}

STATUS_CLASS = {
    "active": "success",
    "signed": "success",
    "received": "success",
    "shipped": "success",
    "won": "success",
    "qualified": "success",
    "draft": "gray",
    "new": "info",
    "contacted": "primary",
    "proposal": "primary",
    "negotiation": "warning",
    "confirmed": "warning",
    "inactive": "gray",
    "closed": "gray",
    "cancelled": "danger",
    "lost": "danger",
}

STAGES = [
    ("new", "新建"),
    ("qualified", "已确认"),
    ("proposal", "方案报价"),
    ("negotiation", "谈判中"),
    ("won", "赢单"),
    ("lost", "输单"),
]
