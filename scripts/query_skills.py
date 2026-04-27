#!/usr/bin/env python3
"""
query_skills.py - Skill 检索脚本
用法: python query_skills.py <关键词> [数据源模式]

数据源优先级:
1. 飞书多维表格（优先，数据实时）
2. 本地 Excel（备用，需 GitHub 同步）

示例:
  python query_skills.py "调研"
  python query_skills.py "邓风华" "feishu"
  python query_skills.py "罗琦" "excel"
"""

import sys
import json
import os
import pandas as pd
from difflib import SequenceMatcher

REPO_PATH = os.path.dirname(os.path.dirname(__file__))


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_feishu(query: str):
    """从飞书多维表格搜索"""
    try:
        from feishu_client import FeishuClient
        from feishu_config import (APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                                   TABLE_SKILL)
        client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN,
                              TABLE_CLAIM, TABLE_UPDATE, TABLE_SKILL)
        records = client.search_skills(query)
        if records:
            print(json.dumps({"query": query, "count": len(records),
                             "source": "feishu", "results": records},
                             ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"query": query, "count": 0, "source": "feishu",
                             "results": [], "message": "未找到匹配的 Skill"},
                             ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(json.dumps({"error": f"飞书读取失败: {e}"}, ensure_ascii=False),
              file=sys.stderr)
        return False


def search_excel(query: str, repo_path: str):
    """从本地 Excel 搜索（需 Git 同步）"""
    from git_utils import git_pull

    skill_list_path = os.path.join(repo_path, "data", "skill_list.xlsx")
    if os.path.exists(os.path.join(repo_path, ".git")):
        git_pull(repo_path)

    if not os.path.exists(skill_list_path):
        print(json.dumps({"error": f"找不到 skill 列表文件: {skill_list_path}"},
                         ensure_ascii=False))
        sys.exit(1)

    df = pd.read_excel(skill_list_path)

    # 兼容列名
    name_col = None
    for col in df.columns:
        if "skill" in col.lower() or "名称" in col:
            name_col = col
            break
    if name_col is None:
        name_col = df.columns[-1]

    results = []
    for _, row in df.iterrows():
        skill_name = str(row[name_col])
        score = similarity(query, skill_name)
        if query.lower() in skill_name.lower() or score > 0.25:
            entry = {col: str(row[col]) for col in df.columns}
            entry["_match_score"] = round(score, 3)
            results.append(entry)

    results.sort(key=lambda x: x["_match_score"], reverse=True)

    if results:
        print(json.dumps({"query": query, "count": len(results),
                         "source": "excel", "results": results},
                         ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"query": query, "count": 0, "source": "excel",
                         "results": [], "message": "未找到匹配的 Skill"},
                         ensure_ascii=False, indent=2))


def search_skills(query: str, mode: str = "auto"):
    """
    mode: "feishu" | "excel" | "auto"
    auto 模式优先飞书，飞书失败则回退 Excel
    """
    if mode == "auto":
        if os.path.exists(os.path.join(os.path.dirname(__file__), "feishu_config.py")):
            if search_feishu(query):
                return
        # 飞书不可用，使用 Excel
        search_excel(query, REPO_PATH)
    elif mode == "feishu":
        search_feishu(query)
    elif mode == "excel":
        search_excel(query, REPO_PATH)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python query_skills.py <关键词> [feishu|excel|auto]")
        sys.exit(1)
    query = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    search_skills(query, mode)
