from dataclasses import replace

import pytest

from model.tco import PriceBook, estimate, ranking, seoul_premiums, t1_verdict, t2_verdict

# 손계산 값은 tests/conftest.py의 로직 검증용 가격 기준이다(실제 가격표와 다를 수 있다).


def test_ranking_is_cheapest_first(price_records, workloads):
    rows = estimate(PriceBook(price_records), workloads)
    # 손계산(us): W1 redshift 900 < bigquery 1506.26 < snowflake 1550 < databricks 2056
    assert ranking(rows, "W1", "us") == ["redshift", "bigquery", "snowflake", "databricks"]


def test_t1_winners_differ_by_scenario(price_records, workloads):
    v = t1_verdict(PriceBook(price_records), workloads, 0.5)
    # W3: bigquery 온디맨드 125+186.26=311.26 < redshift 120+240=360
    assert v["winners"] == {"W1": "redshift", "W2": "redshift", "W3": "bigquery"}
    assert v["supported"] is True


def test_t1_marks_close_call_as_sensitive(price_records, workloads):
    # W1: bigquery 용량을 x0.5로 하면 660+186.26=846.26 < redshift 900 → 1위가 바뀐다
    assert t1_verdict(PriceBook(price_records), workloads, 0.5)["robustness"]["W1"] == "민감"


def test_t1_marks_wide_margin_as_robust(price_records, workloads):
    cheap = [replace(r, price_usd=0.01) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
             for r in price_records]
    # redshift W1 = 1760x0.01+240 = 257.6, x1.5여도 266.4. 다른 플랫폼 x0.5 중 최저는 bigquery 846.26
    assert t1_verdict(PriceBook(cheap), workloads, 0.5)["robustness"]["W1"] == "견고"


def test_seoul_premium_per_sku(price_records):
    p = {(x["platform"], x["sku"]): x for x in seoul_premiums(price_records)}
    assert p[("redshift", "serverless-rpu")]["premium_pct"] == 16.8
    assert p[("databricks", "adls-hot-lrs")]["premium_pct"] == -3.8   # 서울이 더 싸다


def test_t2_uses_spread_threshold(price_records):
    v = t2_verdict(seoul_premiums(price_records), 10.0)
    assert v["spread_pp"] == pytest.approx(39.5)   # databricks DBU +35.7 − ADLS −3.8
    assert v["supported"] is True
    assert t2_verdict(seoul_premiums(price_records), 50.0)["supported"] is False
