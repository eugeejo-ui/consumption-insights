"""Phase 1 파이프라인. 중간 검토 체크포인트(CLAUDE.md 규칙 14)가 있는 2단계 구조다.

1단계  .venv\\Scripts\\python.exe pipeline.py
       수집 → 스냅샷 저장 → 계산 → 검토 보고서(data/raw/<날짜>/review.md) 작성 → 멈춤
2단계  .venv\\Scripts\\python.exe pipeline.py --confirm <날짜>
       사용자가 검토 보고서를 컨펌한 뒤 실행한다. 사이트 생성 + 승인 기록(approved.txt)
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import REGIONS, PriceRecord, read_snapshot, write_snapshot
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.render_site import render
from publish.review_report import APPROVED_FILE, REVIEW_FILE, build_review, previous_snapshot, price_changes

RAW = Path("data/raw")


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def analyze(records: list[PriceRecord]) -> dict:
    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    return {
        "workloads": workloads,
        "rows": estimate(book, workloads),
        "premiums": premiums,
        "t1_by_region": {region: t1_verdict(book, workloads, thresholds["t1_sensitivity"], region) for region in REGIONS},
        "t2": t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
    }


def collect_and_review() -> Path:
    """1단계: 검토 보고서까지만 만들고 멈춘다. 화면 생성과 커밋은 컨펌 이후에 한다."""
    day = dt.date.today().isoformat()
    # 세 수집기가 모두 성공한 뒤에만 스냅샷을 쓴다(수동 가격표 게이트에서 멈추면 아무것도 남기지 않는다).
    collected = {
        "aws": aws_prices.collect(day),
        "azure": azure_prices.collect(day),
        "manual": manual_prices.collect(),
    }
    records = []
    for name, recs in collected.items():
        write_snapshot(recs, day, name, root=RAW)
        records += recs
    result = analyze(records)
    review = RAW / day / REVIEW_FILE
    review.write_text(
        build_review(day, records, price_changes(records, previous_snapshot(day, RAW)),
                     result["rows"], result["t1_by_region"], result["t2"],
                     counts={name: len(recs) for name, recs in collected.items()}),
        encoding="utf-8")
    print(f"검토 보고서: {review}")
    print(f"검토 후 컨펌: .venv\\Scripts\\python.exe pipeline.py --confirm {day}")
    return review


def confirm(day: str) -> Path:
    """2단계: 검토 보고서가 있는 스냅샷만 반영한다. 사이트를 만들고 승인 기록을 남긴다."""
    snapshot = RAW / day
    if not (snapshot / REVIEW_FILE).exists():
        raise SystemExit(f"{snapshot / REVIEW_FILE}가 없다. 검토 보고서가 없는 스냅샷은 반영하지 않는다(먼저 pipeline.py 실행).")
    records = [r for p in sorted(snapshot.glob("*.csv")) for r in read_snapshot(p)]
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
    parser = argparse.ArgumentParser(description="1단계: 수집·검토 보고서 작성 후 멈춤 / 2단계: --confirm으로 반영")
    parser.add_argument("--confirm", metavar="DAY", help="검토 보고서를 컨펌한 스냅샷(DAY)으로 사이트를 만든다")
    args = parser.parse_args(argv)
    return confirm(args.confirm) if args.confirm else collect_and_review()


if __name__ == "__main__":
    main()
