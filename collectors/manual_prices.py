"""사람이 원본에서 확인한 수동 가격표(data/manual/*_prices.csv)를 읽는다.
Snowflake·Databricks 웹사이트는 약관상 자동 접근하지 않는다 (Phase 0-4)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from common.schema import PriceRecord

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_manual(path: Path) -> list[PriceRecord]:
    records = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            confirmed = (row.pop("confirmed_on") or "").strip()
            if not DATE.match(confirmed):
                raise ValueError(f"{path}:{line_no} confirmed_on is empty or not YYYY-MM-DD "
                                 "(사람이 원본에서 확인한 날짜를 적어야 한다)")
            records.append(PriceRecord(**{**row, "price_usd": float(row["price_usd"]), "fetched_at": confirmed}))
    return records


def collect(manual_dir: Path = Path("data/manual")) -> list[PriceRecord]:
    return [r for p in sorted(Path(manual_dir).glob("*_prices.csv")) for r in load_manual(p)]
