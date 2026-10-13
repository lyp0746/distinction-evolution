# -*- coding: utf-8 -*-
"""create_github_release_single.py — 单一 release：一个 tag 承载全部产物。

本仓库约定：只保留**一个** release（tag ``edition-<日期>``），一次承载全部
读者可见产物。不要创建 per-artifact 的 release/tag。

* Token 从 git credential helper 读取，不落盘、不打印。
* 幂等：release 或同名资产已存在时复用；``--refresh`` 时删除同名旧资产再重传。

用法
----
    python scripts/create_github_release_single.py --date 2026-10-13
    python scripts/create_github_release_single.py --date 2026-10-13 --refresh
"""
import argparse
import os
import subprocess

import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = os.environ.get("GIT_BIN", r"D:\Git\cmd\git.exe")
REPO = "lyp0746/distinction-evolution"
BOOK = "区分的演化"
DOI = "10.5281/zenodo.23345013"

# (本地文件, GitHub 资产名)
ASSETS = [
    ("release/distinction-evolution-print.pdf", "distinction-evolution-print.pdf"),
    ("release/distinction-evolution-ereader.pdf", "distinction-evolution-ereader.pdf"),
    ("release/distinction-evolution.epub", "distinction-evolution.epub"),
    ("release/distinction-evolution.html", "distinction-evolution.html"),
    ("release/distinction-evolution-ereader.html", "distinction-evolution-ereader.html"),
    ("release/distinction-evolution.md", "distinction-evolution.md"),
    ("release/distinction-evolution-markdown.zip", "distinction-evolution-markdown.zip"),
    ("release/cover.svg", "cover.svg"),
    ("release/README.md", "README.md"),
    ("release/修订说明.md", "REVISION-NOTES.md"),
    ("release/数据缺口清单.md", "DATA-GAPS.md"),
    ("release/欢迎补充数据.md", "CONTRIBUTING-DATA.md"),
]


def get_token():
    out = subprocess.run([GIT, "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True,
                         env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    raise SystemExit("未能从 git credential helper 取得 token")


def api(tok, method, url, extra_headers=None, **kw):
    headers = {"Authorization": f"token {tok}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "book-release"}
    if extra_headers:
        headers.update(extra_headers)
    return requests.request(method, url, headers=headers, timeout=600, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--date", required=True, help="如 2026-10-13")
    ap.add_argument("--tag-prefix", default="edition")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--prerelease", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="删除同名旧资产并重传（内容更新时用）")
    args = ap.parse_args()

    tag = f"{args.tag_prefix}-{args.date}"
    base = f"https://api.github.com/repos/{args.repo}"
    body = (f"《{BOOK}》发布包（{tag}）。\n\n"
            f"全书 DOI：{DOI} · https://doi.org/{DOI}\n\n"
            "含印刷版 PDF、电子阅读版 PDF、EPUB 3、网页版、合并／分文件 Markdown、"
            "封面与说明文件。本 release 为仓库唯一的 release。")
    tok = get_token()

    r = api(tok, "GET", f"{base}/releases/tags/{tag}")
    if r.status_code == 200:
        rel = r.json()
        print(f"[reuse] {tag} id={rel['id']}")
    else:
        rr = api(tok, "POST", f"{base}/releases", json={
            "tag_name": tag, "name": f"{BOOK} · {args.date}", "body": body,
            "draft": args.draft, "prerelease": args.prerelease})
        if rr.status_code not in (200, 201):
            raise SystemExit(f"创建 release 失败：{rr.status_code} {rr.text[:300]}")
        rel = rr.json()
        print(f"[new] {tag} id={rel['id']}")

    deleted = set()
    if args.refresh:
        for a in rel.get("assets", []):
            api(tok, "DELETE", f"{base}/releases/assets/{a['id']}")
            deleted.add(a["name"])
            print(f"  [del] {a['name']}")

    have = {a["name"] for a in rel.get("assets", [])} - deleted
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
        print(f"  [{'ok' if up.status_code in (200, 201) else 'FAIL'}] {dst}"
              + ("" if up.status_code in (200, 201) else f" {up.status_code} {up.text[:160]}"))
    print("完成。release 页面：", rel.get("html_url"))


if __name__ == "__main__":
    main()
