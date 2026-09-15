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


@pytest.fixture(autouse=True)
def _no_real_bake(monkeypatch):
    monkeypatch.setattr(pipeline, "bake", lambda *args, **kwargs: [])   # E1 테스트가 실제 브라우저를 부르지 않게 한다


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


# ── Phase 3 Task 5: 카드와 게시문 연결 ─────────────────────────────────────────

E1_BASE = ("redshift", "compute", "us")                          # 승인 0.30 → 오늘 0.375: E1


def _e1_approved(price_records):
    _approved([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == E1_BASE else r
               for r in price_records])


def _fake_bake(monkeypatch, fail=None):
    """브라우저 없이 검증하려고 굽기를 바꾼다. 받은 인자를 기록하고 파일을 만든다."""
    calls = []

    def bake(cards, out_dir, eyebrow, events):
        calls.append({"cards": cards, "out_dir": Path(out_dir), "eyebrow": eyebrow})
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if fail:
            (out_dir / "cards.html").write_text("partial", encoding="utf-8")   # 도중에 실패한 상황
            raise fail
        pngs = []
        for n in range(1, len(cards) + 1):
            pngs.append(out_dir / f"{n:02d}-card.png")
            pngs[-1].write_bytes(b"png")
        (out_dir / "cards.html").write_text("cards", encoding="utf-8")
        (out_dir / "cards.pdf").write_bytes(b"pdf")
        return [out_dir / "cards.html", *pngs, out_dir / "cards.pdf"]

    monkeypatch.setattr(pipeline, "bake", bake)
    return calls


def _gh_output(tmp_path, monkeypatch):
    path = tmp_path / "gh_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(path))
    return path


def test_e1_run_writes_cards_and_the_linkedin_post(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _e1_approved(price_records)
    calls = _fake_bake(monkeypatch)
    gh_out = _gh_output(tmp_path, monkeypatch)

    folder = pipeline.main([]).parent

    assert len(calls) == 1
    assert calls[0]["out_dir"] == folder / "cards" and calls[0]["eyebrow"] == "가격 변동 리포트"
    assert calls[0]["cards"][-1]["kind"] == "closing"
    assert (folder / "linkedin.md").read_text(encoding="utf-8").startswith(f"데이터 플랫폼 월 비용 변동 · {TODAY}")
    events = json.loads((folder / "events.json").read_text(encoding="utf-8"))
    assert events["display"]["price_change_count"] == 1 and "chart" in events["display"]   # 카드 데이터 뒤에 썼다
    assert f"cards=ok\ncard_count={len(calls[0]['cards'])}\n" in gh_out.read_text(encoding="utf-8")
    assert not (folder / "card-errors.txt").exists()


def test_non_e1_run_makes_no_cards_and_clears_stale_ones(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _approved([replace(r, price_usd=0.02401) if (r.platform, r.service, r.region) == ("redshift", "storage", "us") else r
               for r in price_records])                          # 단가는 바뀌었지만 월 비용 변동이 기준 미만
    calls = _fake_bake(monkeypatch)
    gh_out = _gh_output(tmp_path, monkeypatch)
    stale = Path("data/raw", TODAY)                              # 같은 날 앞선 실행이 남긴 카드
    (stale / "cards").mkdir(parents=True)
    (stale / "cards" / "01-cover.png").write_bytes(b"old")
    (stale / "linkedin.md").write_text("old", encoding="utf-8")
    (stale / "card-errors.txt").write_text("old", encoding="utf-8")

    folder = pipeline.main([]).parent

    events = json.loads((folder / "events.json").read_text(encoding="utf-8"))
    assert events["status"] == "changed" and not events["significant"]
    assert calls == []
    assert not (folder / "cards").exists() and not (folder / "linkedin.md").exists()
    assert not (folder / "card-errors.txt").exists()
    assert "cards=skipped\ncard_count=0\n" in gh_out.read_text(encoding="utf-8")


def test_card_failure_keeps_the_review_and_records_the_error(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _e1_approved(price_records)
    _fake_bake(monkeypatch, fail=RuntimeError("한글 글꼴이 없다"))
    gh_out = _gh_output(tmp_path, monkeypatch)

    out = pipeline.main([])                                       # 카드가 실패해도 1단계는 정상 종료한다

    folder = out.parent
    for name in ("review.md", "events.json", "post.md", "linkedin.md"):
        assert (folder / name).exists()
    assert "굽기: 한글 글꼴이 없다" in (folder / "card-errors.txt").read_text(encoding="utf-8")
    assert not (folder / "cards").exists()                      # 반쪽 카드를 남기지 않는다
    assert "cards=failed\ncard_count=0\n" in gh_out.read_text(encoding="utf-8")


def test_linkedin_failure_is_recorded_and_cards_still_bake(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _e1_approved(price_records)
    calls = _fake_bake(monkeypatch)

    def too_long(events, workloads):
        raise ValueError("게시문이 3,100자라 LinkedIn 한도 3,000자를 넘는다")

    monkeypatch.setattr(pipeline, "render_linkedin", too_long)

    folder = pipeline.main([]).parent

    assert len(calls) == 1 and (folder / "cards" / "cards.pdf").exists()
    assert not (folder / "linkedin.md").exists()
    assert "게시문: 게시문이 3,100자라" in (folder / "card-errors.txt").read_text(encoding="utf-8")


def test_cards_command_rebuilds_without_touching_approval(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _fake_collectors(monkeypatch, price_records)
    _e1_approved(price_records)
    calls = _fake_bake(monkeypatch)
    folder = pipeline.main([]).parent
    (folder / "approved.txt").write_text("approved", encoding="utf-8")
    shutil.rmtree(folder / "cards")
    (folder / "linkedin.md").unlink()

    out = pipeline.main(["--cards", TODAY])

    assert out == folder / "cards" and len(calls) == 2
    assert (folder / "cards" / "cards.pdf").exists() and (folder / "linkedin.md").exists()
    assert (folder / "approved.txt").read_text(encoding="utf-8") == "approved"


def test_cards_command_refuses_a_day_without_an_e1_event(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _approved(price_records)
    with pytest.raises(SystemExit, match="events.json"):
        pipeline.main(["--cards", "2000-01-01"])
    Path("data/raw/2000-01-01/events.json").write_text(json.dumps({"significant": False}), encoding="utf-8")
    with pytest.raises(SystemExit, match="E1"):
        pipeline.main(["--cards", "2000-01-01"])


def test_site_build_publishes_only_approved_cards(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _approved(price_records, day="2000-01-01")
    write_snapshot(price_records, "2000-01-02", "all")           # 승인 기록이 없는 날(시뮬레이션 포함)
    for day in ("2000-01-01", "2000-01-02"):
        Path("data/raw", day, "cards").mkdir(parents=True)
        Path("data/raw", day, "cards", "01-cover.png").write_bytes(b"png")
        Path("data/raw", day, "linkedin.md").write_text("post", encoding="utf-8")

    pipeline.main(["--build"])

    assert Path("site/cards/2000-01-01/01-cover.png").exists()
    assert Path("site/cards/2000-01-01/linkedin.md").read_text(encoding="utf-8") == "post"
    assert not Path("site/cards/2000-01-02").exists()


def test_build_writes_the_approved_day_to_the_step_output(tmp_path, monkeypatch, price_records):
    """게시 워크플로는 이 값을 시트 적재에 넘긴다. 출력 문장을 파싱하던 방식은 문장이 바뀌자 조용히 깨졌다."""
    monkeypatch.chdir(tmp_path)
    _copy_config(tmp_path)
    _approved(price_records, day="2000-01-01")
    gh_out = _gh_output(tmp_path, monkeypatch)

    pipeline.main(["--build"])

    assert "day=2000-01-01\n" in gh_out.read_text(encoding="utf-8")
