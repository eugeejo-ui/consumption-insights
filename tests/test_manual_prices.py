import csv
from pathlib import Path

import pytest

from collectors.manual_prices import collect, load_manual

HEADER = "platform,service,sku,region,unit,price_usd,source,confirmed_on\n"
REPO = Path(__file__).resolve().parent.parent


def test_loads_confirmed_rows(tmp_path):
    p = tmp_path / "snowflake_prices.csv"
    p.write_text(HEADER + "snowflake,compute,enterprise-credit,us,credit,3.00,src,2026-09-12\n", encoding="utf-8")
    [r] = load_manual(p)
    assert r.price_usd == 3.0 and r.fetched_at == "2026-09-12"


def test_refuses_unconfirmed_rows(tmp_path):
    p = tmp_path / "snowflake_prices.csv"
    p.write_text(HEADER + "snowflake,compute,enterprise-credit,us,credit,3.00,src,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="confirmed_on"):
        load_manual(p)


def test_collect_reads_all_price_files(tmp_path):
    for name, platform in [("snowflake_prices.csv", "snowflake"), ("bigquery_prices.csv", "bigquery")]:
        (tmp_path / name).write_text(HEADER + f"{platform},compute,x,us,credit,1.0,src,2026-09-12\n", encoding="utf-8")
    (tmp_path / "workloads.yaml").write_text("ignored: true\n", encoding="utf-8")
    assert {r.platform for r in collect(tmp_path)} == {"snowflake", "bigquery"}


def test_repo_manual_files_have_expected_columns():
    for path in (REPO / "data" / "manual").glob("*_prices.csv"):
        with path.open(newline="", encoding="utf-8") as f:
            assert next(csv.reader(f)) == HEADER.strip().split(",")
