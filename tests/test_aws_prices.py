import json
from pathlib import Path

import pytest

from collectors.aws_prices import collect, extract_redshift

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "aws_redshift_offer.json").read_text(encoding="utf-8"))


def test_picks_on_demand_rpu_and_ignores_capacity_reservations():
    recs = {r.sku: r for r in extract_redshift(FIXTURE, "seoul", "2026-09-11", "src")}
    assert recs["serverless-rpu"].price_usd == 0.438  # 2839(선결제)나 0.342(예약)가 아니어야 한다
    assert recs["serverless-rpu"].unit == "RPU-hour"
    assert recs["managed-storage"].price_usd == 0.0261


def test_fails_loudly_when_sku_missing():
    with pytest.raises(ValueError):
        extract_redshift({"products": {}, "terms": {"OnDemand": {}}}, "us", "2026-09-11", "src")


def test_collect_fetches_region_index_then_region_files():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if url.endswith("region_index.json"):
            return {"regions": {"us-east-1": {"currentVersionUrl": "/x/us-east-1/index.json"},
                                "ap-northeast-2": {"currentVersionUrl": "/x/ap-northeast-2/index.json"}}}
        return FIXTURE

    recs = collect("2026-09-11", fetch=fake_fetch)
    assert {r.region for r in recs} == {"us", "seoul"}
    assert any(u.endswith("/x/ap-northeast-2/index.json") for u in calls)
