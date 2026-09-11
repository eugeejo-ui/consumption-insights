from pathlib import Path

import pytest
import yaml

from model.tco import PLATFORMS, PriceBook, estimate

REPO = Path(__file__).resolve().parent.parent


def rows_by_key(rows):
    return {(r.scenario, r.platform, r.region): r for r in rows}


def test_w1_snowflake_matches_hand_calculation(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W1", "snowflake", "us")]
    assert r.compute_usd == pytest.approx(2 * 1 * 220 * 3.00)   # 440 credits x $3 = $1,320
    assert r.storage_usd == pytest.approx(10000 / 1000 * 23.00)  # 10TB x $23 = $230
    assert r.total_usd == pytest.approx(1550.0)


def test_w3_bigquery_uses_on_demand_scan_price(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W3", "bigquery", "us")]
    assert r.compute_usd == pytest.approx(20 * 6.25)             # 20 TiB x $6.25


def test_w3_capacity_platforms_convert_scan_to_hours(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W3", "redshift", "us")]
    assert r.compute_usd == pytest.approx(8 * 4 * (20 / 2) * 0.375)  # 320 RPU-h x $0.375


def test_gib_storage_is_converted_from_gb(price_records, workloads):
    r = rows_by_key(estimate(PriceBook(price_records), workloads))[("W1", "bigquery", "us")]
    assert r.storage_usd == pytest.approx(10000 / 1.073741824 * 0.02)


def test_estimate_covers_every_scenario_platform_region(price_records, workloads):
    assert len(estimate(PriceBook(price_records), workloads)) == 3 * len(PLATFORMS) * 2


def test_missing_price_names_the_gap(price_records, workloads):
    book = PriceBook([r for r in price_records if not (r.platform == "redshift" and r.region == "seoul")])
    with pytest.raises(KeyError, match="redshift"):
        estimate(book, workloads)


def test_repo_workloads_file_is_complete():
    wl = yaml.safe_load((REPO / "data" / "manual" / "workloads.yaml").read_text(encoding="utf-8"))
    assert set(wl["scenarios"]) == {"W1", "W2", "W3"}
    assert set(wl["capacity_per_small"]) == set(PLATFORMS)
