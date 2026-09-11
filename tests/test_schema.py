import pytest

from common.schema import PriceRecord, read_snapshot, write_snapshot


def rec(**kw):
    base = dict(platform="redshift", service="compute", sku="serverless-rpu", region="us",
                unit="RPU-hour", price_usd=0.375, source="https://example", fetched_at="2026-09-11")
    base.update(kw)
    return PriceRecord(**base)


def test_rejects_unknown_region():
    with pytest.raises(ValueError):
        rec(region="eu")


def test_rejects_zero_price():
    with pytest.raises(ValueError):
        rec(price_usd=0)


def test_roundtrip_is_sorted_and_lossless(tmp_path):
    path = write_snapshot([rec(region="seoul", price_usd=0.438), rec()], "2026-09-11", "aws", root=tmp_path)
    assert path == tmp_path / "2026-09-11" / "aws.csv"
    back = read_snapshot(path)
    assert [r.region for r in back] == ["seoul", "us"]
    assert back[0].price_usd == 0.438
