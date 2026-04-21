#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_utils.py - Git 同步工具
通过 subprocess 调用 git.exe 执行 pull / commit / push
"""

import subprocess
import os

GIT_EXE = r"D:\Git\cmd\git.exe"


def _run_git(cwd, *args):
    cmd = [GIT_EXE, "-C", cwd] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def git_pull(repo_path: str):
    """拉取最新代码"""
    return _run_git(repo_path, "pull", "--rebase", "origin", "main")


def git_commit_push(repo_path: str, files: list, commit_msg: str, author_name: str = "WorkBuddy", author_email: str = "workbuddy@ai.com"):
    """提交文件变更并推送到远程"""
    _run_git(repo_path, "config", "user.name", author_name)
    _run_git(repo_path, "config", "user.email", author_email)
    for f in files:
        rel = os.path.relpath(f, repo_path).replace(os.sep, "/")
        _run_git(repo_path, "add", rel)
    _run_git(repo_path, "commit", "-m", commit_msg)
    code, stdout, stderr = _run_git(repo_path, "push", "-u", "origin", "main")
    return code, stdout, stderr
