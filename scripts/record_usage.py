#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
record_usage.py - 记录 Skill 领取和更新操作
用法:
  python record_usage.py claim  <skill_name> <user_name> [数据源模式]
  python record_usage.py update <skill_name> <user_name> <update_desc> [数据源模式]

数据源: feishu（优先）| excel（备用，GitHub 同步）
模式: feishu | excel | auto（默认飞书，失败回退 Excel）
"""

import sys
import json
import os
from datetime import datetime
import pandas as pd
from git_utils import git_pull

REPO_PATH = os.path.dirname(os.path.dirname(__file__))


# ========== 飞书模式 ==========

def record_claim_feishu(skill_name: str, user_name: str):
    from feishu_client import FeishuClient
    from feishu_config import (APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                               TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                          TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    result = client.record_claim(skill_name, user_name)
    result["source"] = "feishu"
    print(json.dumps(result, ensure_ascii=False, indent=2))


def record_update_feishu(skill_name: str, user_name: str, update_desc: str):
    from feishu_client import FeishuClient
    from feishu_config import (APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                               TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                          TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
    result = client.record_update(skill_name, user_name, update_desc)
    result["source"] = "feishu"
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ========== Excel 模式（备用）==========#

CLAIM_SHEET = "领取记录"
UPDATE_SHEET = "更新记录"
STATS_SHEET = "统计汇总"


def get_known_users(repo_path: str = REPO_PATH) -> set:
    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if not os.path.exists(log_path):
        return set()
    df = pd.read_excel(log_path, sheet_name=CLAIM_SHEET)
    return set(df["用户"].dropna().unique())


def load_or_create_workbook(path):
    if os.path.exists(path):
        sheets = pd.read_excel(path, sheet_name=None)
        claim_df = sheets.get(CLAIM_SHEET, pd.DataFrame(columns=["时间", "用户", "Skill名称", "操作"]))
        update_df = sheets.get(UPDATE_SHEET, pd.DataFrame(columns=["时间", "用户", "Skill名称", "更新说明"]))
        stats_df = sheets.get(STATS_SHEET, pd.DataFrame(columns=["Skill名称", "领取次数", "最后领取时间", "最后领取用户"]))
    else:
        claim_df = pd.DataFrame(columns=["时间", "用户", "Skill名称", "操作"])
        update_df = pd.DataFrame(columns=["时间", "用户", "Skill名称", "更新说明"])
        stats_df = pd.DataFrame(columns=["Skill名称", "领取次数", "最后领取时间", "最后领取用户"])
    return claim_df, update_df, stats_df


def save_workbook(path, claim_df, update_df, stats_df):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        claim_df.to_excel(writer, sheet_name=CLAIM_SHEET, index=False)
        update_df.to_excel(writer, sheet_name=UPDATE_SHEET, index=False)
        stats_df.to_excel(writer, sheet_name=STATS_SHEET, index=False)


def sync_to_github(repo_path: str, skill: str, action: str, user: str):
    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if not os.path.exists(os.path.join(repo_path, ".git")):
        return
    from git_utils import git_commit_push
    msg = f"[{action}] {user} 领取/更新了《{skill}》"
    git_commit_push(repo_path, [log_path], msg)


def record_claim_excel(skill_name: str, user_name: str, repo_path: str = REPO_PATH):
    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if os.path.exists(os.path.join(repo_path, ".git")):
        git_pull(repo_path)
    claim_df, update_df, stats_df = load_or_create_workbook(log_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"时间": now, "用户": user_name, "Skill名称": skill_name, "操作": "领取"}])
    claim_df = pd.concat([claim_df, new_row], ignore_index=True)
    mask = stats_df["Skill名称"] == skill_name
    if mask.any():
        current = float(stats_df.loc[mask, "领取次数"].fillna(0).values[0])
        stats_df.loc[mask, "领取次数"] = int(current) + 1
        stats_df.loc[mask, "最后领取时间"] = now
        stats_df.loc[mask, "最后领取用户"] = user_name
    else:
        new_stat = pd.DataFrame([{"Skill名称": skill_name, "领取次数": 1, "最后领取时间": now, "最后领取用户": user_name}])
        stats_df = pd.concat([stats_df, new_stat], ignore_index=True)
    save_workbook(log_path, claim_df, update_df, stats_df)
    sync_to_github(repo_path, skill_name, "领取", user_name)
    total = int(stats_df.loc[stats_df["Skill名称"] == skill_name, "领取次数"].values[0])
    result = {"status": "success", "action": "claim", "skill": skill_name, "user": user_name, "time": now, "total_claims": total, "source": "excel"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def record_update_excel(skill_name: str, user_name: str, update_desc: str, repo_path: str = REPO_PATH):
    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if os.path.exists(os.path.join(repo_path, ".git")):
        git_pull(repo_path)
    claim_df, update_df, stats_df = load_or_create_workbook(log_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"时间": now, "用户": user_name, "Skill名称": skill_name, "更新说明": update_desc}])
    update_df = pd.concat([update_df, new_row], ignore_index=True)
    save_workbook(log_path, claim_df, update_df, stats_df)
    sync_to_github(repo_path, skill_name, "更新", user_name)
    result = {"status": "success", "action": "update", "skill": skill_name, "user": user_name, "time": now, "update_desc": update_desc, "source": "excel"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ========== 入口 ==========

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法:")
        print("  python record_usage.py claim  <skill_name> <user_name> [feishu|excel|auto]")
        print("  python record_usage.py update <skill_name> <user_name> <update_desc> [feishu|excel|auto]")
        sys.exit(1)

    action = sys.argv[1]
    skill = sys.argv[2]
    user = sys.argv[3]
    mode = sys.argv[4] if len(sys.argv) > 4 else "auto"

    feishu_available = os.path.exists(os.path.join(os.path.dirname(__file__), "feishu_config.py"))

    if mode == "feishu":
        if not feishu_available:
            print("错误: 飞书配置不存在，请使用 excel 模式或配置飞书", file=sys.stderr)
            sys.exit(1)
        use_feishu = True
    elif mode == "excel":
        use_feishu = False
    else:  # auto
        use_feishu = feishu_available

    if action == "claim":
        if use_feishu:
            record_claim_feishu(skill, user)
        else:
            record_claim_excel(skill, user)
    elif action == "update":
        desc = sys.argv[4] if mode == "excel" and len(sys.argv) > 4 else (sys.argv[4] if len(sys.argv) > 4 else "")
        if mode != "excel" and len(sys.argv) > 4:
            desc = sys.argv[5] if len(sys.argv) > 5 else ""
        if use_feishu:
            record_update_feishu(skill, user, desc)
        else:
            record_update_excel(skill, user, desc)
    else:
        print(f"未知操作: {action}，支持 claim / update")
        sys.exit(1)
