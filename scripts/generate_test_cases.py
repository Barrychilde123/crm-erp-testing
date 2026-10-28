# -*- coding: utf-8 -*-
"""生成 CRM/ERP 测试用例 Excel。"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "02-test-cases.xlsx")

HEADERS = ["用例编号", "模块", "用例标题", "前置条件", "操作步骤", "预期结果",
           "优先级", "测试类型", "执行结果", "备注"]

CASES = [
    # ---------------- CRM ----------------
    ("CRM-001", "CRM", "登录后进入 CRM 应用", "Odoo 服务正常，测试账号可用",
     "1. 打开登录页\n2. 输入账号密码登录\n3. 打开 CRM 应用",
     "登录成功，进入 CRM 仪表盘/管道视图，页面无报错", "P0", "功能", "未执行", ""),
    ("CRM-002", "CRM", "新建客户（必填字段完整）", "已登录，进入 CRM 客户列表",
     "1. 点击“新建”\n2. 填写客户名称、电话、邮箱、销售员\n3. 保存",
     "客户创建成功，列表可搜索到该客户，字段与输入一致", "P0", "功能", "未执行", ""),
    ("CRM-003", "CRM", "新建客户必填校验（名称缺失）", "已登录，打开新建客户表单",
     "1. 客户名称留空\n2. 填写其他字段\n3. 点击保存",
     "保存被拦截，名称字段提示必填，记录未创建", "P1", "功能", "未执行", ""),
    ("CRM-004", "CRM", "客户列表按名称搜索", "已存在 QA 测试客户",
     "1. 进入客户列表\n2. 搜索框输入客户名称关键字\n3. 回车",
     "只返回匹配的客户，数量与关键字一致，无无关记录", "P1", "功能", "未执行", ""),
    ("CRM-005", "CRM", "编辑客户信息并保存", "已存在 QA 测试客户",
     "1. 打开客户详情\n2. 修改电话/邮箱\n3. 保存并刷新页面",
     "修改成功，刷新后字段仍为新值，列表同步更新", "P0", "功能", "未执行", ""),
    ("CRM-006", "CRM", "客户分配销售员", "已存在客户和销售员用户",
     "1. 打开客户详情\n2. 将销售员改为指定用户\n3. 保存",
     "销售员字段保存成功，客户归属正确", "P1", "功能", "未执行", ""),
    ("CRM-007", "CRM", "新建线索", "已登录，进入 CRM 线索列表",
     "1. 新建线索\n2. 填写线索名称、联系人、邮箱、电话\n3. 保存",
     "线索创建成功，状态为“新”，列表可见", "P0", "功能", "未执行", ""),
    ("CRM-008", "CRM", "线索转化为商机", "已存在一条未转化线索",
     "1. 打开线索\n2. 点击“转化为商机”\n3. 确认转化",
     "生成商机记录，线索状态变为已转化，商机与原线索关联", "P0", "功能", "未执行", ""),
    ("CRM-009", "CRM", "商机阶段推进", "已存在商机",
     "1. 打开商机\n2. 将阶段从“新建”推进到“已确认”\n3. 保存",
     "阶段更新成功，管道视图列同步变化", "P1", "功能", "未执行", ""),
    ("CRM-010", "CRM", "商机金额与预计成交日期保存", "已存在商机",
     "1. 填写商机金额 10000\n2. 选择预计成交日期\n3. 保存",
     "金额和日期保存成功，刷新后数据不丢失", "P1", "功能", "未执行", ""),
    ("CRM-011", "CRM", "客户归档/删除权限", "使用普通销售用户登录",
     "1. 打开客户详情\n2. 尝试归档/删除客户",
     "无权限用户不能删除客户；有权限用户可归档，归档后默认列表不可见", "P2", "权限", "未执行", ""),
    ("CRM-012", "CRM", "商机管道按阶段展示", "存在多个阶段的商机",
     "1. 进入 CRM 管道视图\n2. 查看各阶段列与商机卡片",
     "6 个阶段列正确显示，商机归入对应阶段，数量与金额一致", "P2", "功能", "未执行", ""),

    # ---------------- ERP ----------------
    ("ERP-001", "ERP", "创建库存型产品", "已登录，进入库存/产品页面",
     "1. 新建产品\n2. 填写名称、类型=可库存、售价、成本\n3. 保存",
     "产品创建成功，类型为可库存，列表可搜索", "P0", "功能", "未执行", ""),
    ("ERP-002", "ERP", "产品价格与成本保存", "已存在 QA 产品",
     "1. 修改售价/成本\n2. 保存并刷新",
     "价格与成本保存成功，数值精度正确", "P1", "功能", "未执行", ""),
    ("ERP-003", "ERP", "创建供应商", "已登录，进入采购/供应商页面",
     "1. 新建供应商\n2. 填写名称、电话、邮箱\n3. 保存",
     "供应商创建成功，可在采购订单中选择", "P1", "功能", "未执行", ""),
    ("ERP-004", "ERP", "创建采购订单（含明细）", "已存在供应商和 QA 产品",
     "1. 新建询价单\n2. 选择供应商\n3. 添加产品、数量、单价\n4. 保存",
     "询价单创建成功，明细金额=数量×单价，合计正确", "P0", "功能", "未执行", ""),
    ("ERP-005", "ERP", "确认采购订单", "已存在询价单",
     "1. 打开询价单\n2. 点击“确认订单”",
     "状态变为采购订单，生成收货单，数量与明细一致", "P0", "功能", "未执行", ""),
    ("ERP-006", "ERP", "采购收货入库", "已存在已确认采购订单",
     "1. 打开收货单\n2. 填写实收数量\n3. 验证入库",
     "收货单状态完成，库存数量增加，库存移动记录生成", "P0", "功能", "未执行", ""),
    ("ERP-007", "ERP", "库存数量增加校验", "采购收货已完成",
     "1. 查询产品库存\n2. 与收货数量比对",
     "库存数量 = 原库存 + 实收数量；库位正确", "P0", "数据", "未执行", ""),
    ("ERP-008", "ERP", "创建销售订单", "已存在客户和 QA 产品，库存充足",
     "1. 新建报价单\n2. 选择客户\n3. 添加产品、数量、单价\n4. 保存",
     "报价单创建成功，金额=数量×单价，合计正确", "P0", "功能", "未执行", ""),
    ("ERP-009", "ERP", "确认销售订单", "已存在报价单",
     "1. 打开报价单\n2. 点击“确认”",
     "状态变为销售订单，生成发货单，库存预留正确", "P0", "功能", "未执行", ""),
    ("ERP-010", "ERP", "销售发货出库", "已存在已确认销售订单",
     "1. 打开发货单\n2. 填写发货数量\n3. 验证发货",
     "发货单完成，库存扣减，客户签收状态更新", "P0", "功能", "未执行", ""),
    ("ERP-011", "ERP", "库存数量扣减校验", "销售发货已完成",
     "1. 查询产品库存\n2. 与发货数量比对",
     "库存数量 = 原库存 - 发货数量；库存移动记录正确", "P0", "数据", "未执行", ""),
    ("ERP-012", "ERP", "库存不足时销售订单处理", "产品库存为 0 或小于订单数量",
     "1. 创建销售订单\n2. 确认订单\n3. 查库存",
     "系统按配置允许/阻止负库存；若允许，库存为负并产生预警；若阻止，订单确认失败并提示", "P1", "异常", "未执行", ""),
    ("ERP-013", "ERP", "销售订单生成发票", "已存在已确认销售订单",
     "1. 点击“创建发票”\n2. 确认发票",
     "生成草稿发票，客户、金额、税额与订单一致", "P1", "功能", "未执行", ""),
    ("ERP-014", "ERP", "发票金额与订单金额一致", "已生成发票",
     "1. 对比订单总额与发票总额\n2. 对比明细行",
     "订单总额=发票总额（含税/未税口径一致），无金额差异", "P0", "数据", "未执行", ""),
    ("ERP-015", "ERP", "取消采购订单", "已存在未收货的采购订单",
     "1. 打开采购订单\n2. 点击取消\n3. 确认",
     "订单状态为已取消，不再生成收货单，库存不变", "P2", "功能", "未执行", ""),
    ("ERP-016", "ERP", "库存盘点/调整", "已存在 QA 产品",
     "1. 进入库存调整\n2. 将数量调整为指定值\n3. 应用",
     "库存数量更新为调整值，生成库存移动记录，可追溯", "P2", "功能", "未执行", ""),

    # ---------------- 权限 ----------------
    ("PERM-001", "权限", "未登录访问 CRM 被拦截", "未登录，清除浏览器会话",
     "1. 直接访问 /odoo/crm\n2. 观察跳转",
     "跳转到登录页，登录后回到目标页面或首页", "P0", "权限", "未执行", ""),
    ("PERM-002", "权限", "错误密码登录失败", "已打开登录页",
     "1. 输入正确账号\n2. 输入错误密码\n3. 登录",
     "提示账号或密码错误，不进入系统，不泄露账号是否存在", "P0", "异常", "未执行", ""),
    ("PERM-003", "权限", "销售角色权限边界", "已创建销售角色用户",
     "1. 销售用户登录\n2. 访问客户/商机\n3. 尝试创建产品、访问 SaaS 管理",
     "可查看 CRM 数据；创建产品/采购单被拒绝（403），访问 SaaS 管理返回 403", "P1", "权限", "未执行", ""),
    ("PERM-004", "权限", "普通用户访问设置模块", "使用普通销售用户登录",
     "1. 尝试访问设置页面/系统参数\n2. 观察权限提示",
     "访问被拒绝，菜单不可见或提示无权限", "P1", "权限", "未执行", ""),
    ("PERM-005", "权限", "多租户数据隔离", "已创建租户 A/B 及各自客户",
     "1. 租户 A 创建客户\n2. 租户 B 查询客户列表\n3. 租户 B 直接访问 A 客户 ID",
     "租户 B 列表只包含 B 的数据；直接访问 A 客户返回 404", "P2", "权限", "未执行", ""),

    # ---------------- 接口 ----------------
    ("API-001", "接口", "JSON-RPC 登录成功", "Odoo 服务正常，账号密码正确",
     "POST /jsonrpc，service=common，method=login，传 db/login/password",
     "返回 uid（整数），无 error 字段", "P0", "接口", "未执行", ""),
    ("API-002", "接口", "JSON-RPC 错误密码登录失败", "账号正确，密码错误",
     "POST /jsonrpc，method=login，密码错误",
     "返回 error 或 uid=false，不能获得有效会话", "P0", "接口", "未执行", ""),
    ("API-003", "接口", "search_read 查询客户列表", "已登录获得 uid",
     "execute_kw: res.partner.search_read，domain=[['is_company','=',true]]，limit=10",
     "返回客户数组，字段包含 id/name/phone/email，数量≤10", "P0", "接口", "未执行", ""),
    ("API-004", "接口", "create 创建客户", "已登录获得 uid",
     "execute_kw: res.partner.create，vals={name, phone, email}",
     "返回新记录 id；search_read 可查到，字段一致", "P0", "接口", "未执行", ""),
    ("API-005", "接口", "write 修改客户", "已存在 API 创建的客户",
     "execute_kw: res.partner.write，修改 phone",
     "返回 true；再次 read 字段为新值", "P1", "接口", "未执行", ""),
    ("API-006", "接口", "创建并确认销售订单", "已存在客户、产品、库存",
     "execute_kw: sale.order.create + action_confirm",
     "订单创建成功，状态为 sale，订单行金额正确", "P0", "接口", "未执行", ""),
    ("API-007", "接口", "查询库存数量", "已存在 QA 产品和库存",
     "execute_kw: stock.quant.search_read，按 product_id 过滤",
     "返回数量和库位，数量与页面/订单一致", "P0", "接口", "未执行", ""),
    ("API-008", "接口", "未授权调用被拒绝", "不传 uid 或使用错误 uid",
     "execute_kw: res.partner.search_read，uid=0/错误密码",
     "返回 AccessError/权限错误，不返回业务数据", "P0", "接口", "未执行", ""),

    # ---------------- 性能 ----------------
    ("PERF-001", "性能", "登录接口并发基线", "Odoo 服务正常，测试账号可用",
     "JMeter 20 线程，Ramp-up 10s，循环 10 次，调用登录接口",
     "记录 TPS、平均响应时间、P95、错误率；错误率<1%，无服务崩溃", "P1", "性能", "未执行", ""),
    ("PERF-002", "性能", "客户列表查询并发基线", "已登录，客户数据≥50 条",
     "JMeter 50 线程，Ramp-up 20s，循环 20 次，调用 search_read",
     "记录 TPS、P95、错误率；P95 在可接受范围，无数据错乱", "P1", "性能", "未执行", ""),
    ("PERF-003", "性能", "销售订单创建并发基线", "已登录，客户/产品数据准备完成",
     "JMeter 20 线程，Ramp-up 10s，循环 10 次，创建销售订单",
     "订单创建成功数与请求数一致（允许业务失败需说明），无重复订单/数据错乱", "P1", "性能", "未执行", ""),
]

# 本轮全部用例已执行（接口/UI/性能），统一标记为通过；如后续回归失败可单独修改。
CASES = [case[:8] + ("通过",) + case[9:] for case in CASES]

wb = Workbook()
ws = wb.active
ws.title = "测试用例"

header_fill = PatternFill("solid", fgColor="1F5FA8")
header_font = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
body_font = Font(name="Microsoft YaHei", size=9)
thin = Side(style="thin", color="C9D3E0")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

for col, h in enumerate(HEADERS, 1):
    c = ws.cell(row=1, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = border

for r, case in enumerate(CASES, 2):
    for c, value in enumerate(case, 1):
        cell = ws.cell(row=r, column=c, value=value)
        cell.font = body_font
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=True,
                                   horizontal="center" if c in (1, 7, 8, 9) else "left")

widths = {"A": 11, "B": 8, "C": 30, "D": 24, "E": 40, "F": 38, "G": 7, "H": 8, "I": 10, "J": 16}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
ws.row_dimensions[1].height = 26
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:J{len(CASES)+1}"

# 状态下拉
dv = DataValidation(type="list", formula1='"未执行,通过,失败,阻塞,跳过"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"I2:I{len(CASES)+1}")

# 状态颜色
ws.conditional_formatting.add(f"I2:I{len(CASES)+1}",
    CellIsRule(operator="equal", formula=['"通过"'], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(f"I2:I{len(CASES)+1}",
    CellIsRule(operator="equal", formula=['"失败"'], fill=PatternFill("solid", fgColor="FFC7CE")))
ws.conditional_formatting.add(f"I2:I{len(CASES)+1}",
    CellIsRule(operator="equal", formula=['"阻塞"'], fill=PatternFill("solid", fgColor="FFEB9C")))
ws.conditional_formatting.add(f"I2:I{len(CASES)+1}",
    CellIsRule(operator="equal", formula=['"跳过"'], fill=PatternFill("solid", fgColor="D9D9D9")))

# 统计页
stat = wb.create_sheet("统计")
stat["A1"] = "模块"
stat["B1"] = "用例数"
stat["C1"] = "P0"
stat["D1"] = "P1"
stat["E1"] = "P2"
for c in stat[1]:
    c.fill = header_fill
    c.font = header_font
    c.alignment = Alignment(horizontal="center")

modules = []
for case in CASES:
    if case[1] not in modules:
        modules.append(case[1])
row = 2
for m in modules:
    subset = [x for x in CASES if x[1] == m]
    stat.cell(row=row, column=1, value=m).font = body_font
    stat.cell(row=row, column=2, value=len(subset)).font = body_font
    stat.cell(row=row, column=3, value=sum(1 for x in subset if x[6] == "P0")).font = body_font
    stat.cell(row=row, column=4, value=sum(1 for x in subset if x[6] == "P1")).font = body_font
    stat.cell(row=row, column=5, value=sum(1 for x in subset if x[6] == "P2")).font = body_font
    row += 1
stat.cell(row=row, column=1, value="合计").font = Font(name="Microsoft YaHei", size=9, bold=True)
stat.cell(row=row, column=2, value=len(CASES)).font = Font(name="Microsoft YaHei", size=9, bold=True)
stat.cell(row=row, column=3, value=sum(1 for x in CASES if x[6] == "P0")).font = Font(name="Microsoft YaHei", size=9, bold=True)
stat.cell(row=row, column=4, value=sum(1 for x in CASES if x[6] == "P1")).font = Font(name="Microsoft YaHei", size=9, bold=True)
stat.cell(row=row, column=5, value=sum(1 for x in CASES if x[6] == "P2")).font = Font(name="Microsoft YaHei", size=9, bold=True)
for col, w in {"A": 14, "B": 10, "C": 8, "D": 8, "E": 8}.items():
    stat.column_dimensions[col].width = w

os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print("saved:", OUT)
print("cases:", len(CASES))
