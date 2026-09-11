import json
from pathlib import Path

import pytest

from collectors.azure_prices import collect, extract_databricks

ITEMS = json.loads((Path(__file__).parent / "fixtures" / "azure_items.json").read_text(encoding="utf-8"))


def test_picks_serverless_sql_and_first_storage_tier():
    recs = {r.sku: r for r in extract_databricks(ITEMS, "seoul", "2026-09-11", "src")}
    assert recs["sql-serverless-dbu"].price_usd == 0.95   # 0원 체험·POC, 클래식 0.22가 아니어야 한다
    assert recs["adls-hot-lrs"].price_usd == 0.02         # 51200GB 이상 구간(0.0192)이 아니어야 한다


def test_fails_when_serverless_sql_missing():
    items = [i for i in ITEMS if i["skuName"] != "Premium Serverless SQL"]
    with pytest.raises(ValueError):
        extract_databricks(items, "us", "2026-09-11", "src")


def test_collect_queries_both_regions_with_both_filters():
    seen = []

    def fake_fetch(expr):
        seen.append(expr)
        return ITEMS

    recs = collect("2026-09-11", fetch=fake_fetch)
    assert len(seen) == 4
    assert any("koreacentral" in e for e in seen) and any("eastus" in e for e in seen)
    assert {r.region for r in recs} == {"us", "seoul"}
