---
name: skill-library
description: "Skill 图书馆管理系统。当用户提出以下需求时触发：查找/推荐/领取 skill、我需要一个能做XX的skill、有没有XX相关技能、记录skill使用/领取、skill日报、skill更新记录、skill被领取多少次、谁用了哪个skill、skill统计。"
description_zh: "Skill 图书馆：检索推荐、领取记录、更新记录、日报生成（支持 GitHub 跨用户同步）"
description_en: "Skill Library: search, claim tracking, update log, daily report (GitHub sync supported)"
version: 1.1.0
allowed-tools: Read,Write,Bash
---

# Skill 图书馆（Skill Library）

本 Skill 实现三大核心功能：
1. 从 GitHub 仓库的 Excel 目录中检索并推荐合适的 Skill（自动 git pull）
2. 记录用户领取 Skill 的操作，含次数统计（自动 git push 到 GitHub）
3. 记录 Skill 更新操作，并生成可发送的日报

**仓库地址**：`https://github.com/Yangyang0207/skill-library`  
**本地克隆路径**：`D:/skill-library`（用户需根据自己电脑调整）  
**数据文件**：`D:/skill-library/data/skill_list.xlsx`、`D:/skill-library/data/skill_usage_log.xlsx`

---

## 工作流

### 工作流 1：检索推荐 Skill

**触发场景**：用户表达了某种需求，想知道有没有合适的 Skill

**步骤**：
1. 从用户输入中提取关键词（1-3个）
2. 执行检索脚本（传入 repo 路径）：
   ```bash
   python {baseDirectory}/scripts/query_skills.py "<关键词>" "<repo路径>"
   ```
   例：`python scripts/query_skills.py "调研" "D:/skill-library"`
3. 脚本自动执行 `git pull`，确保读取最新数据
4. 解析返回的 JSON，将结果以表格形式呈现给用户
5. **询问用户是否要"领取"某个 Skill**

### 工作流 2：记录 Skill 领取

**触发场景**：用户确认领取某个 Skill

**步骤**：
1. 确认：skill 名称、用户姓名、repo 路径
2. 执行记录脚本：
   ```bash
   python {baseDirectory}/scripts/record_usage.py claim "<skill_name>" "<user_name>" "<repo路径>"
   ```
3. 脚本流程：`git pull` → 追加记录 → 保存 Excel → `git commit + push`
4. 告知用户记录成功及累计领取次数

### 工作流 3：记录 Skill 更新

**触发场景**：用户说"我更新了某个 skill"

**步骤**：
1. 确认：skill 名称、用户姓名、更新说明、repo 路径
2. 执行：
   ```bash
   python {baseDirectory}/scripts/record_usage.py update "<skill_name>" "<user_name>" "<update_desc>" "<repo路径>"
   ```
3. 同样自动 git pull → 保存 → git push

### 工作流 4：生成日报

**触发场景**：用户说"生成日报"、"今天的 skill 报告"

**步骤**：
1. 确认目标日期（默认今天）和 repo 路径
2. 执行：
   ```bash
   python {baseDirectory}/scripts/daily_report.py "<YYYY-MM-DD>" "<repo路径>"
   ```
3. 脚本自动 `git pull` 拉取最新日志，汇总后输出可直接发送的日报

---

## GitHub 同步机制

| 操作 | 自动行为 |
|------|---------|
| 检索（query） | 自动 `git pull` 拉最新 |
| 领取（claim） | 自动 `git pull → 保存 → git push` |
| 更新（update） | 自动 `git pull → 保存 → git push` |
| 日报（report） | 自动 `git pull` 拉最新 |

> 多用户使用：每人 clone 仓库到本地后，每次操作会自动同步，日报会汇总所有人的记录。

---

## 首次安装配置

1. **克隆仓库到本地**：
   ```bash
   git clone https://github.com/Yangyang0207/skill-library.git D:/skill-library
   ```

2. **安装依赖**：
   ```bash
   pip install pandas openpyxl
   ```

3. **首次使用**：告知 AI 你的本地 repo 路径（脚本支持传入自定义 repo 路径）

---

## 数据文件说明

| 文件 | 用途 |
|------|------|
| `data/skill_list.xlsx` | Skill 目录（可导出统一平台 Excel 替换） |
| `data/skill_usage_log.xlsx` | 使用日志，含"领取记录"/"更新记录"/"统计汇总"三个 Sheet |
