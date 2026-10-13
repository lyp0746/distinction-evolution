# -*- coding: utf-8 -*-
"""create_github_release_per_artifact.py — 一个产物一个 tag：为每个发布产物各建一个 GitHub Release。

与 ``create_github_release.py``（单 release 多资产）相对。当每个产物需要被独立引用／
独立归档（例如各获得一个 Zenodo 版本 DOI）时使用本脚本。

要点
----
* **一个产物一个 tag**：每个 release 只承载一个资产。
* Token 从 git credential helper 读取，**不落盘、不打印**。
* 幂等：同名 tag / 同名资产已存在时复用，不重复创建。

用法
----
    python scripts/create_github_release_per_artifact.py --list
    python scripts/create_github_release_per_artifact.py --date 2026-10-12
    python scripts/create_github_release_per_artifact.py --date 2026-10-12 --draft
    python scripts/create_github_release_per_artifact.py --date 2026-10-12 --only epub

适配到新书时：改 REPO、ARTIFACTS（kind / 源文件 / 资产名 / 名称 / 说明）。
"""
import argparse
import os
import subprocess
import sys

import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = os.environ.get("GIT_BIN", r"D:\Git\cmd\git.exe")

REPO = "lyp0746/distinction-evolution"
BASE = "distinction-evolution"
BOOK = "区分的演化"

# (kind, 源文件, GitHub 资产名, release 名称, 说明)
ARTIFACTS = [
    ("print-pdf", f"release/{BASE}-print.pdf", f"{BASE}-print.pdf", "印刷版 PDF（A4）",
     "A4 单栏、四级 PDF 书签，适合打印与正式引用。"),
    ("ereader-pdf", f"release/{BASE}-ereader.pdf", f"{BASE}-ereader.pdf", "电子阅读版 PDF（B5）",
     "B5 重排、斑马纹表格，适合平板与屏幕阅读。"),
    ("epub", f"release/{BASE}.epub", f"{BASE}.epub", "EPUB 3",
     "EPUB 3（含 nav + NCX 四级目录）。"),
    ("html", f"release/{BASE}.html", f"{BASE}.html", "网页版（自包含）",
     "单文件自包含 HTML。"),
    ("ereader-html", f"release/{BASE}-ereader.html", f"{BASE}-ereader.html", "电子阅读网页版",
     "网页版 + 电子阅读样式。"),
    ("markdown", f"release/{BASE}.md", f"{BASE}.md", "合并 Markdown",
     "全书合一的 GFM Markdown。"),
    ("markdown-zip", f"release/{BASE}-markdown.zip", f"{BASE}-markdown.zip", "分文件 Markdown 打包",
     "逐文件 Markdown + assets 图片。"),
    ("cover", "release/cover.svg", "cover.svg", "封面矢量图",
     "满版封面 SVG。"),
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
        "User-Agent": "book-release"}
    if extra_headers:
        headers.update(extra_headers)
    return requests.request(method, url, headers=headers, timeout=180, **kw)


def ensure_release(tok, repo, tag, name, body, draft, prerelease):
    base = f"https://api.github.com/repos/{repo}"
    r = api(tok, "GET", f"{base}/releases/tags/{tag}")
    if r.status_code == 200:
        rel = r.json()
        print(f"[reuse] {tag} id={rel['id']}")
        return rel
    r = api(tok, "POST", f"{base}/releases", json={
        "tag_name": tag, "name": name, "body": body,
        "draft": draft, "prerelease": prerelease})
    if r.status_code not in (200, 201):
        raise SystemExit(f"创建 release 失败（{tag}）：{r.status_code} {r.text[:300]}")
    rel = r.json()
    print(f"[new] {tag} id={rel['id']} draft={draft}")
    return rel


def upload(tok, repo, rel, src, dst, refresh=False):
    p = os.path.join(HERE, src)
    if not os.path.exists(p):
        print(f"  [skip] 缺文件 {src}")
        return
    base = f"https://api.github.com/repos/{repo}"
    deleted = set()
    if refresh:
        # 删除同名旧资产，强制重传（用于内容更新但 tag 不变）
        for a in rel.get("assets", []):
            if a["name"] == dst:
                d = api(tok, "DELETE", f"{base}/releases/assets/{a['id']}")
                deleted.add(a["name"])
                print(f"  [del] {dst} ({d.status_code})")
    have = {a["name"] for a in rel.get("assets", [])} - deleted
    if dst in have:
        print(f"  [have] {dst}")
        return
    with open(p, "rb") as fh:
        up = api(tok, "POST",
                 f"https://uploads.github.com/repos/{repo}/releases/{rel['id']}/assets",
                 params={"name": dst}, data=fh,
                 extra_headers={"Content-Type": "application/octet-stream"})
    ok = up.status_code in (200, 201)
    print(f"  [{'ok' if ok else 'FAIL'}] {dst}"
          + ("" if ok else f" {up.status_code} {up.text[:200]}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--date", default="", help="版本日期，用于 tag，如 2026-10-12")
    ap.add_argument("--tag-prefix", default="edition")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--prerelease", action="store_true")
    ap.add_argument("--only", default="", help="只发布某个 kind")
    ap.add_argument("--refresh", action="store_true", help="删除同名旧资产并重传（内容更新时用）")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list or not args.date:
        print("产物清单（一个产物一个 tag）：")
        for kind, src, dst, name, desc in ARTIFACTS:
            print(f"  {args.tag_prefix}-<date>-{kind:16s} {name}  <- {src}")
        return

    tok = get_token()
    for kind, src, dst, name, desc in ARTIFACTS:
        if args.only and kind != args.only:
            continue
        tag = f"{args.tag_prefix}-{args.date}-{kind}"
        rel_name = f"{BOOK} · {name}（{args.date}）"
        body = (f"{desc}\n\n本 release 仅承载一个产物（一个产物一个 tag）。")
        rel = ensure_release(tok, args.repo, tag, rel_name, body,
                             args.draft, args.prerelease)
        upload(tok, args.repo, rel, src, dst, refresh=args.refresh)
        print(f"      -> {rel.get('html_url')}")
    print("完成。")


if __name__ == "__main__":
    main()
