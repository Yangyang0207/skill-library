#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_report.py - 生成 Skill 日报
用法: python daily_report.py [date: YYYY-MM-DD] [数据源模式]

数据源: feishu（优先）| excel（备用，需 Git 同步）
不传日期则默认今天
"""

import sys
import os
import io
from datetime import date
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_PATH = os.path.dirname(os.path.dirname(__file__))


def generate_feishu_report(target_date: str):
    """从飞书多维表格生成日报"""
    from feishu_client import FeishuClient
    from feishu_config import (APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                               TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                          TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    claims = client.get_claim_records(target_date)
    updates = client.get_update_records(target_date)

    lines = []
    lines.append(f"📊 **Skill 日报 · {target_date}**")
    lines.append("=" * 36)

    lines.append(f"\n📥 **今日领取记录**（共 {len(claims)} 次）")
    if not claims:
        lines.append("  · 今日暂无领取记录")
    else:
        for r in claims:
            lines.append(f"  · [{r['时间']}] {r['用户']} 领取了《{r['Skill名称']}》")

    lines.append(f"\n🔄 **今日更新记录**（共 {len(updates)} 次）")
    if not updates:
        lines.append("  · 今日暂无更新记录")
    else:
        for r in updates:
            lines.append(f"  · [{r['时间']}] {r['用户']} 更新了《{r['Skill名称']}》：{r['更新说明']}")

    # 热门 Skill（从飞书统计）
    all_claims = client.get_claim_records()
    from collections import Counter
    skill_counts = Counter(r["Skill名称"] for r in all_claims if r["操作"] == "领取")
    lines.append("\n🏆 **累计最热门 Skill（TOP 5）**")
    if not skill_counts:
        lines.append("  · 暂无统计数据")
    else:
        for i, (name, count) in enumerate(skill_counts.most_common(5), 1):
            last_user = next((r["用户"] for r in reversed(all_claims)
                            if r["Skill名称"] == name), "-")
            lines.append(f"  {i}. 《{name}》- 共被领取 {count} 次（最近：{last_user}）")

    unique_users = len({r["用户"] for r in claims if r["用户"]})
    lines.append(f"\n📈 **今日数据摘要**")
    lines.append(f"  · 领取总次数：{len(claims)} 次")
    lines.append(f"  · 参与用户数：{unique_users} 人")
    lines.append(f"  · 更新操作数：{len(updates)} 次")

    lines.append("\n" + "=" * 36)
    lines.append("以上为自动生成日报，如有疑问请联系管理员。")

    report = "\n".join(lines)
    print(report)
    return report


def generate_excel_report(target_date: str, repo_path: str):
    """从本地 Excel 生成日报（备用模式）"""
    from git_utils import git_pull

    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if os.path.exists(os.path.join(repo_path, ".git")):
        git_pull(repo_path)

    if not os.path.exists(log_path):
        print(f"【Skill 日报 {target_date}】\n\n暂无任何使用记录，请先通过 record_usage.py 记录操作。")
        return

    sheets = pd.read_excel(log_path, sheet_name=None)
    claim_df = sheets.get("领取记录", pd.DataFrame())
    update_df = sheets.get("更新记录", pd.DataFrame())
    stats_df = sheets.get("统计汇总", pd.DataFrame())

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


def generate_report(target_date: str = None, mode: str = "auto"):
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    feishu_available = os.path.exists(os.path.join(
        os.path.dirname(__file__), "feishu_config.py"))

    if mode == "feishu":
        if not feishu_available:
            print("错误: 飞书配置不存在", file=sys.stderr)
            sys.exit(1)
        generate_feishu_report(target_date)
    elif mode == "excel":
        generate_excel_report(target_date, REPO_PATH)
    else:  # auto
        if feishu_available:
            try:
                generate_feishu_report(target_date)
                return
            except Exception:
                pass  # 飞书失败，fallback 到 Excel
        generate_excel_report(target_date, REPO_PATH)


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    generate_report(target_date, mode)
