#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
record_usage.py - 记录 Skill 领取和更新操作
用法:
  python record_usage.py claim  <skill_name> <user_name> [repo路径]
  python record_usage.py update <skill_name> <user_name> <update_desc> [repo路径]

写入后自动 git commit + push 同步到远程
"""

import sys
import json
import os
from datetime import datetime
import pandas as pd
from git_utils import git_pull, git_commit_push

REPO_PATH = os.path.dirname(os.path.dirname(__file__))
LOG_PATH = os.path.join(REPO_PATH, "data", "skill_usage_log.xlsx")

CLAIM_SHEET = "领取记录"
UPDATE_SHEET = "更新记录"
STATS_SHEET = "统计汇总"


def get_known_users(repo_path: str = REPO_PATH) -> set:
    """从领取记录中获取所有已知用户名"""
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
    """写入后自动推送到 GitHub"""
    log_path = os.path.join(repo_path, "data", "skill_usage_log.xlsx")
    if not os.path.exists(os.path.join(repo_path, ".git")):
        return
    msg = f"[{action}] {user} 领取/更新了《{skill}》"
    git_commit_push(repo_path, [log_path], msg)


def record_claim(skill_name: str, user_name: str, repo_path: str = REPO_PATH):
    log_path = LOG_PATH if repo_path == REPO_PATH else os.path.join(repo_path, "data", "skill_usage_log.xlsx")

    # 拉取最新
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
    result = {"status": "success", "action": "claim", "skill": skill_name, "user": user_name, "time": now, "total_claims": total}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def record_update(skill_name: str, user_name: str, update_desc: str, repo_path: str = REPO_PATH):
    log_path = LOG_PATH if repo_path == REPO_PATH else os.path.join(repo_path, "data", "skill_usage_log.xlsx")

    if os.path.exists(os.path.join(repo_path, ".git")):
        git_pull(repo_path)

    claim_df, update_df, stats_df = load_or_create_workbook(log_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_row = pd.DataFrame([{"时间": now, "用户": user_name, "Skill名称": skill_name, "更新说明": update_desc}])
    update_df = pd.concat([update_df, new_row], ignore_index=True)

    save_workbook(log_path, claim_df, update_df, stats_df)
    sync_to_github(repo_path, skill_name, "更新", user_name)

    result = {"status": "success", "action": "update", "skill": skill_name, "user": user_name, "time": now, "update_desc": update_desc}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法:")
        print("  python record_usage.py claim  <skill_name> <user_name> [repo路径]")
        print("  python record_usage.py update <skill_name> <user_name> <update_desc> [repo路径]")
        sys.exit(1)

    action = sys.argv[1]
    skill = sys.argv[2]
    user = sys.argv[3]

    if action == "claim":
        repo = sys.argv[4] if len(sys.argv) > 4 else REPO_PATH
        record_claim(skill, user, repo)
    elif action == "update":
        if len(sys.argv) < 5:
            print("update 操作需要提供更新说明")
            sys.exit(1)
        desc = sys.argv[4]
        repo = sys.argv[5] if len(sys.argv) > 5 else REPO_PATH
        record_update(skill, user, desc, repo)
    else:
        print(f"未知操作: {action}，支持 claim / update")
        sys.exit(1)
