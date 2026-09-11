from dataclasses import replace

from common.schema import write_snapshot
from model.tco import PriceBook, estimate, seoul_premiums, t1_verdict, t2_verdict
from publish.review_report import build_review, previous_snapshot, price_changes


def _results(price_records, workloads):
    book = PriceBook(price_records)
    t1 = {region: t1_verdict(book, workloads, 0.5, region) for region in ("us", "seoul")}
    return estimate(book, workloads), t1, t2_verdict(seoul_premiums(price_records), 10.0)


def test_review_lists_prices_costs_verdicts_and_next_command(price_records, workloads):
    rows, t1, t2 = _results(price_records, workloads)
    md = build_review("2026-09-11", price_records, None, rows, t1, t2)
    assert "첫 스냅샷" in md                                     # 비교할 승인 스냅샷이 없다
    assert "| redshift | compute | serverless-rpu | seoul | 0.438 |" in md
    assert "redshift 900" in md                                  # W1 미국 1위(로직 검증용 가격 기준 손계산)
    assert "T1 (미국)" in md and "T1 (서울)" in md
    assert "pipeline.py --confirm 2026-09-11" in md


def test_review_lists_changes_against_previous_snapshot(tmp_path, price_records, workloads):
    def with_seoul_rpu(price):
        return [replace(r, price_usd=price) if (r.platform, r.service, r.region) == ("redshift", "compute", "seoul") else r
                for r in price_records]

    write_snapshot(with_seoul_rpu(0.40), "2026-09-09", "all", root=tmp_path)
    (tmp_path / "2026-09-09" / "approved.txt").write_text("approved", encoding="utf-8")
    write_snapshot(with_seoul_rpu(0.99), "2026-09-10", "all", root=tmp_path)   # 승인 기록 없음(반려) → 비교에서 제외

    changes = price_changes(price_records, previous_snapshot("2026-09-11", root=tmp_path))

    assert [(c["sku"], c["region"], c["before"], c["after"], c["change_pct"]) for c in changes] == \
        [("serverless-rpu", "seoul", 0.40, 0.438, 9.5)]
    rows, t1, t2 = _results(price_records, workloads)
    assert "+9.5%" in build_review("2026-09-11", price_records, changes, rows, t1, t2)
