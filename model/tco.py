"""같은 워크로드의 플랫폼별 월 비용(TCO) 추정. 플랫폼 간 비교는 [가정] 기반 모델 추정이다."""
from __future__ import annotations

from dataclasses import dataclass

from common.schema import REGIONS, PriceRecord

PLATFORMS = ("snowflake", "databricks", "redshift", "bigquery")
GB_PER_UNIT = {"GB-month": 1.0, "TB-month": 1000.0, "GiB-month": 1.073741824}


@dataclass(frozen=True)
class CostRow:
    scenario: str
    platform: str
    region: str
    compute_usd: float
    storage_usd: float

    @property
    def total_usd(self) -> float:
        return self.compute_usd + self.storage_usd


class PriceBook:
    def __init__(self, records: list[PriceRecord]):
        self._by: dict[tuple[str, str, str], PriceRecord] = {}
        for r in records:
            key = (r.platform, r.service, r.region)
            if key in self._by and self._by[key].sku != r.sku:
                raise ValueError(f"two SKUs for {key}: {self._by[key].sku}, {r.sku}")
            self._by[key] = r

    def get(self, platform: str, service: str, region: str) -> PriceRecord:
        try:
            return self._by[(platform, service, region)]
        except KeyError:
            raise KeyError(f"missing price: {platform}/{service}/{region}") from None


def storage_cost(book: PriceBook, platform: str, region: str, storage_gb: float) -> float:
    rec = book.get(platform, "storage", region)
    return storage_gb / GB_PER_UNIT[rec.unit] * rec.price_usd


def compute_cost(book: PriceBook, platform: str, region: str, scenario: dict, capacity: dict,
                 factor: float = 1.0) -> float:
    if scenario["mode"] == "scan" and platform == "bigquery":
        # 스캔량이 곧 사용량이다. 용량 가정(factor)을 적용하지 않는다.
        return scenario["tib_scanned_per_month"] * book.get("bigquery", "scan", region).price_usd
    if scenario["mode"] == "scan":
        hours = scenario["tib_scanned_per_month"] / scenario["tib_per_hour"]
    else:
        hours = scenario["hours_per_month"]
    units = capacity[platform]["per_hour"] * scenario["size"] * hours * factor
    return units * book.get(platform, "compute", region).price_usd


def estimate(book: PriceBook, workloads: dict, factors: dict[str, float] | None = None) -> list[CostRow]:
    factors = factors or {}
    rows = []
    for sid, scenario in workloads["scenarios"].items():
        for platform in PLATFORMS:
            for region in REGIONS:
                rows.append(CostRow(
                    sid, platform, region,
                    compute_cost(book, platform, region, scenario, workloads["capacity_per_small"],
                                 factors.get(platform, 1.0)),
                    storage_cost(book, platform, region, workloads["storage_gb"]),
                ))
    return rows


def ranking(rows: list[CostRow], scenario: str, region: str) -> list[str]:
    selected = sorted((r for r in rows if r.scenario == scenario and r.region == region), key=lambda r: r.total_usd)
    return [r.platform for r in selected]


def t1_verdict(book: PriceBook, workloads: dict, sensitivity: float, region: str = "us") -> dict:
    """T1: 시나리오마다 1위가 다른가. 1위가 플랫폼 하나의 용량 가정 ±sensitivity에도 유지되면 '견고'."""
    base = estimate(book, workloads)
    winners = {sid: ranking(base, sid, region)[0] for sid in workloads["scenarios"]}
    robustness = {sid: "견고" for sid in workloads["scenarios"]}
    for platform in PLATFORMS:
        for factor in (1 - sensitivity, 1 + sensitivity):
            shaken = estimate(book, workloads, {platform: factor})
            for sid in workloads["scenarios"]:
                if ranking(shaken, sid, region)[0] != winners[sid]:
                    robustness[sid] = "민감"
    return {"winners": winners, "robustness": robustness, "supported": len(set(winners.values())) > 1}


def seoul_premiums(records: list[PriceRecord]) -> list[dict]:
    by = {(r.platform, r.service, r.sku, r.region): r for r in records}
    out = []
    for (platform, service, sku, region), us in sorted(by.items()):
        seoul = by.get((platform, service, sku, "seoul"))
        if region != "us" or seoul is None:
            continue
        out.append({"platform": platform, "service": service, "sku": sku,
                    "us": us.price_usd, "seoul": seoul.price_usd,
                    "premium_pct": round((seoul.price_usd / us.price_usd - 1) * 100, 1)})
    return out


def t2_verdict(premiums: list[dict], min_spread_pp: float) -> dict:
    values = [p["premium_pct"] for p in premiums]
    spread = round(max(values) - min(values), 1)
    return {"spread_pp": spread, "supported": spread >= min_spread_pp}
