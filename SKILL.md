---
name: skill-library
description: "Skill 图书馆管理系统。当用户提出以下需求时触发：查找/推荐/领取/安装/发给我 skill、我需要一个能做XX的skill、有没有XX相关技能、记录skill使用/领取、skill日报、skill更新记录、skill被领取多少次、谁用了哪个skill、skill统计。"
description_zh: "Skill 图书馆：检索推荐、自动领取记录、更新记录、日报生成（支持飞书多维表格云存储）"
description_en: "Skill Library: search, auto claim tracking, update log, daily report (Feishu Bitable cloud storage)"
version: 1.3.0
allowed-tools: Read,Write,Bash
---

# Skill 图书馆（Skill Library）

本 Skill 实现三大核心功能：
1. 从飞书多维表格（云端）/ Excel（本地）检索并推荐合适的 Skill
2. 记录用户领取 Skill 的操作，含次数统计
3. 记录 Skill 更新操作，并生成可发送的日报

**飞书多维表格**（优先）：实时云端同步，多人同时使用无冲突  
**GitHub + Excel**（备用）：无飞书配置时自动回退

---

## 飞书多维表格配置

> 由管理员首次初始化，所有用户共享同一个表格，无需各自配置

**表格地址**：`https://zcn07z6w5bmf.feishu.cn/base/HVsrbotCHaUEzcs3xbFc4SlPnDb`

| 数据表 | 用途 |
|--------|------|
| Skill目录 | Skill 清单，含名称/序号 |
| 领取记录 | 记录谁在什么时间领取了哪个 Skill |
| 更新记录 | 记录谁在什么时间更新了哪个 Skill |

**配置文件**（自动生成）：`scripts/feishu_config.py`  
**初始化脚本**：`scripts/feishu_bitable_init.py`（管理员使用，普通用户无需运行）

---

## 工作流

### 工作流 1：检索推荐 Skill

**触发场景**：用户表达了某种需求，想知道有没有合适的 Skill

**步骤**：
1. 从用户输入中提取关键词（1-3个）
2. 执行检索脚本（auto 模式自动优先飞书）：
   ```bash
   python {baseDirectory}/scripts/query_skills.py "<关键词>" [feishu|excel|auto]
   ```
   例：`python scripts/query_skills.py "调研"`
3. 解析返回的 JSON，将结果以表格形式呈现给用户
4. **如用户随后表达了"领取/安装/发给我"的意图，直接进入工作流 2**

### 工作流 2：记录 Skill 领取

**触发场景**：用户表达"领取/安装/发给我"某个 Skill 的意图

**步骤**：
1. 从用户输入中解析出目标 Skill 名称
2. **获取用户姓名**：
   - 优先从飞书多维表格读取历史记录判断是否首次
   - **无记录（首次）** → **必须询问用户姓名**
3. 执行记录脚本（auto 模式自动用飞书）：
   ```bash
   python {baseDirectory}/scripts/record_usage.py claim "<skill_name>" "<user_name>" [feishu|excel|auto]
   ```
4. 数据写入飞书多维表格（多人实时同步）
5. 告知用户记录成功及累计领取次数

### 工作流 3：记录 Skill 更新

**触发场景**：用户说"我更新了某个 skill"

**步骤**：
1. 确认：skill 名称、用户姓名、更新说明
2. 执行：
   ```bash
   python {baseDirectory}/scripts/record_usage.py update "<skill_name>" "<user_name>" "<update_desc>" [feishu|excel|auto]
   ```

### 工作流 4：生成日报

**触发场景**：用户说"生成日报"、"今天的 skill 报告"

**步骤**：
1. 确认目标日期（默认今天）
2. 执行：
   ```bash
   python {baseDirectory}/scripts/daily_report.py [YYYY-MM-DD] [feishu|excel|auto]
   ```
3. 从飞书多维表格实时读取数据，输出可直接发送的日报

---

## 数据源切换

| 模式 | 说明 |
|------|------|
| `feishu`（推荐） | 读写飞书多维表格，云端实时同步 |
| `excel` | 读写本地 Excel + GitHub 同步 |
| `auto`（默认） | 优先飞书，飞书不可用时自动回退 Excel |

脚本会自动检测配置，无需手动指定。

---

## 首次安装配置

1. **克隆仓库**：
   ```bash
   git clone https://github.com/Yangyang0207/skill-library.git D:/skill-library
   ```

2. **安装依赖**：
   ```bash
   pip install pandas openpyxl
   ```

3. **配置飞书（可选，默认 auto 模式已自动处理）**：
   - 飞书配置由管理员在 `scripts/feishu_config.py` 中维护
   - 普通用户克隆后直接使用，无需额外配置

---

## 脚本说明

| 脚本 | 功能 | 数据源 |
|------|------|--------|
| `query_skills.py` | 检索推荐 Skill | 飞书 / Excel |
| `record_usage.py` | 记录领取/更新 | 飞书 / Excel |
| `daily_report.py` | 生成日报 | 飞书 / Excel |
| `feishu_client.py` | 飞书 API 统一客户端 | - |
| `feishu_config.py` | 飞书配置（自动生成） | - |
| `feishu_bitable_init.py` | 初始化飞书多维表格 | 飞书 API |
| `git_utils.py` | Git 操作工具（Excel 模式用） | - |
