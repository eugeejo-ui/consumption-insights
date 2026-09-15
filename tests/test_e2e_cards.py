"""승인 경로 종단 테스트(Phase 3 Task 9). 시뮬레이션 스냅샷은 설계상 승인되지 않아 CI에서 머지로 끝까지 볼 수 없다.
가짜 수집기로 시뮬레이션 표시가 없는 변동을 넣고, 실제 브라우저로 굽고, 승인하고, 사이트를 빌드한다.
브라우저나 한글 글꼴이 없으면 건너뛴다(게시 워크플로에는 글꼴이 없다). 네트워크는 쓰지 않는다."""
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import pipeline
from common.schema import write_snapshot
from publish import browser
from publish.render_cards import korean_font_available

REPO = Path(__file__).resolve().parent.parent
CHANGED = ("redshift", "compute", "us")                     # 승인 0.30 → 오늘 0.375: 월 사용료 ±1% 이상(E1)


def _has_browser():
    try:
        browser.find_browser()
        return True
    except RuntimeError:
        return False


@pytest.mark.skipif(not (_has_browser() and korean_font_available()), reason="브라우저나 한글 글꼴이 없다")
def test_approved_change_publishes_cards_that_match_the_dashboard(tmp_path, monkeypatch, price_records):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    for rel in ("data/manual/workloads.yaml", "config/thresholds.yaml"):
        Path(rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, rel)
    write_snapshot([replace(r, price_usd=0.30) if (r.platform, r.service, r.region) == CHANGED else r
                    for r in price_records], "2000-01-01", "all")
    Path("data/raw/2000-01-01/approved.txt").write_text("approved", encoding="utf-8")

    def by(*platforms):
        return [r for r in price_records if r.platform in platforms]

    monkeypatch.setattr(pipeline.aws_prices, "collect", lambda day: by("redshift"))
    monkeypatch.setattr(pipeline.azure_prices, "collect", lambda day: by("databricks"))
    monkeypatch.setattr(pipeline.manual_prices, "collect", lambda: by("snowflake", "bigquery"))

    # 1단계: 검토 자료와 함께 카드를 실제로 굽는다
    folder = pipeline.main([]).parent
    cards = folder / "cards"
    pngs = sorted(cards.glob("[0-9][0-9]-*.png"))
    assert not (folder / "card-errors.txt").exists()
    assert [p.name[3:] for p in (pngs[0], pngs[-1])] == ["cover.png", "closing.png"] and len(pngs) >= 5
    assert (cards / "cards.pdf").exists() and (folder / "linkedin.md").exists()

    # 2단계: 승인(= 검토 PR 머지 뒤 게시 워크플로의 --confirm). 승인된 날의 카드만 사이트에 올라간다
    index = pipeline.main(["--confirm", folder.name])
    published = Path("site/cards") / folder.name
    for original in [*pngs, cards / "cards.pdf", cards / "cards.html", folder / "linkedin.md"]:
        assert (published / original.name).read_bytes() == original.read_bytes(), original.name

    # 카드 차트의 금액이 같은 날 대시보드에 그대로 있다(카드와 화면이 같은 계산 결과를 쓴다)
    chart = json.loads((folder / "events.json").read_text(encoding="utf-8"))["display"]["chart"]
    html = index.read_text(encoding="utf-8")
    amounts = [amount for region in ("us", "seoul") for amount in chart[region].values()]
    assert len(amounts) == 8
    missing = [f"${amount:,}" for amount in amounts if f"${amount:,}" not in html]
    assert not missing, missing
