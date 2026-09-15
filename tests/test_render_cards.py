import re
import struct

import pytest

from publish import browser
from publish.card_data import price_change_cards
from publish import render_cards
from publish.render_cards import REPORT, bake, check_layout, korean_font_available, render_html, visible_text
from publish.render_post import check_numbers

TYPICAL = {("redshift", "compute", "us"): 0.40}           # 5장
RANKED = {("redshift", "compute", "us"): 0.80}            # 7장: 모든 장 종류가 나온다
MANY = {(p, s, "us"): v for (p, s, v) in [                # 8장: 쪽 나눔
    ("redshift", "compute", 0.40), ("redshift", "storage", 0.03), ("bigquery", "compute", 0.07),
    ("bigquery", "storage", 0.03), ("bigquery", "scan", 7.0), ("snowflake", "compute", 3.3),
    ("databricks", "compute", 0.8)]}


def _cards(make_events, workloads, changed):
    events, rows, prev_rows = make_events(changed)
    return events, price_change_cards(events, rows, prev_rows, workloads)


def _sections(html):
    return html.split('<section class="card')[1:]


def _has_browser():
    try:
        browser.find_browser()
        return True
    except RuntimeError:
        return False


def test_no_external_requests(make_events, workloads):
    _, cards = _cards(make_events, workloads, RANKED)
    html = render_html(cards, REPORT)
    for banned in ("<img", "<link", "@import", "url(", "http://", "https://", "<script"):
        assert banned not in html
    assert "<script" in render_html(cards, REPORT, measure=True)      # 측정 스크립트는 측정 모드에만 들어간다


def test_every_card_has_the_fixed_bars(make_events, workloads):
    _, cards = _cards(make_events, workloads, RANKED)
    html = render_html(cards, REPORT)
    n = len(cards)
    assert len(_sections(html)) == n
    assert html.count("CONSUMPTION INSIGHTS") == n
    assert html.count(f'<span class="eyebrow">{REPORT}</span>') == n
    assert html.count('<span class="pill-url">eugeejo-ui.github.io/consumption-insights</span>') == n
    assert "--w:1080px" in html and "--h:1350px" in html


def test_only_the_last_card_says_end(make_events, workloads):
    _, cards = _cards(make_events, workloads, RANKED)
    sections = _sections(render_html(cards, REPORT))
    assert sum("넘기기" in s for s in sections) == len(cards) - 1
    assert '<span class="swipe">끝</span>' in sections[-1]
    assert all('<span class="swipe">끝</span>' not in s for s in sections[:-1])


def test_cover_title_breaks_before_the_accent(make_events, workloads):
    _, cards = _cards(make_events, workloads, RANKED)
    cover = _sections(render_html(cards, REPORT))[0]
    assert '월 사용료 <br><em class="accent">순위 변동</em>' in cover


def test_accent_and_page_mark_are_rendered_apart(make_events, workloads):
    _, cards = _cards(make_events, workloads, MANY)
    html = render_html(cards, REPORT)
    assert '단가 <em class="accent">변동 내역</em> <span class="page">(1/2)</span>' in html
    assert '<em class="accent">변동 내역 (1/2)' not in html


def test_chart_bars_share_one_scale_and_show_both_regions(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    chart = next(s for s in _sections(render_html(cards, REPORT)) if 'class="panel"' in s)
    assert chart.count('class="bar us"') == 4 and chart.count('class="bar seoul"') == 4
    heights = [float(h) for h in re.findall(r'class="bar (?:us|seoul)" style="height:([\d.]+)%"', chart)]
    assert max(heights) == 100.0 and heights.count(100.0) == 1           # 두 리전 전체 최댓값 기준
    assert "미국 리전" in chart and "서울 리전" in chart
    assert "$2,708" in chart and "$944" in chart


def test_banners_show_before_and_after(make_events, workloads):
    _, cards = _cards(make_events, workloads, RANKED)
    html = render_html(cards, REPORT)
    assert html.count('<div class="banner">') == 3
    assert html.count(">이전<") == 3 and html.count(">현재<") == 3
    text = visible_text(html).replace(" ", " ")
    assert "소규모 BI 대시보드 · 미국 리전" in text
    assert "BigQuery › Snowflake › Redshift › Databricks" in text


def test_closing_card_shows_the_dashboard_address(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    closing = _sections(render_html(cards, REPORT))[-1]
    assert '전체 비교는 <em class="accent">대시보드</em>에 있습니다' in closing
    assert "시나리오별 월 사용료, 서울 프리미엄, 가정과 산출 근거를 공개합니다." in closing
    assert '<p class="closing-url" data-role="url" data-lines="1">eugeejo-ui.github.io/consumption-insights</p>' in closing


def test_visible_numbers_are_all_in_events(make_events, workloads):
    events, cards = _cards(make_events, workloads, MANY)
    html = render_html(cards, REPORT)
    check_numbers(visible_text(html), events)                             # 템플릿이 숫자를 더하지 않았다
    assert "(1/2)" not in visible_text(html)                              # 쪽 표시는 장 순번이라 뺀다
    cards[0]["lead"] += " 777%"
    with pytest.raises(ValueError, match="777"):
        check_numbers(visible_text(render_html(cards, REPORT)), events)


def test_single_card_page_keeps_the_end_mark(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    last = render_html(cards, REPORT, only=len(cards))
    first = render_html(cards, REPORT, only=1)
    assert len(_sections(last)) == 1 and '<span class="swipe">끝</span>' in last
    assert len(_sections(first)) == 1 and "넘기기" in first


def test_typesetting_rules_are_in_the_css(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    html = render_html(cards, REPORT)
    assert "word-break:keep-all" in html
    assert "@page{size:1080px 1350px;margin:0}" in html
    assert '"Noto Sans CJK KR"' in html
    assert all(int(w) <= 700 for w in re.findall(r"font-weight:(\d+)", html))


def _page(**overrides):
    page = {"card": 1, "gap_top": 120, "gap_bottom": 140, "limit_right": 1032,
            "fields": [{"role": "lead", "max": 3, "lines": 2, "right": 990, "last_em": 6.5, "orphan_check": True}]}
    for key, value in overrides.items():
        if key in page:
            page[key] = value
        else:
            page["fields"][0][key] = value
    return [page]


def test_layout_problems_stop_baking():
    cards = [{"kind": "chart"}]
    assert check_layout(_page(), cards) == {"min_gap": 120, "max_right": 990, "limit_right": 1032}   # 통과하면 요약
    for overrides, message in [({"gap_bottom": 12}, "하단 알약과 겹친다"), ({"gap_top": -5}, "상단 바와 겹친다"),
                               ({"lines": 4}, "줄 수"), ({"right": 1050}, "넘친다"), ({"last_em": 1.2}, "한 음절")]:
        with pytest.raises(ValueError, match=message):
            check_layout(_page(**overrides), cards)
    check_layout(_page(last_em=1.2, orphan_check=False), cards)           # 의도된 줄바꿈은 검사하지 않는다


@pytest.mark.skipif(not (_has_browser() and korean_font_available()), reason="브라우저나 한글 글꼴이 없다")
def test_bakes_every_card_and_passes_the_layout_check(make_events, workloads, tmp_path):
    events, cards = _cards(make_events, workloads, RANKED)
    paths = bake(cards, tmp_path, REPORT, events)
    pngs = sorted(tmp_path.glob("*.png"))
    assert [p.name for p in pngs] == ["01-cover.png", "02-price.png", "03-chart.png", "04-cost.png",
                                      "05-rank.png", "06-rank.png", "07-closing.png"]
    assert all(struct.unpack(">II", p.read_bytes()[16:24]) == (1080, 1350) for p in pngs)
    pdf = (tmp_path / "cards.pdf").read_bytes()
    assert len(re.findall(rb"/Type\s*/Page(?![s])", pdf)) == len(cards)
    assert set(paths) == {tmp_path / "cards.html", tmp_path / "cards.pdf", *pngs}


def test_bake_refuses_without_a_korean_font(make_events, workloads, tmp_path, monkeypatch):
    """CI 서버에는 한글 글꼴이 없다. 그대로 구우면 실패하지 않고 두부 글자 카드가 만들어진다."""
    events, cards = _cards(make_events, workloads, TYPICAL)
    monkeypatch.setattr(render_cards, "korean_font_available", lambda: False)

    def must_not_run(*args, **kwargs):
        raise AssertionError("글꼴이 없으면 브라우저를 부르지 않는다")

    monkeypatch.setattr(browser, "dump_dom", must_not_run)
    monkeypatch.setattr(browser, "screenshot", must_not_run)
    with pytest.raises(RuntimeError, match="한글 글꼴"):
        bake(cards, tmp_path, REPORT, events)
    assert not list(tmp_path.iterdir())
