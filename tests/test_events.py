from dataclasses import replace

from detect.events import detect

TH = {"e1_min_cost_change_pct": 1.0}


def _with(records, platform, service, region, price):
    return [replace(r, price_usd=price) if (r.platform, r.service, r.region) == (platform, service, region) else r
            for r in records]


def test_same_prices_are_unchanged(price_records, workloads):
    ev = detect("2026-09-12", price_records, price_records, "2026-09-11", workloads, TH)
    assert ev["status"] == "unchanged" and ev["price_changes"] == [] and not ev["significant"]


def test_no_approved_snapshot_is_first(price_records, workloads):
    ev = detect("2026-09-12", price_records, None, None, workloads, TH)
    assert ev["status"] == "first" and ev["price_changes"] is None and not ev["significant"]


def test_small_price_change_needs_review_but_no_post(price_records, workloads):
    now = _with(price_records, "bigquery", "storage", "us", 0.0201)        # +0.5%: 월 비용 변화는 1% 미만
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert ev["status"] == "changed" and len(ev["price_changes"]) == 1
    assert ev["cost_changes"] == [] and ev["rank_changes"] == [] and not ev["significant"]


def test_cost_change_over_threshold_is_an_event(price_records, workloads):
    now = _with(price_records, "redshift", "compute", "us", 0.40)          # 0.375 → 0.40
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert [(c["scenario"], c["region"], c["platform"], c["before"], c["after"], c["change_pct"])
            for c in ev["cost_changes"]] == [
        ("W1", "us", "redshift", 900.0, 944.0, 4.9),
        ("W2", "us", "redshift", 600.0, 624.0, 4.0),
        ("W3", "us", "redshift", 360.0, 368.0, 2.2),
    ]
    assert ev["rank_changes"] == [] and ev["significant"] and ev["compared_to"] == "2026-09-11"


def test_rank_change_is_an_event(price_records, workloads):
    now = _with(price_records, "redshift", "compute", "us", 0.80)          # W1 미국 Redshift 900 → 1,648
    ev = detect("2026-09-12", now, price_records, "2026-09-11", workloads, TH)
    assert ev["rank_changes"][0] == {
        "scenario": "W1", "region": "us",
        "before": ["redshift", "bigquery", "snowflake", "databricks"],
        "after": ["bigquery", "snowflake", "redshift", "databricks"],
    }
    assert {(r["scenario"], r["region"]) for r in ev["rank_changes"]} == {("W1", "us"), ("W2", "us"), ("W3", "us")}
