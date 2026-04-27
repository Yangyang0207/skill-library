#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feishu_bitable_init.py - 初始化飞书多维表格（使用已创建的测试表格）
用法: python feishu_bitable_init.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json, os, time, urllib.request, urllib.error, urllib.parse, pandas as pd

APP_ID = "cli_a95ee2523af95bb4"
APP_SECRET = "eXDtKf0MVBndJ5ymSUdjEERy8Pehhmel"

# 已创建的测试表格
APP_TOKEN = "HVsrbotCHaUEzcs3xbFc4SlPnDb"
DEFAULT_TABLE_ID = "tbl5CRQAwuiVv8R7"  # 当前只有一个默认表，先改名当领取记录表

REPO_PATH = os.path.dirname(os.path.dirname(__file__))
LOCAL_SKILL_LIST = os.path.join(REPO_PATH, "data", "skill_list.xlsx")
LOCAL_USAGE_LOG = os.path.join(REPO_PATH, "data", "skill_usage_log.xlsx")
TOKEN_CACHE = os.path.join(os.path.dirname(__file__), "feishu_token_cache.json")


# ========== 核心函数 ==========

def get_token():
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE, "r", encoding="utf-8") as f:
            c = json.load(f)
        if time.time() < c.get("expire_time", 0) - 60:
            print(f"[Token] 缓存 (剩余 {c['expire_time'] - time.time():.0f}s)")
            return c["token"]
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    token = result["tenant_access_token"]
    with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
        json.dump({"token": token, "expire_time": time.time() + result.get("expire", 7200)}, f)
    print("[Token] 重新获取成功")
    return token


def api(method, path, token, data=None, params=None):
    url = "https://open.feishu.cn/open-apis" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    payload = None
    if data is not None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, data=payload, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP {e.code}: {body[:400]}")
    if result.get("code") != 0:
        raise Exception(f"API [{result.get('code')}]: {result.get('msg')}")
    return result.get("data", {})


def rename_table(token, table_id, new_name):
    """重命名数据表"""
    print(f"  重命名表 {table_id} -> {new_name}")
    api("PATCH", f"/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}", token,
        data={"name": new_name})
    print(f"    OK")


def add_field(token, table_id, field_name, field_type=1):
    """添加字段"""
    try:
        api("POST", f"/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/fields", token,
            data={"field_name": field_name, "type": field_type})
    except Exception as e:
        if "FieldNameDuplicated" in str(e) or "已存在" in str(e) or "already exists" in str(e):
            pass  # 字段已存在
        else:
            raise


def batch_create_records(token, table_id, fields, records):
    """批量创建记录（最多500条/次）"""
    if not records:
        print("    无数据，跳过")
        return
    batch_size = 500
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        rows = []
        for record in batch:
            fields_data = {}
            for idx, name in enumerate(fields):
                val = record[idx] if idx < len(record) else ""
                fields_data[name] = str(val) if val is not None else ""
            rows.append({"fields": fields_data})
        api("POST",
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/records/batch_create",
            token, data={"records": rows})
        total += len(rows)
        print(f"    写入 {len(rows)} 条...")
    print(f"    共 {total} 条")


# ========== 主流程 ==========

def get_existing_tables(token):
    """获取已存在的数据表"""
    r = api("GET", f"/bitable/v1/apps/{APP_TOKEN}/tables", token)
    tables = {}
    for item in r.get("items", []):
        tables[item["name"]] = item["table_id"]
    return tables


def get_or_create_table(token, name, existing_tables):
    """获取或创建表"""
    if name in existing_tables:
        print(f"  使用已有表: {name} -> {existing_tables[name]}")
        return existing_tables[name]
    print(f"  创建新表: {name}")
    r = api("POST", f"/bitable/v1/apps/{APP_TOKEN}/tables", token,
            data={"table": {"name": name}})
    table_id = r["table_id"]
    print(f"    -> {table_id}")
    return table_id


def main():
    print("=" * 50)
    print("飞书多维表格初始化")
    print("=" * 50)

    token = get_token()

    # 先获取已有表
    print("\n[0] 检查已有数据表...")
    existing = get_existing_tables(token)
    for name, tid in existing.items():
        print(f"  {name} -> {tid}")

    # 1. 领取记录表
    print("\n[1] 设置领取记录表...")
    if "领取记录" in existing:
        claim_table_id = existing["领取记录"]
        print(f"  使用已有: {claim_table_id}")
    else:
        rename_table(token, DEFAULT_TABLE_ID, "领取记录")
        claim_table_id = DEFAULT_TABLE_ID
    add_field(token, claim_table_id, "时间", field_type=1)
    add_field(token, claim_table_id, "用户", field_type=1)
    add_field(token, claim_table_id, "Skill名称", field_type=1)
    add_field(token, claim_table_id, "操作", field_type=1)
    claim_fields = ["时间", "用户", "Skill名称", "操作"]

    # 2. 更新记录表
    print("\n[2] 设置更新记录表...")
    update_table_id = get_or_create_table(token, "更新记录", existing)
    add_field(token, update_table_id, "时间", field_type=1)
    add_field(token, update_table_id, "用户", field_type=1)
    add_field(token, update_table_id, "Skill名称", field_type=1)
    add_field(token, update_table_id, "更新说明", field_type=1)
    update_fields = ["时间", "用户", "Skill名称", "更新说明"]

    # 3. Skill目录表
    print("\n[3] 设置Skill目录表...")
    skill_table_id = get_or_create_table(token, "Skill目录", existing)
    add_field(token, skill_table_id, "序号", field_type=1)
    add_field(token, skill_table_id, "SKILL名称", field_type=1)
    skill_fields = ["序号", "SKILL名称"]

    # 4. 导入 Skill 目录
    print("\n[4] 导入 Skill 目录...")
    if os.path.exists(LOCAL_SKILL_LIST):
        df = pd.read_excel(LOCAL_SKILL_LIST)
        df.columns = [c.strip() for c in df.columns]
        records = [[str(row.get("序号", "")), str(row.get("SKILL 名称", ""))]
                   for _, row in df.iterrows()]
        batch_create_records(token, skill_table_id, skill_fields, records)
    else:
        print("  本地 skill_list.xlsx 不存在，跳过")

    # 5. 导入领取记录
    print("\n[5] 导入领取记录...")
    if os.path.exists(LOCAL_USAGE_LOG):
        try:
            df = pd.read_excel(LOCAL_USAGE_LOG, sheet_name="领取记录")
            df.columns = [c.strip() for c in df.columns]
            records = [[str(row.get("时间", "")), str(row.get("用户", "")),
                        str(row.get("Skill名称", "")), str(row.get("操作", ""))]
                       for _, row in df.iterrows()]
            batch_create_records(token, claim_table_id, claim_fields, records)
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print("  本地文件不存在，跳过")

    # 6. 导入更新记录
    print("\n[6] 导入更新记录...")
    if os.path.exists(LOCAL_USAGE_LOG):
        try:
            df = pd.read_excel(LOCAL_USAGE_LOG, sheet_name="更新记录")
            df.columns = [c.strip() for c in df.columns]
            records = [[str(row.get("时间", "")), str(row.get("用户", "")),
                        str(row.get("Skill名称", "")), str(row.get("更新说明", ""))]
                       for _, row in df.iterrows()]
            batch_create_records(token, update_table_id, update_fields, records)
        except Exception as e:
            print(f"  读取失败或无数据: {e}")
    else:
        print("  本地文件不存在，跳过")

    # 7. 保存配置
    print("\n[7] 保存配置...")
    config_path = os.path.join(os.path.dirname(__file__), "feishu_config.py")
    config = f'''# -*- coding: utf-8 -*-
# 飞书多维表格配置（自动生成）
APP_ID = "{APP_ID}"
APP_SECRET = "{APP_SECRET}"
BITABLE_APP_TOKEN = "{APP_TOKEN}"
TABLE_CLAIM = "{claim_table_id}"       # 领取记录表
TABLE_UPDATE = "{update_table_id}"    # 更新记录表
TABLE_SKILL = "{skill_table_id}"       # Skill目录表
BITABLE_URL = "https://zcn07z6w5bmf.feishu.cn/base/{APP_TOKEN}"
'''
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config)
    print(f"  OK: {config_path}")

    print(f"\n{'='*50}")
    print(f"完成！多维表格地址：")
    print(f"  https://zcn07z6w5bmf.feishu.cn/base/{APP_TOKEN}")
    print(f"  app_token: {APP_TOKEN}")
    print(f"  领取记录表: {claim_table_id}")
    print(f"  更新记录表: {update_table_id}")
    print(f"  Skill目录表: {skill_table_id}")


if __name__ == "__main__":
    main()
