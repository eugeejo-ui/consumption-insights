import shutil
from pathlib import Path

import pytest

import pipeline
from common.schema import write_snapshot

REPO = Path(__file__).resolve().parent.parent


def test_offline_pipeline_builds_site(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    write_snapshot(price_records, "2026-09-11", "all")
    (tmp_path / "data" / "manual").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "data" / "manual" / "workloads.yaml", tmp_path / "data" / "manual" / "workloads.yaml")
    (tmp_path / "config").mkdir()
    shutil.copy(REPO / "config" / "thresholds.yaml", tmp_path / "config" / "thresholds.yaml")

    out = pipeline.main(["--offline", "2026-09-11"])

    assert out == Path("site") / "index.html"
    html = out.read_text(encoding="utf-8")
    assert "W3" in html
    assert "(미국)" in html and "(서울)" in html   # T1을 두 리전 모두 표시


def test_live_mode_writes_nothing_when_manual_gate_fails(tmp_path, monkeypatch, price_records):
    # 수집기 셋이 모두 성공한 뒤에만 스냅샷을 쓴다. 수동 가격표 게이트에서 멈추면 반쪽 스냅샷이 남으면 안 된다.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline.aws_prices, "collect", lambda day: [r for r in price_records if r.platform == "redshift"])
    monkeypatch.setattr(pipeline.azure_prices, "collect", lambda day: [r for r in price_records if r.platform == "databricks"])

    def gate():
        raise ValueError("confirmed_on is empty")

    monkeypatch.setattr(pipeline.manual_prices, "collect", gate)

    with pytest.raises(ValueError, match="confirmed_on"):
        pipeline.main([])
    assert not (tmp_path / "data" / "raw").exists()
