#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_report.py - 生成 Skill 日报
用法: python daily_report.py [date: YYYY-MM-DD] [repo路径]
不传日期则默认今天，读取前自动 git pull 同步

需要在 repo 目录下有 .git（即 git 仓库）
"""

import sys
import os
import io
from datetime import datetime, date
import pandas as pd
from git_utils import git_pull

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_PATH = os.path.dirname(os.path.dirname(__file__))
LOG_PATH = os.path.join(REPO_PATH, "data", "skill_usage_log.xlsx")

CLAIM_SHEET = "领取记录"
UPDATE_SHEET = "更新记录"
STATS_SHEET = "统计汇总"


def generate_report(target_date: str = None, repo_path: str = REPO_PATH):
    log_path = LOG_PATH if repo_path == REPO_PATH else os.path.join(repo_path, "data", "skill_usage_log.xlsx")

    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    # 读取前先 pull 最新
    if os.path.exists(os.path.join(repo_path, ".git")):
        code, _, _ = git_pull(repo_path)

    if not os.path.exists(log_path):
        print(f"【Skill 日报 {target_date}】\n\n暂无任何使用记录，请先通过 record_usage.py 记录操作。")
        return

    sheets = pd.read_excel(log_path, sheet_name=None)
    claim_df = sheets.get(CLAIM_SHEET, pd.DataFrame())
    update_df = sheets.get(UPDATE_SHEET, pd.DataFrame())
    stats_df = sheets.get(STATS_SHEET, pd.DataFrame())

    def filter_today(df):
        if df.empty or "时间" not in df.columns:
            return df
        df = df.copy()
        df["时间"] = df["时间"].astype(str)
        return df[df["时间"].str.startswith(target_date)]

    today_claims = filter_today(claim_df)
    today_updates = filter_today(update_df)

    lines = []
    lines.append(f"📊 **Skill 日报 · {target_date}**")
    lines.append("=" * 36)

    lines.append(f"\n📥 **今日领取记录**（共 {len(today_claims)} 次）")
    if today_claims.empty:
        lines.append("  · 今日暂无领取记录")
    else:
        for _, row in today_claims.iterrows():
            lines.append(f"  · [{row['时间']}] {row['用户']} 领取了《{row['Skill名称']}》")

    lines.append(f"\n🔄 **今日更新记录**（共 {len(today_updates)} 次）")
    if today_updates.empty:
        lines.append("  · 今日暂无更新记录")
    else:
        for _, row in today_updates.iterrows():
            lines.append(f"  · [{row['时间']}] {row['用户']} 更新了《{row['Skill名称']}》：{row['更新说明']}")

    lines.append("\n🏆 **累计最热门 Skill（TOP 5）**")
    if stats_df.empty or "领取次数" not in stats_df.columns:
        lines.append("  · 暂无统计数据")
    else:
        top5 = stats_df.sort_values("领取次数", ascending=False).head(5)
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            lines.append(f"  {i}. 《{row['Skill名称']}》- 共被领取 {int(row['领取次数'])} 次（最近：{row['最后领取用户']}）")

    unique_users = today_claims["用户"].nunique() if not today_claims.empty else 0
    lines.append(f"\n📈 **今日数据摘要**")
    lines.append(f"  · 领取总次数：{len(today_claims)} 次")
    lines.append(f"  · 参与用户数：{unique_users} 人")
    lines.append(f"  · 更新操作数：{len(today_updates)} 次")

    lines.append("\n" + "=" * 36)
    lines.append("以上为自动生成日报，如有疑问请联系管理员。")

    report = "\n".join(lines)
    print(report)
    return report


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    repo = sys.argv[2] if len(sys.argv) > 2 else REPO_PATH
    generate_report(target_date, repo)
