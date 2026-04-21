# Skill Library - Skill 图书馆

一个用于团队内部管理、检索和追踪 Skill 使用情况的 WorkBuddy Skill，支持 **GitHub 跨用户数据同步**。

## 功能

| 功能 | 说明 |
|------|------|
| 🔍 检索推荐 | 根据需求从 Excel 模糊匹配推荐 Skill，自动 git pull 最新数据 |
| 📥 领取记录 | 记录谁领取了哪个 Skill，自动 git push 到 GitHub |
| 🔄 更新记录 | 记录 Skill 更新操作，自动同步到 GitHub |
| 📊 日报生成 | 汇总所有用户的领取/更新记录，生成可直接发送的日报 |

## GitHub 同步机制

```
阳阳的电脑  ──push──▶  GitHub 仓库
                              ▲
                              │
马静的电脑  ──push─── pull ────┘
```

每次操作脚本自动：
- **读取前** → `git pull`（拉取他人最新记录）
- **写入后** → `git commit + push`（推送自己的记录）

## 目录结构

```
skill-library/
├── SKILL.md                  # AI 工作流说明
├── README.md                 # 本文档
├── scripts/
│   ├── query_skills.py       # 检索脚本（自动 git pull）
│   ├── record_usage.py       # 领取/更新记录（自动 git push）
│   ├── daily_report.py       # 日报生成（自动 git pull）
│   └── git_utils.py          # Git 同步工具
└── data/
    ├── skill_list.xlsx       # Skill 目录
    └── skill_usage_log.xlsx  # 使用日志（三人 Sheet）
```

## 首次安装

### 1. 克隆仓库

```bash
git clone https://github.com/Yangyang0207/skill-library.git D:/skill-library
```

> 每台电脑 clone 一次，clone 到哪里，repo 路径就填哪里

### 2. 安装 Python 依赖

```bash
pip install pandas openpyxl
```

### 3. 告诉 AI 你的 repo 路径

首次使用时告诉 AI："我的 repo 克隆到了 D:/skill-library"，AI 会自动用该路径执行所有脚本。

## 脚本使用

```bash
# 检索 Skill（自动 git pull）
python scripts/query_skills.py "调研" "D:/skill-library"

# 记录领取（自动 git push）
python scripts/record_usage.py claim "马静-调研问卷生成" "阳阳" "D:/skill-library"

# 记录更新（自动 git push）
python scripts/record_usage.py update "马静-表格拆分与合并工具" "马静" "新增批量合并功能" "D:/skill-library"

# 生成日报（自动 git pull，汇总所有用户数据）
python scripts/daily_report.py "2026-04-21" "D:/skill-library"
```

## 数据文件说明

### skill_list.xlsx（Skill 目录）
可直接替换为团队统一平台导出的 Excel，格式要求：
- 至少包含一列含"skill"或"名称"的列
- 可包含多列（描述、作者、版本等），均会在检索结果中展示

### skill_usage_log.xlsx（使用日志）
三个 Sheet：

**领取记录**：时间、用户、Skill名称、操作

**更新记录**：时间、用户、Skill名称、更新说明

**统计汇总**：Skill名称、领取次数、最后领取时间、最后领取用户
