# -*- coding: utf-8 -*-
"""
preregistration_checkup.py —— 事前登记盲测的核销账本工具（附录 I / docs/preregistration）。

功能：
  1) 校验 registry.json 与 checkups.csv 的一致性（未知 test_id、缺列、日期倒序）。
  2) 打印当前进度摘要（每项：核对次数、最近状态、是否触发）。
  3) --append 追加一行核销（append-only，绝不改写旧行）。
  4) --plan 打印需要联网核对的数据源清单（离线环境下不伪造数值）。

用法：
    python analysis/preregistration_checkup.py
    python analysis/preregistration_checkup.py --plan
    python analysis/preregistration_checkup.py --append --test B1 \
        --indicator "本币兑美元变动" --value -0.04 --unit ratio \
        --source "IMF IFS" --vintage 2026Q4 --triggered no --note "例行季检"
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(HERE, "docs", "preregistration")
REGISTRY = os.path.join(PREREG, "registry.json")
CHECKUPS = os.path.join(PREREG, "checkups.csv")

COLUMNS = ["test_id", "check_date", "checker", "status", "indicator",
           "value", "unit", "source", "vintage", "triggered", "note"]


def load_registry():
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def load_rows():
    if not os.path.exists(CHECKUPS):
        return []
    with open(CHECKUPS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def validate(reg, rows):
    known = {t["id"] for t in reg["tests"]}
    problems = []
    if rows and list(rows[0].keys()) != COLUMNS:
        problems.append(f"CSV 列不匹配：{list(rows[0].keys())} != {COLUMNS}")
    last_date = {}
    for i, r in enumerate(rows, start=2):  # 含表头，从第 2 行起
        if r["test_id"] not in known:
            problems.append(f"第 {i} 行：未知 test_id={r['test_id']}")
        d = r.get("check_date", "")
        try:
            dt.date.fromisoformat(d)
        except Exception:
            problems.append(f"第 {i} 行：非法日期 {d!r}")
            continue
        if r["test_id"] in last_date and d < last_date[r["test_id"]]:
            problems.append(f"第 {i} 行：日期早于同命题上一行（{d} < {last_date[r['test_id']]}）")
        last_date[r["test_id"]] = max(last_date.get(r["test_id"], d), d)
    return problems


def summary(reg, rows):
    out = []
    for t in reg["tests"]:
        own = [r for r in rows if r["test_id"] == t["id"]]
        checks = [r for r in own if r["status"] != "baseline"]
        triggered = [r for r in own if r.get("triggered") in ("yes", "partial")]
        last = own[-1] if own else None
        out.append({
            "id": t["id"],
            "title": t["title"],
            "n_checks": len(checks),
            "n_triggered": len(triggered),
            "last_status": last["status"] if last else "无",
            "last_date": last["check_date"] if last else "—",
        })
    return out


def plan(reg):
    print("需要联网/官方 vintage 的核对项（离线不伪造数值）：")
    for t in reg["tests"]:
        print(f"\n[{t['id']}] {t['title']}  （预计核对：{t['observation_due']}）")
        for ind in t["indicators"]:
            print(f"  - {ind['name']}  ← {ind['source']}")


def append_row(args):
    rows = load_rows()
    if not os.path.exists(CHECKUPS):
        with open(CHECKUPS, "w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, COLUMNS).writeheader()
    reg = load_registry()
    if args.test not in {t["id"] for t in reg["tests"]}:
        raise SystemExit(f"未知 test_id：{args.test}")
    row = {
        "test_id": args.test,
        "check_date": args.date or dt.date.today().isoformat(),
        "checker": args.checker,
        "status": "checkup",
        "indicator": args.indicator,
        "value": args.value,
        "unit": args.unit,
        "source": args.source,
        "vintage": args.vintage,
        "triggered": args.triggered,
        "note": args.note,
    }
    with open(CHECKUPS, "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, COLUMNS).writerow(row)
    print("已追加：", row)


def main():
    ap = argparse.ArgumentParser(description="事前登记盲测的核销账本工具")
    ap.add_argument("--plan", action="store_true", help="列出需联网核对的数据源")
    ap.add_argument("--append", action="store_true", help="追加一行核销")
    ap.add_argument("--test", help="B1/B2/B3")
    ap.add_argument("--date", help="核对日期 YYYY-MM-DD")
    ap.add_argument("--checker", default="author")
    ap.add_argument("--indicator")
    ap.add_argument("--value")
    ap.add_argument("--unit", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--vintage", default="")
    ap.add_argument("--triggered", default="no", choices=["no", "partial", "yes"])
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    reg = load_registry()

    if args.plan:
        plan(reg)
        return

    if args.append:
        if not args.test or not args.indicator or args.value is None:
            raise SystemExit("--append 需要 --test --indicator --value")
        append_row(args)

    rows = load_rows()
    problems = validate(reg, rows)
    print("=== 登记：%s（%s）===" % (reg["project"], reg["registered_at"]))
    print("迁移状态：", reg["migration"]["status"])
    print("\n=== 核销进度 ===")
    for s in summary(reg, rows):
        print(f"  {s['id']} {s['title']}: 核对 {s['n_checks']} 次，"
              f"触发 {s['n_triggered']} 次，最近 {s['last_date']}/{s['last_status']}")
    if problems:
        print("\n[!] 校验问题：")
        for p in problems:
            print("   -", p)
        sys.exit(1)
    print("\n[ok] 账本校验通过（append-only）。")


if __name__ == "__main__":
    main()
