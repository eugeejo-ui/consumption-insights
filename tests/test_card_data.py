import re
from pathlib import Path

import pytest

from publish.card_data import (card_text, check_complete, closing_card, cover_title, intro_cards, price_change_cards,
                               price_item, price_label)
from publish.render_post import check_numbers

TYPICAL = {("redshift", "compute", "us"): 0.40}           # 단가 1건 · 월 사용료 3건 · 순위 0건
RANKED = {("redshift", "compute", "us"): 0.80}            # 단가 1건 · 월 사용료 3건 · 순위 3건
MANY = {(p, s, "us"): v for (p, s, v) in [                # 단가 7건 · 월 사용료 12건 · 순위 2건
    ("redshift", "compute", 0.40), ("redshift", "storage", 0.03), ("bigquery", "compute", 0.07),
    ("bigquery", "storage", 0.03), ("bigquery", "scan", 7.0), ("snowflake", "compute", 3.3),
    ("databricks", "compute", 0.8)]}


def _cards(make_events, workloads, changed):
    events, rows, prev_rows = make_events(changed)
    return events, price_change_cards(events, rows, prev_rows, workloads)


def _title(card):
    return "".join(part["text"] for part in card["title"])


def test_cover_title_follows_the_three_conditions():
    assert cover_title({"rank_changes": [{}], "cost_changes": [{}]}) == [
        {"text": "월 사용료 ", "accent": False}, {"text": "순위 변동", "accent": True}]
    assert cover_title({"rank_changes": [], "cost_changes": [{}]}) == [
        {"text": "월 사용료 ", "accent": False}, {"text": "변동", "accent": True}]
    assert cover_title({"rank_changes": [], "cost_changes": []}) == [
        {"text": "단가 ", "accent": False}, {"text": "변동", "accent": True}]


def test_five_cards_on_a_typical_day(make_events, workloads):
    events, cards = _cards(make_events, workloads, TYPICAL)
    assert [(c["kind"], c.get("group")) for c in cards] == [
        ("cover", None), ("bullets", "price"), ("chart", None), ("bullets", "cost"), ("closing", None)]
    assert events["display"]["price_change_count"] == 1
    assert cards[0]["subtitle"] == "2026-09-13 · 단가 1건"
    assert cards[0]["lead"] == "직전 승인 가격(2026-09-11) 대비 변동 사항입니다."
    closing = cards[-1]
    assert _title(closing) == "전체 비교는 대시보드에 있습니다"
    assert [p["text"] for p in closing["title"] if p["accent"]] == ["대시보드"]
    assert closing["lead"] == "시나리오별 월 사용료, 서울 프리미엄, 가정과 산출 근거를 공개합니다."
    assert closing["url"] == "eugeejo-ui.github.io/consumption-insights"


def test_rank_banners_are_split_two_per_card(make_events, workloads):
    events, cards = _cards(make_events, workloads, RANKED)
    assert len(events["rank_changes"]) == 3
    ranks = [c for c in cards if c["kind"] == "banners"]
    assert [len(c["banners"]) for c in ranks] == [2, 1]
    assert [c["page"] for c in ranks] == ["(1/2)", "(2/2)"]
    assert len(cards) == 7 and cards[-1]["kind"] == "closing"
    assert ranks[0]["banners"][0] == {"label": "소규모 BI 대시보드 · 미국 리전",
                                      "before": "Redshift › BigQuery › Snowflake › Databricks",
                                      "after": "BigQuery › Snowflake › Redshift › Databricks"}


def test_every_item_is_carried_across_pages(make_events, workloads):
    """규칙 18: 항목을 생략하지 않는다. 한 장에 담기지 않으면 같은 종류의 장을 늘린다."""
    events, cards = _cards(make_events, workloads, MANY)
    prices = [c for c in cards if c.get("group") == "price"]
    costs = [c for c in cards if c.get("group") == "cost"]
    ranks = [c for c in cards if c["kind"] == "banners"]
    assert [len(c["items"]) for c in prices] == [5, 2]
    assert [len(c["items"]) for c in costs] == [6, 6]
    assert [len(c["banners"]) for c in ranks] == [2]
    assert [c["page"] for c in prices] == ["(1/2)", "(2/2)"]
    assert ranks[0]["page"] is None                            # 한 장뿐이면 쪽 표시를 붙이지 않는다
    assert len(cards) == 8
    assert "외 " not in card_text(cards)


def test_missing_item_stops_generation(make_events, workloads):
    events, cards = _cards(make_events, workloads, TYPICAL)
    cards[1]["items"] = cards[1]["items"][:-1]
    with pytest.raises(ValueError, match="누락"):
        check_complete(cards, events)


def test_chart_card_always_shows_both_regions(make_events, workloads):
    """D18: 변동이 미국 리전에만 있어도 차트에는 서울 리전이 함께 실린다."""
    events, cards = _cards(make_events, workloads, TYPICAL)
    chart = next(c for c in cards if c["kind"] == "chart")
    assert list(chart["series"]) == ["us", "seoul"]
    assert all(list(chart["series"][r]) == ["snowflake", "databricks", "redshift", "bigquery"] for r in ("us", "seoul"))
    assert chart["series"]["us"]["redshift"] == 944                     # 바뀐 뒤 금액
    assert events["display"]["chart"] == {"scenario": "W1", **chart["series"]}
    assert chart["notes"] == ["금액은 벤더 공시 통화인 미국 달러 기준입니다.", "약정 할인을 제외한 모델 추정치입니다."]


def test_chart_names_the_scenario_with_the_largest_change(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    chart = next(c for c in cards if c["kind"] == "chart")
    assert chart["lead"] == "월 사용료 변동 폭이 가장 큰 시나리오는 소규모 BI 대시보드입니다."
    assert _title(chart) == "플랫폼별 월 사용료"


def test_no_cost_card_when_only_the_ranking_changes(make_events, workloads):
    events, rows, prev_rows = make_events(RANKED)
    events["cost_changes"] = []                          # 순위만 바뀌고 월 사용료 변동은 기준 미만인 날
    cards = price_change_cards(events, rows, prev_rows, workloads)
    assert [c["kind"] for c in cards] == ["cover", "bullets", "chart", "banners", "banners", "closing"]
    assert next(c for c in cards if c["kind"] == "chart")["scenario"] == "W1"   # 전체 조합에서 정한다


def test_labels_follow_the_fixed_terms(make_events, workloads):
    _, cards = _cards(make_events, workloads, TYPICAL)
    assert cards[1]["items"] == [{"strong": "Redshift 컴퓨트 · 미국 리전", "rest": "$0.375 → $0.40 (+6.7%)"}]
    assert cards[3]["items"][0] == {"strong": "소규모 BI 대시보드 · 미국 리전 Redshift", "rest": "$900 → $944 (+4.9%)"}
    assert cards[3]["lead"] == "월 사용료가 ±1% 이상 바뀐 조합입니다."
    assert _title(cards[1]) == "단가 변동 내역" and _title(cards[3]) == "월 사용료 변동 내역"
    assert "월 비용" not in card_text(cards)                              # D17: 카드는 월 사용료


def test_prices_follow_the_script_format():
    """스크립트 0-2절: 반올림하지 않고, 소수 둘째 자리까지는 0을 채운다."""
    assert [price_label(v) for v in (0.4, 0.39375, 0.0208, 23.0, 6.25)] == ["$0.40", "$0.39375", "$0.0208", "$23.00", "$6.25"]
    added = {"platform": "bigquery", "service": "storage", "region": "us", "before": None, "after": 0.04, "change_pct": None}
    assert price_item(added) == {"strong": "BigQuery 스토리지 · 미국 리전", "rest": "없음 → $0.04"}
    scan = {"platform": "bigquery", "service": "scan", "region": "seoul", "before": 7.5, "after": None, "change_pct": None}
    assert price_item(scan) == {"strong": "BigQuery 주문형 쿼리 · 서울 리전", "rest": "$7.50 → 없음"}


def test_every_number_on_the_cards_is_in_events(make_events, workloads):
    events, cards = _cards(make_events, workloads, MANY)
    check_numbers(card_text(cards), events)                              # 그대로면 통과
    workloads["scenarios"]["W1"]["name"] = "소규모 BI 대시보드 777"
    events, rows, prev_rows = make_events(TYPICAL)
    with pytest.raises(ValueError, match="777"):
        price_change_cards(events, rows, prev_rows, workloads)


def test_text_over_the_length_limit_stops_generation(make_events, workloads):
    workloads["scenarios"]["W1"]["name"] = "매우 긴 이름을 가진 시나리오" * 3
    events, rows, prev_rows = make_events(TYPICAL)
    with pytest.raises(ValueError, match="글자 수"):
        price_change_cards(events, rows, prev_rows, workloads)


def test_events_without_a_significant_change_are_rejected(make_events, workloads):
    events, rows, prev_rows = make_events({("redshift", "storage", "us"): 0.02401})   # 월 사용료 변동이 기준 미만
    assert events["price_changes"] and not events["significant"]
    with pytest.raises(ValueError):
        price_change_cards(events, rows, prev_rows, workloads)


SCRIPT = Path(__file__).resolve().parent.parent / "docs" / "scripts" / "cards-script.md"


def _result(us=False, seoul=False, t2=True, spread=39.5, us_winner="redshift", seoul_winner="redshift"):
    """analyze()의 판정 부분. supported=True가 채택이다. 채택이면 시나리오마다 1위가 다르다."""
    def t1(supported, winner):
        return {"winners": {"W1": winner, "W2": "bigquery" if supported else winner, "W3": winner},
                "robustness": {"W1": "견고", "W2": "견고", "W3": "견고"}, "supported": supported}
    return {"t1_by_region": {"us": t1(us, us_winner), "seoul": t1(seoul, seoul_winner)},
            "t2": {"spread_pp": spread, "supported": t2}}


def test_intro_cards_are_five_in_order():
    cards, _ = intro_cards(_result(), "2026-09-11")
    assert [(c["kind"], c.get("group")) for c in cards] == [
        ("cover", None), ("chips", None), ("flow", None), ("bullets", "result"), ("closing", None)]
    assert cards[-1] == closing_card()
    assert [(chip["platform"], chip["unit"]) for chip in cards[1]["chips"]] == [
        ("Snowflake", "크레딧"), ("Databricks", "DBU-시간"), ("Redshift", "RPU-시간"), ("BigQuery", "슬롯-시간")]
    assert [step["text"] for step in cards[2]["steps"]] == ["매일 수집", "월 사용료 계산", "검토 요청에서 정지", "승인 후 게시"]
    assert [step["text"] for step in cards[2]["steps"] if step["stop"]] == ["검토 요청에서 정지"]   # 멈춤 지점


def test_intro_results_state_each_region_and_the_conclusion():
    cards, _ = intro_cards(_result(us_winner="databricks"), "2026-09-11")
    result = cards[3]
    assert result["lead"] == "월 사용료가 가장 낮은 플랫폼이 1위입니다."
    assert result["items"] == [
        {"strong": "T1 기각 · 미국 리전", "rest": "시나리오가 달라도 1위는 Databricks로 같습니다."},
        {"strong": "T1 기각 · 서울 리전", "rest": "시나리오가 달라도 1위는 Redshift로 같습니다."},
        {"strong": "T2 채택", "rest": "서울 프리미엄은 서비스마다 최대 39.5%p 다릅니다."}]
    assert result["notes"] == ["2026-09-11 승인 스냅샷 기준입니다.", "약정 할인을 제외한 모델 추정치입니다."]

    cards, _ = intro_cards(_result(us=True, t2=False, spread=9.9), "2026-09-11")
    assert cards[3]["items"][0] == {"strong": "T1 채택 · 미국 리전", "rest": "시나리오에 따라 1위가 달라집니다."}
    assert cards[3]["items"][2] == {"strong": "T2 기각", "rest": "서울 프리미엄의 서비스 간 차이가 9.9%p로 작습니다."}
    assert "지지" not in card_text(cards)                                  # 규칙 17: 채택 / 기각


def test_intro_numbers_come_from_the_approved_snapshot():
    cards, facts = intro_cards(_result(spread=39.5), "2026-09-11")
    text = card_text(cards)
    assert "39.5%p" in text and "2026-09-11" in text
    check_numbers(text, facts)                                             # 그대로면 통과
    with pytest.raises(ValueError, match="39.5"):
        check_numbers(text, {**facts, "spread_pp": 12.3})                  # 기준 사전에 없는 숫자는 멈춘다


def test_intro_copy_matches_the_script():
    """소개 카드 고정 문장이 확정 스크립트 3절과 글자 단위로 같다. 자리표시자 {…} 자리에는 무엇이 와도 된다."""
    section = SCRIPT.read_text(encoding="utf-8").split("## 3. 소개 카드")[1].split("\n## ")[0]
    expected = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- 제목:", "- 부제:", "- 리드:")):
            expected.append(stripped.split(":", 1)[1].strip().replace("**", "").strip("`"))
        elif stripped.startswith(("- 칩 4개:", "- 흐름 4단계:", "- 각주")):
            expected += re.findall(r"`([^`]+)`", stripped)
        elif stripped.startswith("| T1") or stripped.startswith("| T2") or stripped.startswith("| |"):
            expected += [re.sub(r"^\[.+?\] ", "", cell) for cell in re.findall(r"(?:\[.+?\] )?`([^`]+)`", stripped)]
        elif stripped and not stripped.startswith(("-", "#", "|", "`", "1-1")) and "니다." in stripped:
            expected.append(stripped)                                      # 3장 각주 코드 블록의 문장
    assert len(expected) >= 20
    variants = [intro_cards(_result(), "2026-09-11")[0], intro_cards(_result(us=True, t2=False, spread=9.9), "2026-09-11")[0]]
    lines = set()
    for cards in variants:
        lines |= set(card_text(cards).splitlines())
        lines |= {f"{chip['platform']} {chip['unit']}" for chip in cards[1]["chips"]}
        lines |= {step["text"] for step in cards[2]["steps"]}
    for text in expected:
        pattern = re.sub(r"\\\{.+?\\\}", ".+?", re.escape(text))
        assert any(re.fullmatch(pattern, line) for line in lines), text
