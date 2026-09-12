import datetime as dt
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import pipeline
from common.schema import write_snapshot

REPO = Path(__file__).resolve().parent.parent
TODAY = dt.date.today().isoformat()


@pytest.fixture(autouse=True)
def _no_github_output(monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)   # CI 안에서 테스트가 실제 단계 출력에 쓰지 않게 한다


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


def _approved(records, day="2000-01-01"):
    write_snapshot(records, day, "all")
    Path(f"data/raw/{day}/approved.txt").write_text("approved", encoding="utf-8")


def test_default_run_stops_after_review(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)

    out = pipeline.main([])

    assert out.name == "review.md" and out.exists()
    assert "pipeline.py --confirm" in out.read_text(encoding="utf-8")
    assert len(list(out.parent.glob("*.csv"))) == 3          # aws, azure, manual
    assert not Path("site").exists()                          # 컨펌 전에는 화면을 만들지 않는다
    events = json.loads((out.parent / "events.json").read_text(encoding="utf-8"))
    assert events["status"] == "first" and not (out.parent / "post.md").exists()


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
    assert "(미국 리전)" in html and "(서울 리전)" in html      # T1을 두 리전 모두 표시
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


def test_unchanged_run_only_records_the_check(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records)
    gh_out = tmp_path / "gh_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_out))

    out = pipeline.main([])

    assert out == Path("data/checks.csv")
    assert f"{TODAY},unchanged,2000-01-01" in out.read_text(encoding="utf-8")
    assert not Path("data/raw", TODAY).exists()                  # 변화가 없으면 스냅샷을 만들지 않는다
    assert "status=unchanged" in gh_out.read_text(encoding="utf-8")
    pipeline.main([])                                            # 같은 날 다시 실행해도 한 줄만 남는다
    assert out.read_text(encoding="utf-8").count(TODAY) == 1


def test_changed_run_writes_events_post_and_review(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
               for r in price_records])

    out = pipeline.main([])

    events = json.loads((out.parent / "events.json").read_text(encoding="utf-8"))
    assert events["status"] == "changed" and events["significant"] and events["compared_to"] == "2000-01-01"
    assert "$0.3 → $0.375 (+25.0%)" in (out.parent / "post.md").read_text(encoding="utf-8")
    assert "글 초안(E1): 있음" in out.read_text(encoding="utf-8")
    assert f"{TODAY},review,2000-01-01" in Path("data/checks.csv").read_text(encoding="utf-8")


def test_simulated_snapshot_is_marked_and_cannot_be_confirmed(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records)

    out = pipeline.main(["--simulate"])

    assert out.read_text(encoding="utf-8").startswith("> **시뮬레이션:**")
    assert not Path("data/checks.csv").exists()                  # 시뮬레이션은 매일 확인 기록에 남기지 않는다
    with pytest.raises(SystemExit, match="시뮬레이션"):
        pipeline.main(["--confirm", TODAY])
    assert not Path("data/raw", TODAY, "approved.txt").exists()


def test_dry_run_writes_nothing(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
               for r in price_records])

    events = pipeline.main(["--dry-run"])

    assert events["status"] == "changed" and events["significant"]
    assert not Path("data/raw", TODAY).exists() and not Path("data/checks.csv").exists() and not Path("site").exists()


def test_build_renders_the_latest_approved_snapshot(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    with pytest.raises(SystemExit, match="승인된 스냅샷이 없다"):
        pipeline.main(["--build"])

    _approved([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == ("redshift", "compute", "us") else r
               for r in price_records], day="2000-01-01")
    _approved(price_records, day="2000-01-02")

    out = pipeline.main(["--build"])

    html = out.read_text(encoding="utf-8")
    assert out == Path("site") / "index.html"
    assert "2000-01-02" in html                       # 가장 최근 승인 스냅샷으로 그린다
    assert 'data-delta="' in html                     # 이전 승인 스냅샷과 비교한 순위 변동을 표시한다
    assert Path("data/raw/2000-01-02/approved.txt").read_text(encoding="utf-8") == "approved"   # 승인 기록은 그대로다


def test_rerun_after_same_day_approval_is_refused(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved(price_records, day=TODAY)

    with pytest.raises(SystemExit, match="이미 승인"):
        pipeline.main([])
