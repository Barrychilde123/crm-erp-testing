# 把 CRM/ERP 测试项目上传到 GitHub

> 说明：CRM 和 ERP 两个项目在同一个仓库 `crm-erp-testing` 里（README 同时介绍 CRM / ERP / SaaS）。**上传一次就够了**，不需要拆成两个仓库；一个仓库反而更方便面试官一次看完。
>
> 本机项目位置：`C:\Users\Administrator\Desktop\工作\测试项目\crm-erp-testing`
> 当前状态：已有本地 Git 提交，分支是 `master`，还没有远程仓库。

---

## 方案一：GitHub Desktop（最简单，推荐新手）

1. 打开 https://github.com ，注册/登录账号。
   - 用户名建议用职业化的名字，例如 `zhouyueming-qa`，会出现在仓库链接里。
2. 下载 GitHub Desktop：https://desktop.github.com/ ，安装并登录。
3. 打开 GitHub Desktop → `File` → `Add local repository`。
4. 选择文件夹：`C:\Users\Administrator\Desktop\工作\测试项目\crm-erp-testing`。
5. 如果提示这不是 Git 仓库，点 `create a repository` 也可以；正常情况会直接识别。
6. 点击右上角 `Publish repository`：
   - Name：`crm-erp-testing`
   - Description：`CRM/ERP 测试实战：Flask + SQLite + Selenium + Pytest + Allure + JMeter`
   - 想给面试官看就**取消勾选** `Keep this code private`（公开）
   - 点 `Publish repository`
7. 打开 `https://github.com/你的用户名/crm-erp-testing`，能看到代码和 README 就成功了。

> 公开前确认：仓库里没有你的手机号、身份证、成绩单等隐私文件。当前仓库只有代码、测试数据、报告和截图，没有简历文件。

---

## 方案二：命令行（已安装 Git，适合想学 Git 的人）

### 第 1 步：在 GitHub 创建空仓库

1. 打开 https://github.com/new
2. Repository name：`crm-erp-testing`
3. Description 可填：`CRM/ERP 测试实战`
4. 选择 `Public`（求职展示建议公开）
5. **不要勾选** `Add a README file`、`Add .gitignore`、`Choose a license`
   - 因为本地已经有 README 和 .gitignore，勾选会造成冲突。
6. 点 `Create repository`。

### 第 2 步：配置 Git 身份

在项目文件夹打开终端（地址栏输入 `cmd` 回车，或在 Git Bash 里进入目录）：

```bash
cd C:\Users\Administrator\Desktop\工作\测试项目\crm-erp-testing

git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
```

> 重要：GitHub 只会把“邮箱已添加到账号”的提交关联到你的头像。  
> 去 GitHub → Settings → Emails，把你的邮箱添加并验证；或者使用 GitHub 提供的 noreply 邮箱。

### 第 3 步：关联远程仓库并推送

把下面命令里的 `<你的用户名>` 换成你的 GitHub 用户名：

```bash
git remote add origin https://github.com/<你的用户名>/crm-erp-testing.git
git branch -M main
git push -u origin main
```

### 第 4 步：输入账号密码

- GitHub 现在**不接受账号密码**，密码处要填 **Personal Access Token（PAT）**。
- 生成方式：
  1. GitHub 右上角头像 → `Settings`
  2. 左侧最下方 `Developer settings`
  3. `Personal access tokens` → `Tokens (classic)`
  4. `Generate new token (classic)`
  5. Note 填 `crm-erp-testing`，Expiration 选 30 天或 90 天
  6. 勾选 `repo` 权限
  7. `Generate token`，复制生成的 token（只显示一次）
- 执行 `git push` 时：
  - Username：你的 GitHub 用户名
  - Password：粘贴刚才的 token（不是账号密码）
- 也可以使用 Git Credential Manager：push 时可能自动弹出浏览器登录，按提示授权即可。

> **不要把 token 发给任何人，也不要粘贴到聊天里。** 如果泄露，立即去 GitHub 删除/重新生成。

### 第 5 步：检查

打开 `https://github.com/<你的用户名>/crm-erp-testing`：

- 能看到 `README.md`、`app/`、`api/`、`ui/`、`perf/`、`reports/`、`screenshots/`；
- README 里的截图能正常显示；
- 点 `reports/ui/allure-report/index.html` 等文件，GitHub 不能直接运行 HTML，但可以下载后用浏览器打开；面试时本地演示即可。

---

## 常见问题

### 1. `remote origin already exists`

说明已经配置过远程仓库，改地址即可：

```bash
git remote set-url origin https://github.com/<你的用户名>/crm-erp-testing.git
```

### 2. `Authentication failed` / `Support for password authentication was removed`

- 密码处必须用 PAT，不是 GitHub 登录密码；
- 或者用 GitHub Desktop 登录后发布，最省事。

### 3. `src refspec main does not match any`

先确认有提交、分支已改名：

```bash
git log --oneline
git branch -M main
git push -u origin main
```

### 4. `failed to push some refs` / `fetch first`

通常是因为创建仓库时勾选了 README。两种处理：

```bash
# 保留本地内容，把远程的 README 拉到本地再推送
git pull --rebase origin main
git push -u origin main
```

或者删掉 GitHub 上的空仓库，重新创建一个**不勾选任何初始化文件**的仓库。

### 5. 提示 CRLF / LF

Windows 换行符警告，不影响上传，可以忽略。

### 6. 仓库太大 / 超过 100MB

当前项目约 23MB，没有单个大文件，正常不会触发。不要上传 `instance/` 数据库和 `*.jtl` 原始压测结果，`.gitignore` 已经排除。

---

## 上传后建议

1. 把仓库链接加到简历顶部，例如：
   `GitHub：github.com/你的用户名/crm-erp-testing`
2. 把仓库链接发给我，我可以帮你检查 README、截图和报告是否能正常显示，并帮你把链接加到简历里。
3. 面试时提前在本地启动项目：
   ```bash
   cd C:\Users\Administrator\Desktop\工作\测试项目\crm-erp-testing
   python -m app.seed
   python run.py
   ```
   然后打开 `http://127.0.0.1:5000` 演示。

---

## 如果你不想自己敲命令

可以先在 GitHub 创建空仓库，然后把仓库地址发给我（**不要发 token**）。我可以帮你：

```bash
git remote add origin <你的仓库地址>
git branch -M main
```

最后一步 `git push -u origin main` 建议你在自己的终端执行，这样浏览器登录/输入 token 的提示会出现在你这边；在 Claude Code 里可以输入：

```
! git push -u origin main
```

执行完把输出发给我，我帮你看是否成功。
