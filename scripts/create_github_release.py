# -*- coding: utf-8 -*-
"""
create_github_release.py —— 为当前提交创建 GitHub Release 并上传 release/ 产物。

用途：本仓库通过“GitHub Release → Zenodo”完成归档（mint 版本 DOI）。
本脚本把这一步脚本化；token 从 git credential helper 读取，**不落盘、不打印**。

用法：
    python scripts/create_github_release.py \
        --tag edition-2026-10-11-audit \
        --name "2026-10-11 审计闭环" \
        --body-file release/修订说明.md
    # 先做草稿（不触发 Zenodo）：
    python scripts/create_github_release.py --tag ... --name ... --draft
"""
import argparse
import os
import subprocess
import sys

import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = os.environ.get("GIT_BIN", r"D:\Git\cmd\git.exe")

# release/ 内的中文名 → GitHub 资产 ASCII 名（与既有 release 对齐）
ASSETS = [
    ("release/cover.svg", "cover.svg"),
    ("release/entropy-spiral-print.pdf", "entropy-spiral-print.pdf"),
    ("release/entropy-spiral-ereader.pdf", "entropy-spiral-ereader.pdf"),
    ("release/entropy-spiral.epub", "entropy-spiral.epub"),
    ("release/entropy-spiral.html", "entropy-spiral.html"),
    ("release/entropy-spiral-ereader.html", "entropy-spiral-ereader.html"),
    ("release/entropy-spiral.md", "entropy-spiral.md"),
    ("release/entropy-spiral-markdown.zip", "entropy-spiral-markdown.zip"),
    ("release/README.md", "README.md"),
    ("release/修订说明.md", "REVISION-NOTES.md"),
    ("release/数据缺口清单.md", "DATA-GAPS.md"),
    ("release/欢迎补充数据.md", "CONTRIBUTING-DATA.md"),
]


def get_token():
    out = subprocess.run(
        [GIT, "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    raise SystemExit("未能从 git credential helper 取得 token")


def api(tok, method, url, extra_headers=None, **kw):
    headers = {
        "Authorization": f"token {tok}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "entropy-spiral-release"}
    if extra_headers:
        headers.update(extra_headers)
    r = requests.request(method, url, headers=headers, timeout=120, **kw)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="lyp0746/entropy-spiral")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--prerelease", action="store_true")
    args = ap.parse_args()

    body = args.body
    if args.body_file and os.path.exists(os.path.join(HERE, args.body_file)):
        with open(os.path.join(HERE, args.body_file), encoding="utf-8") as f:
            body = f.read()

    tok = get_token()
    base = f"https://api.github.com/repos/{args.repo}"

    # 已存在则复用
    r = api(tok, "GET", f"{base}/releases/tags/{args.tag}")
    if r.status_code == 200:
        rel = r.json()
        print(f"[reuse] release {args.tag} id={rel['id']}")
    else:
        r = api(tok, "POST", f"{base}/releases", json={
            "tag_name": args.tag, "name": args.name, "body": body,
            "draft": args.draft, "prerelease": args.prerelease})
        if r.status_code not in (200, 201):
            raise SystemExit(f"创建 release 失败：{r.status_code} {r.text[:300]}")
        rel = r.json()
        print(f"[new] release {args.tag} id={rel['id']} draft={args.draft}")

    have = {a["name"] for a in rel.get("assets", [])}
    for src, dst in ASSETS:
        p = os.path.join(HERE, src)
        if not os.path.exists(p):
            print(f"  [skip] 缺文件 {src}")
            continue
        if dst in have:
            print(f"  [have] {dst}")
            continue
        with open(p, "rb") as fh:
            up = api(tok, "POST",
                     f"https://uploads.github.com/repos/{args.repo}/releases/{rel['id']}/assets",
                     params={"name": dst}, data=fh,
                     extra_headers={"Content-Type": "application/octet-stream"})
        print(f"  [{'ok' if up.status_code in (200,201) else 'FAIL'}] {dst}"
              + ("" if up.status_code in (200, 201) else f" {up.status_code} {up.text[:160]}"))
    print("完成。release 页面：", rel.get("html_url"))


if __name__ == "__main__":
    main()
