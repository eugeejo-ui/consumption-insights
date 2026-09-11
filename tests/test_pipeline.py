import shutil
from pathlib import Path

import pytest

import pipeline
from common.schema import write_snapshot

REPO = Path(__file__).resolve().parent.parent


def _copy_config(tmp_path):
    (tmp_path / "data" / "manual").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "data" / "manual" / "workloads.yaml", tmp_path / "data" / "manual" / "workloads.yaml")
    (tmp_path / "config").mkdir(exist_ok=True)
    shutil.copy(REPO / "config" / "thresholds.yaml", tmp_path / "config" / "thresholds.yaml")


def _fake_collectors(monkeypatch, price_records):
    def by(*platforms):
        return [r for r in price_records if r.platform in platforms]

    monkeypatch.setattr(pipeline.aws_prices, "collect", lambda day: by("redshift"))
    monkeypatch.setattr(pipeline.azure_prices, "collect", lambda day: by("databricks"))
    monkeypatch.setattr(pipeline.manual_prices, "collect", lambda: by("snowflake", "bigquery"))


def test_default_run_stops_after_review(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)

    out = pipeline.main([])

    assert out.name == "review.md" and out.exists()
    assert "pipeline.py --confirm" in out.read_text(encoding="utf-8")
    assert len(list(out.parent.glob("*.csv"))) == 3          # aws, azure, manual
    assert not Path("site").exists()                          # 컨펌 전에는 화면을 만들지 않는다


def test_confirm_requires_review(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    write_snapshot(price_records, "2026-09-11", "all")

    with pytest.raises(SystemExit):                            # 검토 보고서가 없는 스냅샷은 반영하지 않는다
        pipeline.main(["--confirm", "2026-09-11"])
    assert not Path("site").exists()

    Path("data/raw/2026-09-11/review.md").write_text("reviewed", encoding="utf-8")
    out = pipeline.main(["--confirm", "2026-09-11"])

    html = out.read_text(encoding="utf-8")
    assert out == Path("site") / "index.html"
    assert "(미국)" in html and "(서울)" in html               # T1을 두 리전 모두 표시
    assert Path("data/raw/2026-09-11/approved.txt").exists()


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
