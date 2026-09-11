"""E1 변동 감지(Phase 2-2). 오늘 가격을 이전 승인 스냅샷과 비교해 events.json 내용을 만든다.
월 비용은 양쪽 모두 현재 workloads.yaml로 계산한다. 가정이 아니라 가격이 바뀐 효과만 보기 위해서다."""
from __future__ import annotations

from common.schema import REGIONS, PriceRecord
from model.tco import CostRow, PriceBook, estimate, ranking
from publish.review_report import price_changes


def cost_changes(now: list[CostRow], prev: list[CostRow], min_pct: float) -> list[dict]:
    before = {(r.scenario, r.region, r.platform): r.total_usd for r in prev}
    out = []
    for r in now:
        b = before[(r.scenario, r.region, r.platform)]
        pct = round((r.total_usd / b - 1) * 100, 1)
        if abs(pct) >= min_pct:
            out.append({"scenario": r.scenario, "region": r.region, "platform": r.platform,
                        "before": round(b, 2), "after": round(r.total_usd, 2), "change_pct": pct})
    return out


def rank_changes(now: list[CostRow], prev: list[CostRow], scenarios) -> list[dict]:
    out = []
    for sid in scenarios:
        for region in REGIONS:
            b, a = ranking(prev, sid, region), ranking(now, sid, region)
            if a != b:
                out.append({"scenario": sid, "region": region, "before": b, "after": a})
    return out


def detect(day: str, records: list[PriceRecord], previous: list[PriceRecord] | None, compared_to: str | None,
           workloads: dict, thresholds: dict) -> dict:
    min_pct = thresholds["e1_min_cost_change_pct"]
    events = {"day": day, "compared_to": compared_to, "min_cost_change_pct": min_pct,
              "price_changes": price_changes(records, previous), "cost_changes": [], "rank_changes": []}
    if previous is None:
        events["status"] = "first"
    elif not events["price_changes"]:
        events["status"] = "unchanged"
    else:
        events["status"] = "changed"
        now, prev = estimate(PriceBook(records), workloads), estimate(PriceBook(previous), workloads)
        events["cost_changes"] = cost_changes(now, prev, min_pct)
        events["rank_changes"] = rank_changes(now, prev, workloads["scenarios"])
    events["significant"] = bool(events["cost_changes"] or events["rank_changes"])
    return events
