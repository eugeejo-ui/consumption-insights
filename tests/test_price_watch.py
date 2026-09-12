import json
from pathlib import Path

from detect.price_watch import (MANUAL_CHECK_DAYS, bigquery_issue_body, check_bigquery, fingerprint, reminder_body,
                                save_fingerprint, stale_manual_prices)

PAGE = '<script nonce="{nonce}">x</script><td>$6.25</td><td>$0.0765</td><td>0.000054795</td>'


def test_fingerprint_ignores_nonce_but_catches_price_change():
    assert fingerprint(PAGE.format(nonce="aaa"))["hash"] == fingerprint(PAGE.format(nonce="bbb"))["hash"]
    assert fingerprint(PAGE.format(nonce="aaa"))["hash"] != fingerprint(PAGE.format(nonce="aaa").replace("6.25", "6.50"))["hash"]
    assert fingerprint(PAGE.format(nonce="aaa"))["tokens"] == 3


def test_first_run_creates_the_baseline_without_alerting(tmp_path):
    path = tmp_path / "fingerprint.json"
    result = check_bigquery("2026-09-12", fetch=lambda url: PAGE.format(nonce="aaa"), path=path)

    assert result["first"] and not result["changed"]
    save_fingerprint(result, path)
    assert json.loads(path.read_text(encoding="utf-8"))["checked_on"] == "2026-09-12"


def test_change_is_detected_against_the_saved_fingerprint(tmp_path):
    path = tmp_path / "fingerprint.json"
    save_fingerprint(check_bigquery("2026-09-12", fetch=lambda url: PAGE.format(nonce="aaa"), path=path), path)

    same = check_bigquery("2026-09-13", fetch=lambda url: PAGE.format(nonce="ccc"), path=path)
    changed = check_bigquery("2026-09-13", fetch=lambda url: PAGE.format(nonce="aaa").replace("6.25", "6.50"), path=path)

    assert not same["changed"]
    assert changed["changed"] and changed["before"]["hash"] != changed["after"]["hash"]
    assert "bigquery_prices.csv" in bigquery_issue_body(changed)


def test_old_manual_tables_are_listed_for_a_human_check(tmp_path):
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "snowflake_prices.csv").write_text(
        "platform,service,sku,region,unit,price_usd,source,confirmed_on\n"
        "snowflake,compute,enterprise-credit,us,credit,3.0,https://example.invalid,2026-01-01\n", encoding="utf-8")
    (manual / "bigquery_prices.csv").write_text(
        "platform,service,sku,region,unit,price_usd,source,confirmed_on\n"
        "bigquery,scan,on-demand,us,TiB,6.25,https://example.invalid,2026-09-01\n", encoding="utf-8")

    stale = stale_manual_prices("2026-09-12", manual_dir=manual)

    assert [item["platform"] for item in stale] == ["snowflake"]        # bigquery는 11일 전이라 아직 아니다
    assert stale[0]["days"] >= MANUAL_CHECK_DAYS
    body = reminder_body(stale, "2026-09-12")
    assert "snowflake" in body and "CreditConsumptionTable.pdf" in body and "- [ ]" in body
