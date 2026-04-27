# -*- coding: utf-8 -*-
"""
feishu_client.py - 飞书多维表格统一客户端
所有飞书 API 操作统一入口
"""

import json, os, time, urllib.request, urllib.error, urllib.parse
from typing import Optional, List, Dict, Any


class FeishuClient:
    """飞书多维表格操作客户端"""

    def __init__(self, app_id: str, app_secret: str,
                 app_token: str, claim_table: str, update_table: str, skill_table: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.claim_table = claim_table
        self.update_table = update_table
        self.skill_table = skill_table

        # Token 缓存文件
        cache_dir = os.path.dirname(__file__)
        self.token_cache = os.path.join(cache_dir, "feishu_token_cache.json")

    # ===== Token 管理 =====

    def _get_token(self) -> str:
        if os.path.exists(self.token_cache):
            with open(self.token_cache, "r", encoding="utf-8") as f:
                c = json.load(f)
            if time.time() < c.get("expire_time", 0) - 60:
                return c["token"]
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = json.dumps({"app_id": self.app_id, "app_secret": self.app_secret}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        token = result["tenant_access_token"]
        with open(self.token_cache, "w", encoding="utf-8") as f:
            json.dump({"token": token, "expire_time": time.time() + result.get("expire", 7200)}, f)
        return token

    # ===== 底层请求 =====

    def _request(self, method: str, path: str, data: dict = None,
                 params: dict = None) -> dict:
        url = "https://open.feishu.cn/open-apis" + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {self._get_token()}")
        payload = None
        if data is not None:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, data=payload, timeout=30) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise Exception(f"HTTP {e.code}: {body[:300]}")
        if result.get("code") != 0:
            raise Exception(f"API [{result.get('code')}]: {result.get('msg')}")
        return result.get("data", {})

    # ===== 记录操作 =====

    def _batch_create(self, table_id: str, records: List[Dict[str, Any]]):
        """批量创建记录（自动分批，每批500条）"""
        for i in range(0, len(records), 500):
            batch = records[i:i + 500]
            self._request("POST",
                f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/batch_create",
                data={"records": [{"fields": r} for r in batch]})

    def _get_all_records(self, table_id: str, filter_formula: str = None) -> List[dict]:
        """获取所有记录（自动翻页）"""
        records = []
        page_token = None
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            if filter_formula:
                params["filter"] = filter_formula
            data = self._request("GET",
                f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records",
                params=params)
            items = data.get("items", [])
            records.extend(items)
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return records

    def _delete_all_records(self, table_id: str):
        """清空表中所有记录"""
        records = self._get_all_records(table_id)
        if not records:
            return
        for i in range(0, len(records), 500):
            batch = records[i:i + 500]
            record_ids = [r["record_id"] for r in batch]  # list of strings
            self._request("POST",
                f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/batch_delete",
                data={"records": record_ids})

    # ===== Skill 目录 =====

    def search_skills(self, keyword: str) -> List[dict]:
        """搜索 Skill（模糊匹配名称）"""
        records = self._get_all_records(self.skill_table)
        keyword = keyword.lower()
        matched = []
        for r in records:
            name = r.get("fields", {}).get("SKILL名称", "")
            if keyword in str(name).lower():
                matched.append({
                    "序号": r["fields"].get("序号", ""),
                    "SKILL名称": r["fields"].get("SKILL名称", ""),
                    "record_id": r["record_id"]
                })
        return matched

    # ===== 领取记录 =====

    def record_claim(self, skill_name: str, user_name: str) -> dict:
        """追加一条领取记录"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        self._request("POST",
            f"/bitable/v1/apps/{self.app_token}/tables/{self.claim_table}/records",
            data={"fields": {
                "时间": now,
                "用户": user_name,
                "Skill名称": skill_name,
                "操作": "领取"
            }})
        # 统计该 skill 被领取次数
        all_records = self._get_all_records(self.claim_table)
        total = sum(1 for r in all_records
                    if r["fields"].get("Skill名称") == skill_name
                    and r["fields"].get("操作") == "领取")
        return {"status": "success", "skill": skill_name, "user": user_name,
                "time": now, "total_claims": total}

    def get_claim_records(self, date: str = None) -> List[dict]:
        """获取领取记录（可选按日期过滤）"""
        records = self._get_all_records(self.claim_table)
        result = []
        for r in records:
            fields = r["fields"]
            t = fields.get("时间", "")
            if date and not t.startswith(date):
                continue
            result.append({
                "时间": t,
                "用户": fields.get("用户", ""),
                "Skill名称": fields.get("Skill名称", ""),
                "操作": fields.get("操作", "")
            })
        return result

    def get_known_users(self) -> set:
        """获取所有已知用户名"""
        records = self._get_all_records(self.claim_table)
        return {r["fields"].get("用户", "") for r in records if r["fields"].get("用户")}

    # ===== 更新记录 =====

    def record_update(self, skill_name: str, user_name: str, update_desc: str) -> dict:
        """追加一条更新记录"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        self._request("POST",
            f"/bitable/v1/apps/{self.app_token}/tables/{self.update_table}/records",
            data={"fields": {
                "时间": now,
                "用户": user_name,
                "Skill名称": skill_name,
                "更新说明": update_desc
            }})
        return {"status": "success", "skill": skill_name, "user": user_name,
                "time": now, "update_desc": update_desc}

    def get_update_records(self, date: str = None) -> List[dict]:
        """获取更新记录（可选按日期过滤）"""
        records = self._get_all_records(self.update_table)
        result = []
        for r in records:
            fields = r["fields"]
            t = fields.get("时间", "")
            if date and not t.startswith(date):
                continue
            result.append({
                "时间": t,
                "用户": fields.get("用户", ""),
                "Skill名称": fields.get("Skill名称", ""),
                "更新说明": fields.get("更新说明", "")
            })
        return result
