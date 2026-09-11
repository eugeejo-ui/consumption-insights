from dataclasses import replace

import pytest

from detect.events import detect
from publish.render_post import check_numbers, render_post


def _events(price_records, workloads):
    now = [replace(r, price_usd=0.80) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
           for r in price_records]
    return detect("2026-09-12", now, price_records, "2026-09-11", workloads, {"e1_min_cost_change_pct": 1.0})


def test_post_lists_price_cost_and_rank_changes(price_records, workloads):
    post = render_post(_events(price_records, workloads))
    assert "Redshift serverless-rpu (미국): $0.375 → $0.8 (+113.3%)" in post
    assert "W1 미국 Redshift: $900 → $1,648 (+83.1%)" in post
    assert "W1 미국: Redshift > BigQuery > Snowflake > Databricks → BigQuery > Snowflake > Redshift > Databricks" in post


def test_number_check_rejects_numbers_missing_from_events(price_records, workloads):
    events = _events(price_records, workloads)
    post = render_post(events)
    check_numbers(post, events)                                       # 그대로면 통과
    with pytest.raises(ValueError, match="1,658"):
        check_numbers(post.replace("$1,648", "$1,658"), events)        # 숫자 하나를 바꾸면 게시를 막는다
