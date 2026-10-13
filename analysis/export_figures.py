# -*- coding: utf-8 -*-
"""export_figures.py — 把 assets/svg/*.svg 渲染为约 300 dpi 的 PNG 备份。

优先使用 cairosvg；若不可用，则回退到 Chrome/Edge 无头渲染。
输出：output/figures/*.png
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(HERE, "assets", "svg")
OUT = os.path.join(HERE, "output", "figures")


def via_cairosvg():
    try:
        import cairosvg
    except Exception:
        return False
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(SVG)):
        if not f.endswith(".svg"):
            continue
        src = os.path.join(SVG, f)
        dst = os.path.join(OUT, f[:-4] + ".png")
        cairosvg.svg2png(url=src, write_to=dst, scale=3.0)
        print("wrote", dst)
    return True


def via_chrome():
    cands = [
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/usr/bin/chromium", "/usr/bin/google-chrome",
    ]
    browser = next((c for c in cands if os.path.exists(c)), None)
    if not browser:
        print("未找到 Chrome/Edge，且 cairosvg 不可用；跳过 PNG 导出。")
        return False
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(SVG)):
        if not f.endswith(".svg"):
            continue
        src = os.path.join(SVG, f)
        uri = "file://" + src.replace("\\", "/")
        dst = os.path.join(OUT, f[:-4] + ".png")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-sandbox",
                        f"--screenshot={dst}", "--window-size=1600,1200", uri], check=False)
        print("wrote", dst)
    return True


if __name__ == "__main__":
    ok = via_cairosvg() or via_chrome()
    sys.exit(0 if ok else 0)
