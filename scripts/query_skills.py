#!/usr/bin/env python3
"""
query_skills.py - Skill 检索脚本
用法: python query_skills.py <关键词> [repo路径]

会在读取前自动 git pull 同步最新数据
"""

import sys
import json
import os
import pandas as pd
from difflib import SequenceMatcher
from git_utils import git_pull

REPO_PATH = os.path.dirname(os.path.dirname(__file__))  # skill-library 根目录


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_skills(query: str, repo_path: str = REPO_PATH):
    # 自动 pull 最新数据
    skill_list_path = os.path.join(repo_path, "data", "skill_list.xlsx")
    if os.path.exists(os.path.join(repo_path, ".git")):
        code, _, _ = git_pull(repo_path)
        if code != 0:
            pass  # pull 失败不影响继续

    if not os.path.exists(skill_list_path):
        print(json.dumps({"error": f"找不到 skill 列表文件: {skill_list_path}"}, ensure_ascii=False))
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
        print(json.dumps({"query": query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"query": query, "count": 0, "results": [], "message": "未找到匹配的 Skill，请换个关键词试试"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python query_skills.py <关键词> [repo路径]")
        sys.exit(1)
    query = sys.argv[1]
    repo = sys.argv[2] if len(sys.argv) > 2 else REPO_PATH
    search_skills(query, repo)
