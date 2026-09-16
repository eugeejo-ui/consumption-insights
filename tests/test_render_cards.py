import json
import re
import struct

import pytest

from model.tco import CostRow
from publish import browser
from publish.card_data import intro_cards, price_change_cards
from publish import render_cards
from publish.render_cards import (INTRO, REPORT, bake, check_layout, korean_font_available, pdf_pages_html, render_html,
                                  visible_text)
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
    assert "워크로드별 월 사용료, 리전별 가격 차이, 계산 가정을 공개합니다." in closing
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


def _intro_result():
    rows = [CostRow(scenario="W1", platform=platform, region=region,
                    compute_usd=900 + n * 500 + (100 if region == "seoul" else 0), storage_usd=0)
            for region in ("us", "seoul")
            for n, platform in enumerate(("redshift", "snowflake", "bigquery", "databricks"))]
    premiums = [{"platform": "databricks", "service": "compute", "us": 0.7, "seoul": 0.95, "premium_pct": 35.7},
                {"platform": "redshift", "service": "storage", "us": 0.024, "seoul": 0.0261, "premium_pct": 8.8}]
    return {"rows": rows, "premiums": premiums,
            "workloads": {"storage_gb": 10000,
                          "scenarios": {"W1": {"name": "소규모 BI 대시보드", "hours_per_month": 220}}}}


def test_chips_and_flow_render_with_layout_fields():
    cards, _ = intro_cards(_intro_result(), "2026-09-11")
    html = render_html(cards, INTRO, measure=True)
    chips, flow = _sections(html)[1], _sections(html)[2]
    assert '가격표만으로는 <br><em class="accent">비교되지 않습니다</em>' in chips   # 강조 구절이 두 줄로 갈라지지 않는다
    assert "<br>" not in flow.split("</h2>")[0]                                 # 나머지 장의 제목은 자연 줄바꿈
    assert chips.count('data-role="chip" data-lines="1"') == 8                 # 플랫폼 이름 4 + 과금 단위 4
    assert flow.count('data-role="step" data-lines="1"') == 4
    assert flow.count(" stop") == 1 and "검토 요청에서 정지" in flow.split(" stop")[1].split("</li>")[0]
    assert 'class="lead"' in chips and 'class="lead"' not in flow               # 리드가 없는 장에 빈 리드를 두지 않는다
    assert all(section.count('class="note"') == n for section, n in ((chips, 1), (flow, 2), (_sections(html)[3], 3)))
    assert html.index('"Noto Sans KR"') < html.index('"Malgun Gothic"')        # D22: 로컬도 CI와 같은 Noto 계열로 굽는다


def test_the_basis_line_is_smaller_than_the_notes():
    """비교 기준 줄은 각주 아래에 각주보다 작은 글자로 한 줄 들어간다(2026-09-16 사용자 지시)."""
    cards, _ = intro_cards(_intro_result(), "2026-09-11")
    html = render_html(cards, INTRO, measure=True)
    result = _sections(html)[3]
    assert result.count('<p class="basis" data-role="basis" data-lines="1">') == 1
    assert "비교 기준: 소형 컴퓨트 월 220시간 · 스토리지 10TB(압축 후)" in result
    assert result.index('class="note"') < result.index('class="basis"')        # 각주 아래에 둔다
    sizes = {name: int(re.search(rf"\.{name}{{font-size:(\d+)px", html).group(1)) for name in ("note", "basis")}
    assert sizes["basis"] < sizes["note"]
    with_basis = [n for n, section in enumerate(_sections(html)) if 'class="basis"' in section]
    assert with_basis == [3, 5]                        # 현재 순위 장과 서울 리전 월 사용료 장에만 둔다


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
    assert len(re.findall(rb"/Subtype\s*/Image", pdf)) == len(cards)     # D23: 쪽마다 그 장의 PNG
    assert b"/SMask" not in pdf                                          # 강조 문구 마스크의 테두리선이 생기지 않는다
    assert set(paths) == {tmp_path / "cards.html", tmp_path / "cards.pdf", *pngs}


def test_pdf_pages_show_each_png_on_its_own_full_page(tmp_path):
    pngs = [tmp_path / "01-cover.png", tmp_path / "02-price.png", tmp_path / "03-closing.png"]
    html = pdf_pages_html(pngs)
    assert "@page{size:1080px 1350px;margin:0}" in html
    assert "<title>cards</title>" in html          # PDF 제목이 임시 파일 이름이 되지 않는다(이전 PDF와 같은 제목)
    assert html.count("<img") == len(pngs)
    positions = [html.index(f'src="{p.resolve().as_uri()}"') for p in pngs]   # 절대 파일 주소로, 장 순서대로
    assert positions == sorted(positions)


def test_bake_prints_the_pdf_from_the_baked_pngs(make_events, workloads, tmp_path, monkeypatch):
    """PDF는 cards.html이 아니라 구운 PNG로 만든다(D23). 이미지 수가 다르거나 마스크가 남으면 멈춘다."""
    events, cards = _cards(make_events, workloads, TYPICAL)
    report = [{**_page()[0], "card": n} for n in range(1, len(cards) + 1)]
    printed = []

    def fake_screenshot(page, out, width, height):
        out.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(8) + struct.pack(">II", width, height) + bytes(8))
        return out

    def fake_print(pdf_body):
        def print_pdf(html, out):
            printed.append(html.read_text(encoding="utf-8"))
            out.write_bytes(pdf_body)
            return out
        return print_pdf

    monkeypatch.setattr(render_cards, "korean_font_available", lambda: True)
    monkeypatch.setattr(browser, "dump_dom", lambda html: f'<pre id="layout-report">{json.dumps(report)}</pre>')
    monkeypatch.setattr(browser, "screenshot", fake_screenshot)
    n = len(cards)
    monkeypatch.setattr(browser, "print_pdf", fake_print(b"/Type /Page\n/Subtype /Image\n" * n))
    bake(cards, tmp_path, REPORT, events)
    pngs = sorted(tmp_path.glob("*.png"))
    assert printed[0] == pdf_pages_html(pngs) and "cards.html" not in printed[0]

    for body, message in [(b"/Type /Page\n/Subtype /Image\n" * (n - 1) + b"/Type /Page\n", "이미지"),
                          (b"/Type /Page\n/Subtype /Image\n" * n + b"/SMask 9 0 R", "마스크")]:
        monkeypatch.setattr(browser, "print_pdf", fake_print(body))
        with pytest.raises(ValueError, match=message):
            bake(cards, tmp_path, REPORT, events)


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
