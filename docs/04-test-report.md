# 测试总结报告

> 项目：CRM/ERP 测试靶场（Flask + SQLite）
> 测试周期：2026-10
> 测试环境：Windows 10 / Python 3.15 / Flask 3 / SQLite / Edge / JMeter 5.6.3

## 1. 执行概况

| 指标 | 结果 |
|---|---:|
| 测试用例设计数 | 44 |
| 已执行用例 | 44 |
| 通过 | 44 |
| 失败 | 0 |
| 阻塞 | 0 |
| 用例通过率 | 100% |
| 接口自动化测试 | 20 个 pytest 测试，全部通过 |
| Postman/Newman | 27 个请求 / 46 个断言，全部通过 |
| UI 自动化测试 | 14 个测试，全部通过 |
| 性能场景 | 2 个场景，共 800 个请求，错误率 0% |
| 缺陷数 | 6（已修复 4，已知限制 2） |

## 2. 测试范围与覆盖

### 2.1 CRM

- 客户创建、必填校验、搜索、编辑、负责人分配、归档；
- 线索创建与线索转商机；
- 商机创建、金额/日期保存、阶段推进；
- 商机管道 6 个阶段展示；
- 合同创建（页面）。

**覆盖方式：** UI 自动化 5 条 + 接口测试 7 条 + 手工用例。

### 2.2 ERP

- 产品创建、价格/成本修改、负值校验；
- 供应商创建；
- 采购订单创建、确认、收货、取消；
- 销售订单创建、确认、发货、取消；
- 库存增加/扣减/调整与流水；
- 发票开具、金额校验、重复开票拦截；
- 库存不足拦截。

**覆盖方式：** UI 自动化 5 条 + 接口测试 10 条 + 性能测试 2 个场景。

### 2.3 权限与多租户

- 未登录访问重定向登录页；
- 错误密码登录失败；
- 销售角色看不到 SaaS 管理菜单，直接访问返回 403；
- 销售角色不能创建产品/采购订单；
- 租户 B 无法读取租户 A 的客户（404）；
- 管理员切换租户后数据隔离。

**覆盖方式：** UI 自动化 3 条 + 接口测试 4 条 + Newman 3 条。

## 3. 接口测试结果

### 3.1 pytest（20 个测试）

| 测试类 | 覆盖点 | 结果 |
|---|---|---|
| 基础/登录 | health、登录成功、错误密码、未登录 401、仪表盘 | 通过 |
| 客户 | CRUD、必填校验、跨租户负责人校验 | 通过 |
| 产品 | 创建、负库存/负价格校验、重复 SKU | 通过 |
| 销售订单 | 创建、确认、发货、库存扣减、库存不足、取消、并发发货 | 通过 |
| 采购订单 | 创建、确认、收货、库存增加、重复收货、取消 | 通过 |
| 发票 | 发货后开票、金额一致、重复开票拦截 | 通过 |
| 库存 | 入库/出库调整、超量出库拦截 | 通过 |
| 权限/租户 | 角色 403、租户数据 404/隔离 | 通过 |
| 线索 | 创建、转化、重复转化拦截 | 通过 |

**报告：** `reports/api/report.html`

### 3.2 Postman/Newman

- 27 个请求，46 个断言，0 失败；
- 覆盖登录、客户、产品、销售订单、采购订单、库存、发票、租户隔离；
- 报告：`reports/api/newman-report.html`。

## 4. UI 自动化结果

| 用例 | 覆盖点 | 结果 |
|---|---|---|
| 登录成功 | 管理员登录进入仪表盘 | 通过 |
| 错误密码 | 登录失败提示 | 通过 |
| 未登录拦截 | 访问 CRM 重定向登录 | 通过 |
| 客户创建/搜索 | 新建客户并搜索 | 通过 |
| 客户必填校验 | 名称必填 | 通过 |
| 客户负责人 | 编辑负责人 | 通过 |
| 商机创建/阶段 | 新建商机、阶段推进 | 通过 |
| 商机管道 | 6 个阶段与卡片展示 | 通过 |
| 销售订单 | 创建-确认-发货-开票-库存扣减 | 通过 |
| 供应商/产品 | 新建供应商、修改售价 | 通过 |
| 采购订单 | 创建-确认-收货-库存增加 | 通过 |
| 库存调整 | 入库/出库/超量拦截 | 通过 |
| 销售权限 | SaaS 菜单隐藏、403 | 通过 |
| 租户切换 | 切换到远航集团并切回 | 通过 |

**框架：** POM 页面对象、pytest fixture、显式等待、失败截图、Allure 报告。
**报告：** `reports/ui/allure-report/index.html`

## 5. 性能测试结果

### 5.1 混合场景（登录 + 客户查询 + 客户创建）

- 线程：20；Ramp-up：10s；循环：10 次；
- 总请求：600；错误率：0%；
- 测试时长：10.85s；吞吐量：55.3 req/s。

| 请求 | 次数 | 平均(ms) | P95(ms) | 最大(ms) |
|---|---:|---:|---:|---:|
| POST /api/login | 200 | 147.3 | 168.0 | 195 |
| GET /api/customers?q=... | 200 | 4.2–7.2 | 6–14 | 18 |
| POST /api/customers | 200 | 7.6 | 15.0 | 227 |

**分析：**
- 登录是主要耗时点，平均 147ms，主要成本是密码哈希（Werkzeug scrypt/pbkdf2）校验；这是安全与性能的权衡。
- 客户查询和创建在本地 SQLite 下都是毫秒级，P95 低于 15ms。
- 写请求最大 227ms，可能与 SQLite 写锁/检查点有关；已开启 WAL + busy_timeout，错误率为 0。

### 5.2 销售订单创建场景

- 线程：10；Ramp-up：5s；循环：10 次；
- 总请求：200；错误率：0%；
- 测试时长：5.83s；吞吐量：34.3 req/s。

| 请求 | 次数 | 平均(ms) | P95(ms) | 最大(ms) |
|---|---:|---:|---:|---:|
| POST /api/login | 100 | 141.7 | 161.0 | 169 |
| POST /api/sales-orders | 100 | 5.0 | 8.0 | 11 |

**分析：**
- 订单创建本身很快（P95 8ms），瓶颈仍在登录；
- 若生产环境使用长连接/Token 复用，可显著降低每请求的登录开销；
- 建议：引入 Token/会话复用、Gunicorn 多 worker、连接池、缓存，并补充更大并发梯度（50/100/200）与数据库监控。

**报告：** `reports/perf/html/index.html`、`reports/perf/sales-html/index.html`

## 6. 缺陷统计

| 级别 | 数量 | 已修复 | 已知限制 |
|---|---:|---:|---:|
| P1 | 2 | 2 | 0 |
| P2 | 2 | 2 | 0 |
| P3 | 2 | 0 | 2 |
| 合计 | 6 | 4 | 2 |

详细复现步骤、根因与修复见 `docs/03-defect-report.md`。

## 7. 风险与限制

- **SQLite + Flask 开发服务器**：适合本地测试靶场，不代表生产架构；生产需 MySQL/PostgreSQL + Gunicorn/uWSGI + Nginx。
- **性能基线**：本地单机数据，受 CPU、磁盘、浏览器/进程影响；不能直接作为生产容量结论。
- **安全范围**：仅覆盖基础权限与租户隔离；CSRF、登录限流、密码策略、审计日志未实现/未测试。
- **数据权限**：当前销售角色可查看本租户全部 CRM 数据（小团队模型）；如要求“只看自己的客户”，需增加数据范围（owner-based data scope）。
- **测试数据**：自动化会创建 `QA-`/`PERF-` 前缀数据；执行 `python -m app.seed` 可恢复演示数据。

## 8. 结论

- 44 条用例全部执行通过，核心业务链路（客户→商机→销售订单→发货→发票；采购→收货→库存）验证完成；
- 接口、UI、性能三类自动化全部落地，报告可复现；
- 在测试过程中发现并修复了并发超卖、跨租户负责人引用、重复收货/开票、负库存等 4 个有价值的缺陷；
- 项目具备可讲、可演示、可追问的完整测试闭环，适合作为软件测试/测试开发岗位的实战项目。

## 9. 复现方式

```bash
python -m pip install -r requirements.txt
python -m app.seed
python run.py

# 接口
python -m pytest api/test_api.py -v --html=reports/api/report.html --self-contained-html
newman run api/postman_collection.json -e api/postman_environment.json --reporters cli,htmlextra --reporter-htmlextra-export reports/api/newman-report.html

# UI
python -m pytest ui/tests -v --alluredir=reports/ui/allure-results
allure generate reports/ui/allure-results -o reports/ui/allure-report --clean

# 性能
jmeter -n -t perf/crm_erp_load_test.jmx -l reports/perf/result.jtl -e -o reports/perf/html
jmeter -n -t perf/sales_order_load_test.jmx -l reports/perf/sales-result.jtl -e -o reports/perf/sales-html
```
