# -*- coding: utf-8 -*-
"""create_zenodo_version.py — 为既有 Zenodo 记录发布一个新版本。

用法：
    ZENODO_TOKEN=<你的 token> python scripts/create_zenodo_version.py
    ZENODO_TOKEN=<...> python scripts/create_zenodo_version.py --dry-run
    ZENODO_TOKEN=<...> python scripts/create_zenodo_version.py --sandbox

流程（Zenodo REST API）：
    1. POST /deposit/depositions/<RECORD_ID>/actions/newversion   新建草稿版本
    2. GET  草稿 -> 取 id 与 files bucket
    3. PUT  草稿 metadata（来自 .zenodo.json）
    4. 清空草稿旧文件，上传 release/ 全部文件
    5. POST /deposit/depositions/<草稿 id>/actions/publish       发布

依赖：仅标准库。
token 权限需包含 deposit:write。
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

try:  # Windows 控制台默认 GBK，强制 UTF-8 以打印下标等字符
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

RECORD_ID = "23412033"                       # 当前版本记录号
API = "https://zenodo.org/api"
BUCKET = "https://zenodo.org/api/files"
RELEASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "release")
META_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".zenodo.json")
TIMEOUT = 180


def req(method, url, token, data=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {token}"}
    if headers:
        h.update(headers)
    body = None
    if raw is not None:
        body = raw
    elif data is not None:
        body = json.dumps(data).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=TIMEOUT) as resp:
            txt = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"HTTP {e.code} on {method} {url}\n{detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印将提交的元数据，不调用 API")
    ap.add_argument("--sandbox", action="store_true", help="使用 sandbox.zenodo.org（测试）")
    ap.add_argument("--record", default=RECORD_ID, help=f"当前版本记录号（默认 {RECORD_ID}）")
    args = ap.parse_args()

    meta = json.load(open(META_FILE, encoding="utf-8"))
    api = "https://sandbox.zenodo.org/api" if args.sandbox else API

    if args.dry_run:
        print("=== 将提交的元数据（.zenodo.json）===")
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        print("\n=== 将上传的发布包文件 ===")
        for f in sorted(os.listdir(RELEASE_DIR)):
            p = os.path.join(RELEASE_DIR, f)
            if os.path.isfile(p):
                print(f"  {f}  ({os.path.getsize(p)} bytes)")
        return

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        raise SystemExit("未设置 ZENODO_TOKEN。请先 export/设置环境变量（权限需含 deposit:write）。")

    print(f"[1/5] 从记录 {args.record} 新建草稿版本 …")
    _, r = req("POST", f"{api}/deposit/depositions/{args.record}/actions/newversion", token)
    draft_url = (r.get("links") or {}).get("latest_draft")
    if not draft_url:
        raise SystemExit(f"未能取得 latest_draft：{json.dumps(r, ensure_ascii=False)[:500]}")
    draft = draft_url if draft_url.startswith("http") else api + draft_url.split("/api", 1)[-1]
    print("      draft:", draft)

    print("[2/5] 读取草稿（id / bucket）…")
    _, d = req("GET", draft, token)
    did = d["id"]
    bucket = (d.get("links") or {}).get("bucket") or f"{api}/files/{d['bucket'].split('/')[-1]}"
    print("      id:", did)

    print("[3/5] 写入元数据 …")
    try:
        req("PUT", f"{api}/deposit/depositions/{did}", token, data={"metadata": meta})
    except SystemExit as e:
        # 某些 Zenodo 实例不接受 subjects：降级重试
        if "subjects" in str(e):
            meta2 = {k: v for k, v in meta.items() if k != "subjects"}
            print("      注意：subjects 被拒，改为仅用 keywords 重试。")
            req("PUT", f"{api}/deposit/depositions/{did}", token, data={"metadata": meta2})
        else:
            raise

    print("[4/5] 清空草稿旧文件并上传 release/ …")
    for f in d.get("files", []):
        req("DELETE", f["links"]["self"], token)
    for name in sorted(os.listdir(RELEASE_DIR)):
        p = os.path.join(RELEASE_DIR, name)
        if not os.path.isfile(p):
            continue
        with open(p, "rb") as fh:
            req("PUT", f"{bucket}/{name}", token, raw=fh.read(),
                headers={"Content-Type": "application/octet-stream"})
        print("      +", name)

    print("[5/5] 发布 …")
    _, pub = req("POST", f"{api}/deposit/depositions/{did}/actions/publish", token)
    doi = (pub.get("doi") or (pub.get("metadata") or {}).get("doi") or "")
    print("完成。新版本 DOI:", doi)
    print("记录页:", pub.get("links", {}).get("record_html") or pub.get("links", {}).get("html"))


if __name__ == "__main__":
    main()
