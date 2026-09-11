"""파이프라인. 중간 검토 체크포인트(CLAUDE.md 규칙 14)가 있는 2단계 구조다.

1단계  .venv\\Scripts\\python.exe pipeline.py [--simulate]
       수집 → 이전 승인 스냅샷과 비교
       · 변화 없음: data/checks.csv에 한 줄 기록하고 끝낸다(스냅샷을 만들지 않는다)
       · 변화 있음(또는 첫 스냅샷): 스냅샷, review.md, events.json, (E1이면) post.md → 멈춤
2단계  .venv\\Scripts\\python.exe pipeline.py --confirm <날짜>
       사용자가 검토 보고서를 컨펌한 뒤 실행한다. 사이트 생성 + 승인 기록(approved.txt)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from dataclasses import replace
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import REGIONS, PriceRecord, read_snapshot, write_snapshot
from detect.events import detect
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.render_post import render_post
from publish.render_site import render
from publish.review_report import (APPROVED_FILE, REVIEW_FILE, build_review, latest_approved_day,
                                   previous_snapshot)

RAW = Path("data/raw")
CHECKS = Path("data/checks.csv")
EVENTS_FILE = "events.json"
POST_FILE = "post.md"
SIMULATED = ("redshift", "compute", "us")     # --simulate: 이 단가만 5% 올려 검토 PR 흐름을 검증한다
SIMULATED_TAG = " (simulated)"
SIMULATION_NOTICE = "> **시뮬레이션:** 검증용 가짜 변동(Redshift 미국 RPU +5%)이다. 머지하지 말고 닫는다.\n\n"


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def analyze(records: list[PriceRecord]) -> dict:
    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    return {
        "workloads": workloads,
        "thresholds": thresholds,
        "rows": estimate(book, workloads),
        "premiums": premiums,
        "t1_by_region": {region: t1_verdict(book, workloads, thresholds["t1_sensitivity"], region) for region in REGIONS},
        "t2": t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
    }


def record_check(day: str, result: str, compared_to: str | None, path: Path = CHECKS) -> Path:
    """매일 확인 기록(day,result,compared_to). 같은 날 다시 실행하면 그 줄을 덮어쓴다."""
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["day"] != day]
    rows.append({"day": day, "result": result, "compared_to": compared_to or ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["day", "result", "compared_to"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["day"]))
    return path


def write_outputs(**values: str) -> None:
    """GitHub Actions 단계 출력(GITHUB_OUTPUT). 로컬에서는 아무것도 하지 않는다."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in values.items())


def simulate_change(records: list[PriceRecord], factor: float = 1.05) -> list[PriceRecord]:
    return [replace(r, price_usd=round(r.price_usd * factor, 6), source=r.source + SIMULATED_TAG)
            if (r.platform, r.service, r.region) == SIMULATED else r for r in records]


def collect_and_review(simulate: bool = False) -> Path:
    """1단계: 변화가 있으면 검토 자료까지만 만들고 멈춘다. 화면 생성과 커밋은 컨펌 이후에 한다."""
    day = dt.date.today().isoformat()
    if (RAW / day / APPROVED_FILE).exists():
        raise SystemExit(f"{day} 스냅샷은 이미 승인됐다. 같은 날 다시 수집하지 않는다.")
    # 세 수집기가 모두 성공한 뒤에만 쓴다(수동 가격표 게이트에서 멈추면 아무것도 남기지 않는다).
    collected = {
        "aws": aws_prices.collect(day),
        "azure": azure_prices.collect(day),
        "manual": manual_prices.collect(),
    }
    if simulate:
        collected["aws"] = simulate_change(collected["aws"])
    records = [r for recs in collected.values() for r in recs]
    result = analyze(records)
    compared_to = latest_approved_day(day, RAW)
    events = detect(day, records, previous_snapshot(day, RAW), compared_to, result["workloads"], result["thresholds"])
    write_outputs(day=day, status=events["status"], significant=str(events["significant"]).lower())

    if events["status"] == "unchanged":
        out = record_check(day, "unchanged", compared_to)
        print(f"변화 없음({compared_to} 승인 스냅샷과 같다). 기록: {out}")
        return out

    for name, recs in collected.items():
        write_snapshot(recs, day, name, root=RAW)
    folder = RAW / day
    review = folder / REVIEW_FILE
    text = build_review(day, records, events["price_changes"], result["rows"], result["t1_by_region"], result["t2"],
                        counts={name: len(recs) for name, recs in collected.items()},
                        significant=events["significant"])
    review.write_text((SIMULATION_NOTICE if simulate else "") + text, encoding="utf-8")
    (folder / EVENTS_FILE).write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if events["significant"]:
        (folder / POST_FILE).write_text(render_post(events), encoding="utf-8")
    if not simulate:
        record_check(day, "review", compared_to)
    print(f"검토 보고서: {review}")
    print(f"검토 후 컨펌: 검토 PR Merge, 또는 로컬에서 .venv\\Scripts\\python.exe pipeline.py --confirm {day}")
    return review


def confirm(day: str) -> Path:
    """2단계: 검토 보고서가 있는 스냅샷만 반영한다. 사이트를 만들고 승인 기록을 남긴다."""
    snapshot = RAW / day
    if not (snapshot / REVIEW_FILE).exists():
        raise SystemExit(f"{snapshot / REVIEW_FILE}가 없다. 검토 보고서가 없는 스냅샷은 반영하지 않는다(먼저 pipeline.py 실행).")
    records = [r for p in sorted(snapshot.glob("*.csv")) for r in read_snapshot(p)]
    if any(r.source.endswith(SIMULATED_TAG) for r in records):
        raise SystemExit(f"{day}는 시뮬레이션 스냅샷이다. 반영하지 않는다.")
    result = analyze(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)
    out = render(result["rows"], result["premiums"], result["t1_by_region"], result["t2"], result["workloads"],
                 price_dates, built_on=day)
    (snapshot / APPROVED_FILE).write_text(f"approved_at: {dt.datetime.now().isoformat(timespec='seconds')}\n",
                                          encoding="utf-8")
    print(f"site written: {out}")
    return out


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="1단계: 수집·비교·검토 자료 작성 후 멈춤 / 2단계: --confirm으로 반영")
    parser.add_argument("--confirm", metavar="DAY", help="검토 보고서를 컨펌한 스냅샷(DAY)으로 사이트를 만든다")
    parser.add_argument("--simulate", action="store_true", help="검증용 가짜 변동을 넣는다(검토 PR 흐름 확인용, 머지 금지)")
    args = parser.parse_args(argv)
    return confirm(args.confirm) if args.confirm else collect_and_review(simulate=args.simulate)


if __name__ == "__main__":
    main()
