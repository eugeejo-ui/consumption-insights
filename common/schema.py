"""가격 스냅샷 공통 스키마: 모든 수집기가 이 형식으로 저장한다."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

REGIONS = ("us", "seoul")
FIELDS = ["platform", "service", "sku", "region", "unit", "price_usd", "source", "fetched_at"]


@dataclass(frozen=True)
class PriceRecord:
    platform: str
    service: str
    sku: str
    region: str
    unit: str
    price_usd: float
    source: str
    fetched_at: str

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(f"unknown region: {self.region}")
        if not self.price_usd > 0:
            raise ValueError(f"price must be positive: {self.sku} {self.region} {self.price_usd}")


def write_snapshot(records: list[PriceRecord], day: str, name: str, root: Path = Path("data/raw")) -> Path:
    out = Path(root) / day / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted((asdict(r) for r in records), key=lambda r: (r["platform"], r["service"], r["sku"], r["region"]))
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return out


def read_snapshot(path: Path) -> list[PriceRecord]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [PriceRecord(**{**row, "price_usd": float(row["price_usd"])}) for row in csv.DictReader(f)]
