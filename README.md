# CRM/ERP 测试实战：Flask + SQLite 测试靶场

一个可运行的轻量级 **CRM/ERP 系统** + 一套完整测试体系：功能用例、接口测试、UI 自动化、性能压测、缺陷分析与测试报告。

> 被测系统：自建 CRM/ERP 测试靶场（Flask + SQLite）
> 访问地址：http://127.0.0.1:5000
> 测试账号：`admin / admin123`

---

## 1. 项目背景

很多测试简历上的“CRM/ERP 项目”只有截图和描述，面试官一问业务链路、数据校验、并发问题就露馅。这个项目用开源技术栈（Flask + SQLite + Jinja2）搭了一个**可运行、可造数、可复现缺陷**的 CRM/ERP 测试靶场，然后针对它完成一整套测试：

- 从需求拆分、测试计划、用例设计到执行报告；
- 接口测试覆盖登录、客户 CRUD、销售订单、采购收货、库存、发票、权限与多租户隔离；
- UI 自动化覆盖 CRM/ERP 核心流程，POM 分层 + 显式等待 + 失败截图 + Allure 报告；
- 性能测试覆盖登录、客户查询、客户创建、销售订单创建；
- 在测试过程中发现并修复并发超卖、跨租户负责人引用、重复收货/开票、负库存等问题。

## 2. 系统功能

| 模块 | 功能 |
|---|---|
| CRM | 客户建档/搜索/编辑/归档、负责人分配、线索创建与转化、商机管道与阶段推进、合同管理 |
| ERP | 产品、供应商、采购订单（创建/确认/收货）、销售订单（创建/确认/发货）、库存调整与流水、发票开具 |
| SaaS | 多租户、用户与角色（管理员/销售/仓管/财务）、角色权限矩阵、租户数据隔离 |
| API | REST API + Session 登录，供 Postman/Newman、pytest、JMeter 调用 |

系统内置两套租户数据（启明科技 / 远航集团）和演示数据，便于验证多租户隔离与权限边界。

## 3. 技术栈

- **被测系统**：Python 3.15、Flask 3、SQLite、Jinja2
- **接口测试**：Postman / Newman、Python requests + pytest
- **UI 自动化**：Selenium 4、Pytest、Allure、POM
- **性能测试**：Apache JMeter 5.6.3
- **测试文档**：Markdown、Excel（openpyxl）
- **版本管理**：Git

## 4. 测试结果

| 类型 | 规模 | 结果 | 报告 |
|---|---:|---|---|
| 功能/接口用例 | 44 条 | 44 通过，0 失败，通过率 100% | `docs/02-test-cases.xlsx` |
| 接口自动化（pytest） | 20 个测试 | 20 通过 | `reports/api/report.html` |
| 接口自动化（Newman） | 27 个请求 / 46 个断言 | 46 断言全部通过 | `reports/api/newman-report.html` |
| UI 自动化（Selenium） | 14 个测试 | 14 通过 | `reports/ui/allure-report/index.html` |
| 性能-混合场景 | 600 请求，20 线程 | 0 错误，55.3 req/s | `reports/perf/html/index.html` |
| 性能-销售订单创建 | 200 请求，10 线程 | 0 错误，34.3 req/s | `reports/perf/sales-html/index.html` |

**关键性能数据（本地单机基线）：**

| 场景 | 平均响应 | P95 | 错误率 |
|---|---:|---:|---:|
| 登录（混合场景） | 147 ms | 168 ms | 0% |
| 客户查询（混合场景） | 4–7 ms | 6–14 ms | 0% |
| 客户创建（混合场景） | 7.6 ms | 15 ms | 0% |
| 销售订单创建 | 5 ms | 8 ms | 0% |

> 登录耗时主要来自密码哈希校验；这是安全与性能的典型权衡点，也是面试可展开的分析点。

## 5. 缺陷分析

测试过程中共记录 6 个问题，其中 4 个已修复并通过回归，2 个为已知限制：

| 编号 | 问题 | 级别 | 状态 |
|---|---|---|---|
| DEF-001 | 客户更新接口未校验负责人是否属于当前租户，存在跨租户引用风险 | 中 | 已修复 |
| DEF-002 | 并发发货时先查库存再扣减，存在超卖/负库存风险 | 中 | 已修复 |
| DEF-003 | 产品创建允许负价格/负库存 | 低 | 已修复 |
| DEF-004 | 重复收货、重复开票缺少幂等控制 | 低 | 已修复 |
| DEF-005 | 表单缺少 CSRF Token | 低 | 已知限制 |
| DEF-006 | 登录无失败次数限制/验证码 | 低 | 已知限制 |

详见 `docs/03-defect-report.md`。

## 6. 目录结构

```
crm-erp-testing/
├── app/                         # 被测系统（Flask + SQLite）
│   ├── __init__.py              # 应用工厂、登录、仪表盘
│   ├── api.py                   # REST API
│   ├── crm.py                   # 客户/线索/商机/合同
│   ├── erp.py                   # 产品/供应商/采购/销售/库存/发票
│   ├── saas.py                  # 租户/用户/角色
│   ├── services.py              # 业务服务层（Web 与 API 共用）
│   ├── schema.sql               # 数据库结构
│   ├── seed.py                  # 测试数据
│   ├── templates/               # Jinja2 页面
│   └── static/                  # CSS / JS
├── api/                         # 接口测试
│   ├── test_api.py              # pytest 接口用例（requests 直连）
│   ├── postman_collection.json
│   └── postman_environment.json
├── ui/                          # UI 自动化
│   ├── conftest.py
│   ├── pages/                   # POM 页面对象
│   └── tests/                   # pytest UI 用例
├── perf/                        # JMeter 脚本与数据
├── docs/                        # 测试计划、用例、缺陷、报告、面试笔记
├── reports/                     # 执行报告
├── screenshots/                 # 系统截图
└── scripts/                     # 辅助脚本
```

## 7. 快速开始

```bash
# 1. 安装依赖
python -m pip install -r requirements.txt

# 2. 初始化测试数据（会重建 SQLite 表）
python -m app.seed

# 3. 启动系统
python run.py
# 浏览器访问 http://127.0.0.1:5000
```

测试账号：

| 账号 | 密码 | 角色 | 租户 |
|---|---|---|---|
| admin | admin123 | 管理员 | 启明科技 |
| sales01 | sales123 | 销售 | 启明科技 |
| warehouse01 | warehouse123 | 仓管 | 启明科技 |
| finance01 | finance123 | 财务 | 启明科技 |
| admin_b | admin123 | 管理员 | 远航集团 |

## 8. 执行测试

### 8.1 接口测试

```bash
python -m pytest api/test_api.py -v \
  --html=reports/api/report.html --self-contained-html

newman run api/postman_collection.json -e api/postman_environment.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export reports/api/newman-report.html
```

### 8.2 UI 自动化

```bash
python -m pytest ui/tests -v --alluredir=reports/ui/allure-results
allure generate reports/ui/allure-results -o reports/ui/allure-report --clean
```

### 8.3 性能测试

```bash
jmeter -n -t perf/crm_erp_load_test.jmx \
  -l reports/perf/result.jtl -e -o reports/perf/html

jmeter -n -t perf/sales_order_load_test.jmx \
  -l reports/perf/sales-result.jtl -e -o reports/perf/sales-html
```

## 9. 项目亮点

1. **不是“只写用例”**：自己搭系统、造数据、设计 API/UI/性能测试，能完整讲清业务链路。
2. **发现了真实并发缺陷**：8 个订单并发发货、库存只有 5，原实现可能超卖；通过条件状态迁移 + 原子扣减 + WAL/busy_timeout 修复，并用并发测试回归。
3. **权限与多租户**：角色菜单隔离、API 403、租户数据 404，覆盖越权访问的典型场景。
4. **自动化框架**：POM 分层、pytest fixture、显式等待、失败截图、Allure 报告，脚本可维护。
5. **性能有数据**：登录、查询、创建三类场景的 TPS/P95/错误率，能解释瓶颈来源（密码哈希、SQLite 单机写锁）。

## 10. 系统截图 & 测试报告说明
本项目基于真实的 SaaS 架构 CRM/ERP 系统（包含多租户隔离、权限矩阵、订单流转及库存扣减等复杂业务逻辑）进行了全面的功能、接口与自动化测试。

### 自动化与性能测试报告
**1. UI 自动化测试报告 (Allure)**
基于 Python + Selenium + Pytest + POM 框架执行，14 个核心用例 100% 全部通过。
<img width="1416" height="861" alt="11-users" src="https://github.com/user-attachments/assets/5141526b-90af-4cfe-9579-b12e0972abd4" />
**2. 接口并发性能压测报告 (JMeter)**
针对核心销售订单与客户查询接口进行 200 并发压测，错误率 0%，TPS 与响应时间表现优异。
<img width="1416" height="861" alt="12-roles" src="https://github.com/user-attachments/assets/1ac58e90-15f8-4cee-8769-f8782bba0e55" />

### 💻 核心业务系统界面展示
**1. 系统登录与数据仪表盘**
支持多角色登录，仪表盘直观展示核心商业指标。
<img width="1416" height="861" alt="13-allure-report" src="https://github.com/user-attachments/assets/b6c541b8-f91e-4487-bdf1-33b88e3ff45c" />
<img width="1416" height="861" alt="14-jmeter-report" src="https://github.com/user-attachments/assets/cd23a80a-624c-4364-8dfb-40e26aef3dfa" />

**2. ERP 核心业务与库存管理**
验证了订单流转、发货以及低库存预警等核心 ERP 数据一致性场景。
<img width="1416" height="861" alt="04-products" src="https://github.com/user-attachments/assets/5ce2d067-73ef-45b6-ac9a-abdd3e403756" />

**3. SaaS 核心架构：多角色权限矩阵**
验证了基于 RBAC 的权限控制，确保不同角色（销售、仓管、财务）的数据隔离与越权防护。
<img width="1416" height="861" alt="10-users" src="https://github.com/user-attachments/assets/17249246-b407-4a8b-ada7-490bf28ddcaa" />

*(注：完整测试计划、测试用例、缺陷报告均在 `docs/` 目录下；自动化与压测底层脚本见 `ui/`、`api/` 和 `perf/` 目录)*

## 11. 已知限制

- 本项目是测试练习靶场，不是生产系统；SQLite + Flask 开发服务器不适合生产。
- 表单未实现 CSRF Token，登录未做失败次数限制；生产环境需补充。
- 性能数据为本地单机基线，不代表生产容量。
- 测试数据统一使用 `QA-` / `PERF-` 前缀；重新执行 `python -m app.seed` 可恢复演示数据。

## 12. 相关文档

- 测试计划：`docs/01-test-plan.md`
- 测试用例：`docs/02-test-cases.xlsx`（44 条）
- 缺陷报告：`docs/03-defect-report.md`
- 测试总结：`docs/04-test-report.md`
- 面试讲解：`docs/05-interview-notes.md`
