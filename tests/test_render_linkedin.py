from pathlib import Path

import pytest

from publish.card_data import price_item
from publish.render_linkedin import DASHBOARD_URL, MAX_CHARS, render_intro_post, render_linkedin
from publish.render_post import NUMBER

TYPICAL = {("redshift", "compute", "us"): 0.40}           # 단가 1건 · 월 비용 3건 · 순위 0건
RANKED = {("redshift", "compute", "us"): 0.80}            # 순위 3건
MANY = {(p, s, "us"): v for (p, s, v) in [                # 단가 7건
    ("redshift", "compute", 0.40), ("redshift", "storage", 0.03), ("bigquery", "compute", 0.07),
    ("bigquery", "storage", 0.03), ("bigquery", "scan", 7.0), ("snowflake", "compute", 3.3),
    ("databricks", "compute", 0.8)]}

HASHTAGS = "#데이터플랫폼 #클라우드비용 #FinOps #Snowflake #Databricks #BigQuery #Redshift"
TOP_LINE = "월 비용 변동 폭이 가장 큰 조합은 소규모 BI 대시보드 · 미국 리전입니다."
RANK_LINE = "월 비용이 낮은 순서가 바뀌었습니다."


def test_post_lists_every_price_change_and_the_dashboard_link(make_events, workloads):
    events, _, _ = make_events(MANY)
    text = render_linkedin(events, workloads)
    assert text.startswith("데이터 플랫폼 월 비용 변동 · 2026-09-13\n\n직전 승인 가격(2026-09-11) 대비 단가 7건이 바뀌었습니다.\n")
    for change in events["price_changes"]:                    # 규칙 18: 한 줄도 빠뜨리지 않는다
        item = price_item(change)
        assert f"▪ {item['strong']} {item['rest']}\n" in text
    assert f"\n{DASHBOARD_URL}\n" in text
    assert text.rstrip("\n").endswith(HASHTAGS)
    assert "외 " not in text


def test_conditional_lines_follow_the_events(make_events, workloads):
    typical, _, _ = make_events(TYPICAL)
    text = render_linkedin(typical, workloads)
    assert TOP_LINE in text and RANK_LINE not in text

    ranked, _, _ = make_events(RANKED)
    assert RANK_LINE in render_linkedin(ranked, workloads)

    ranked["cost_changes"] = []                                # 순위만 바뀐 날에는 변동 폭 줄이 없다
    text = render_linkedin(ranked, workloads)
    assert "변동 폭" not in text and RANK_LINE in text


def test_post_over_3000_chars_stops(make_events, workloads):
    events, _, _ = make_events(TYPICAL)
    change = events["price_changes"][0]
    events["price_changes"] = [dict(change) for _ in range(80)]
    with pytest.raises(ValueError, match="3,000자"):
        render_linkedin(events, workloads)


def test_a_number_not_in_events_is_rejected(make_events, workloads):
    workloads["scenarios"]["W1"]["name"] = "소규모 BI 대시보드 777"
    events, _, _ = make_events(TYPICAL)
    with pytest.raises(ValueError, match="777"):
        render_linkedin(events, workloads)


INTRO_FACTS = {"region_costs": [[900, 1032, 14.7], [1693, 2167, 28.1], [1550, 2032, 31.1], [2056, 2708, 31.7]]}


def test_intro_post_matches_the_script():
    """소개 게시문(스크립트 2절)은 대시보드 주소와 리전 최대 차이만 채운다. events.json 없이 승인 스냅샷으로 만든다."""
    script = (Path(__file__).resolve().parent.parent / "docs" / "scripts" / "linkedin-post-script.md").read_text(encoding="utf-8")
    block = script.split("## 2. 소개 게시문")[1].split("```\n")[1]
    text = render_intro_post(INTRO_FACTS)
    assert text == block.replace("{대시보드 주소}", DASHBOARD_URL).replace("{리전 최대 차이}", "31.7%")
    assert NUMBER.findall(text) == ["31.7"] and len(text) <= MAX_CHARS
    # 첫 게시물은 문제의식과 측정 결과로 연다(2026-09-16). LinkedIn은 첫 두 줄만 펼쳐 보인다.
    assert text.startswith("같은 워크로드를 돌려도 플랫폼마다 월 비용이 두 배 넘게 차이가 납니다.\n"
                           "같은 플랫폼이라도 서울 리전은 미국 리전보다 월 비용이 최대 31.7% 높습니다.\n")
    assert "매일" not in text and "어려웠습니다" not in text


def test_intro_post_carries_the_largest_region_gap():
    """리전 차이는 카드와 같은 승인 스냅샷에서 온다. 게시문에 숫자를 적어 두지 않는다(3-1절)."""
    text = render_intro_post({"region_costs": [[900, 1000, 11.1], [1000, 1234, 23.4]]})
    assert "월 비용이 최대 23.4% 높습니다." in text and "31.7" not in text


def test_intro_post_stops_when_seoul_is_never_dearer():
    """서울 리전이 더 비싼 워크로드가 없으면 `최대 … 높습니다`가 거짓이 된다. 생성을 멈춘다(3-1절)."""
    with pytest.raises(ValueError, match="더 비싼"):
        render_intro_post({"region_costs": [[900, 880, -2.2], [1000, 1000, 0.0]]})
