"""Phase 1 파이프라인: 수집 → 스냅샷 → TCO → site/ 생성.

실행:  .venv\\Scripts\\python.exe pipeline.py                        (오늘 날짜로 수집)
       .venv\\Scripts\\python.exe pipeline.py --offline 2026-09-11   (저장된 스냅샷으로만 계산)
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import REGIONS, read_snapshot, write_snapshot
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.render_site import render


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", metavar="DAY", help="수집하지 않고 data/raw/DAY 스냅샷으로 계산한다")
    args = parser.parse_args(argv)

    if args.offline:
        day = args.offline
        records = [r for p in sorted(Path("data/raw", day).glob("*.csv")) for r in read_snapshot(p)]
    else:
        day = dt.date.today().isoformat()
        # 세 수집기가 모두 성공한 뒤에만 스냅샷을 쓴다(수동 가격표 게이트에서 멈추면 아무것도 남기지 않는다).
        collected = {
            "aws": aws_prices.collect(day),
            "azure": azure_prices.collect(day),
            "manual": manual_prices.collect(),
        }
        records = []
        for name, recs in collected.items():
            write_snapshot(recs, day, name)
            records += recs

    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)

    out = render(estimate(book, workloads), premiums,
                 {region: t1_verdict(book, workloads, thresholds["t1_sensitivity"], region) for region in REGIONS},
                 t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
                 workloads, price_dates, built_on=day)
    print(f"site written: {out}")
    return out


if __name__ == "__main__":
    main()
