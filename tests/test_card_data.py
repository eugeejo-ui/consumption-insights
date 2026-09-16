import re
from pathlib import Path

import pytest

from model.tco import CostRow
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
    assert closing["lead"] == "워크로드별 월 사용료, 리전별 가격 차이, 계산 가정을 공개합니다."
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


ORDER = ("redshift", "snowflake", "bigquery", "databricks")
PREMIUMS = [("databricks", "compute", 0.7, 0.95), ("snowflake", "compute", 3.0, 4.05),
            ("bigquery", "storage", 0.04, 0.052), ("bigquery", "compute", 0.06, 0.0765),
            ("bigquery", "scan", 6.25, 7.5), ("redshift", "compute", 0.375, 0.438),
            ("redshift", "storage", 0.024, 0.0261), ("snowflake", "storage", 23.0, 25.0),
            ("databricks", "storage", 0.0208, 0.02)]


def _result(us_order=ORDER, seoul_order=None, hours=220, storage_gb=10000, premiums=PREMIUMS):
    """analyze()에서 소개 카드가 쓰는 부분. 첫 시나리오의 월 사용료로 순위를 만든다.
    서울 리전 금액은 미국 리전보다 조금씩 더 비싸고, 비싼 플랫폼일수록 증가율이 크다(실제 스냅샷과 같은 모양)."""
    rows = [CostRow(scenario="W1", platform=platform, region=region,
                    compute_usd=900 + n * 500 + (100 * (n + 1) if region == "seoul" else 0), storage_usd=0)
            for region, order in (("us", us_order), ("seoul", seoul_order or us_order))
            for n, platform in enumerate(order)]
    return {"rows": rows,
            "premiums": [{"platform": platform, "service": service, "sku": f"{platform}-{service}",
                          "us": us, "seoul": seoul, "premium_pct": round((seoul / us - 1) * 100, 1)}
                         for platform, service, us, seoul in premiums],
            "workloads": {"storage_gb": storage_gb,
                          "scenarios": {"W1": {"name": "소규모 BI 대시보드", "hours_per_month": hours},
                                        "W2": {"name": "야간 배치 ETL", "hours_per_month": 60}}}}


def test_intro_cards_are_eight_in_order():
    cards, _ = intro_cards(_result(), "2026-09-11")
    assert [(c["kind"], c.get("group")) for c in cards] == [
        ("cover", None), ("chips", None), ("flow", None), ("bullets", "result"),
        ("bullets", "unit"), ("bullets", "unit"), ("bullets", "region"), ("closing", None)]
    assert cards[-1] == closing_card()
    assert [(chip["platform"], chip["unit"]) for chip in cards[1]["chips"]] == [
        ("Snowflake", "크레딧"), ("Databricks", "DBU-시간"), ("Redshift", "RPU-시간"), ("BigQuery", "슬롯-시간")]
    assert [step["text"] for step in cards[2]["steps"]] == ["매일 수집", "월 사용료 계산", "검토 요청에서 정지", "승인 후 게시"]
    assert [step["text"] for step in cards[2]["steps"] if step["stop"]] == ["검토 요청에서 정지"]   # 멈춤 지점


def test_intro_ranks_the_platforms_by_monthly_cost():
    """4장은 가설 판정이 아니라 플랫폼별 순위와 두 리전 금액을 싣는다(2026-09-16 개정)."""
    cards, _ = intro_cards(_result(us_order=("databricks", "redshift", "snowflake", "bigquery")), "2026-09-11")
    result = cards[3]
    assert [part["text"] for part in result["title"]] == ["월 사용료 ", "현재 순위"]
    assert result["lead"] == "월 사용료가 낮은 순서입니다."
    assert result["items"] == [
        {"strong": "1위 Databricks", "rest": "미국 리전 $900 · 서울 리전 $1,000"},
        {"strong": "2위 Redshift", "rest": "미국 리전 $1,400 · 서울 리전 $1,600"},
        {"strong": "3위 Snowflake", "rest": "미국 리전 $1,900 · 서울 리전 $2,200"},
        {"strong": "4위 BigQuery", "rest": "미국 리전 $2,400 · 서울 리전 $2,800"}]
    assert result["notes"] == ["2026-09-11 승인 스냅샷 기준", "금액은 벤더 공시 통화인 달러 기준",
                               "약정 할인을 제외한 모델 추정치"]     # 각주는 명사구로 끝맺는다
    assert result["basis"] == "비교 기준: 소형 컴퓨트 월 220시간 · 스토리지 10TB(압축 후)"
    text = card_text(cards)
    for banned in ("T1", "T2", "채택", "기각", "시나리오", "매일 비교"):
        assert banned not in text                                          # 가설·시나리오는 카드에 싣지 않는다
    assert cards[0]["lead"] == "같은 워크로드를 기준으로 월 사용료를 환산해 비교합니다."


def test_unit_price_cards_carry_every_item_with_page_labels():
    """단가 항목을 생략하지 않는다(규칙 18). 5개마다 장을 늘리고 쪽 표시를 붙인다."""
    cards, _ = intro_cards(_result(), "2026-09-11")
    unit = [c for c in cards if c.get("group") == "unit"]
    assert [c["page"] for c in unit] == ["(1/2)", "(2/2)"]
    assert [[part["text"] for part in c["title"]] for c in unit] == [["서울 리전 ", "단가 차이"]] * 2
    items = [item for c in unit for item in c["items"]]
    assert len(items) == len(_result()["premiums"]) == 9              # 9개를 5 + 4로 나눈다
    assert [len(c["items"]) for c in unit] == [5, 4]
    assert items[0] == {"strong": "Databricks 컴퓨트", "rest": "$0.70 → $0.95 (+35.7%)"}
    assert items[-1] == {"strong": "Databricks 스토리지", "rest": "$0.0208 → $0.02 (-3.8%)"}   # 차이가 큰 순
    assert all(c["notes"] == ["2026-09-11 승인 스냅샷 기준", "단가는 벤더 공시 통화인 달러 기준"] for c in unit)


def test_unit_price_lead_mentions_a_cheaper_seoul_only_when_one_exists():
    cards, _ = intro_cards(_result(), "2026-09-11")
    lead = next(c["lead"] for c in cards if c.get("group") == "unit")
    assert lead == ("같은 상품의 서울 리전 단가가 미국 리전보다 높습니다. "
                    "항목에 따라 서울 리전 단가가 더 낮은 경우도 있습니다.")

    dearer = _result(premiums=[("snowflake", "compute", 3.0, 4.05)])   # 서울이 더 싼 항목이 없는 날
    lead = next(c["lead"] for c in intro_cards(dearer, "2026-09-11")[0] if c.get("group") == "unit")
    assert lead == "같은 상품의 서울 리전 단가가 미국 리전보다 높습니다."


def test_region_cost_card_compares_the_same_workload_in_both_regions():
    cards, _ = intro_cards(_result(), "2026-09-11")
    region = next(c for c in cards if c.get("group") == "region")
    assert [part["text"] for part in region["title"]] == ["서울 리전 ", "월 사용료"]
    assert region["lead"] == "같은 워크로드를 서울 리전에서 돌릴 때의 월 사용료입니다."
    assert region["items"][0] == {"strong": "Redshift", "rest": "$900 → $1,000 (+11.1%)"}   # 증가율이 낮은 순
    assert [item["strong"] for item in region["items"]] == ["Redshift", "Snowflake", "BigQuery", "Databricks"]
    assert region["notes"] == ["2026-09-11 승인 스냅샷 기준", "금액은 벤더 공시 통화인 달러 기준"]
    assert region["basis"] == "비교 기준: 소형 컴퓨트 월 220시간 · 스토리지 10TB(압축 후)"   # 4장과 같은 줄


def test_intro_stops_when_the_two_regions_rank_differently():
    """한 항목에 두 리전을 묶으므로 순서가 같아야 한다. 다르면 문안부터 고친다."""
    with pytest.raises(ValueError, match="순위"):
        intro_cards(_result(seoul_order=("snowflake", "redshift", "bigquery", "databricks")), "2026-09-11")


def test_intro_numbers_come_from_the_approved_snapshot():
    cards, facts = intro_cards(_result(), "2026-09-11")
    text = card_text(cards)
    assert "미국 리전 $900 · 서울 리전 $1,000" in text and "2026-09-11" in text
    assert "월 220시간" in text and "10TB" in text                          # 비교 기준 줄도 숫자 검사를 받는다
    check_numbers(text, facts)                                             # 그대로면 통과
    with pytest.raises(ValueError, match="900"):
        check_numbers(text, {**facts, "amounts": {}, "region_costs": []})  # 기준 사전에 없는 숫자는 멈춘다


def test_intro_copy_matches_the_script():
    """소개 카드 고정 문장이 확정 스크립트 3절과 글자 단위로 같다. 자리표시자 {…} 자리에는 무엇이 와도 된다."""
    section = SCRIPT.read_text(encoding="utf-8").split("## 3. 소개 카드")[1].split("\n## ")[0]
    expected = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- 제목:", "- 부제:", "- 리드:")):
            # 쪽 표시는 장 순번이라 card_text에 들어가지 않는다(4절). 제목 대조에서도 뺀다.
            expected.append(stripped.split(":", 1)[1].replace("**", "").replace("`", "").replace("{쪽}", "").strip())
        elif stripped.startswith(("- 칩 4개:", "- 흐름 4단계:", "- 각주", "- 항목", "- 비교 기준")):
            expected += re.findall(r"`([^`]+)`", stripped)
        elif stripped.startswith("| T1") or stripped.startswith("| T2") or stripped.startswith("| |"):
            expected += [re.sub(r"^\[.+?\] ", "", cell) for cell in re.findall(r"(?:\[.+?\] )?`([^`]+)`", stripped)]
        elif stripped and not stripped.startswith(("-", "#", "|", "`", "*", "1-1")) and "니다." in stripped:
            expected.append(stripped)                                      # 3장 각주 코드 블록의 문장(설명 문단은 **로 시작한다)
    assert len(expected) >= 20
    cards = intro_cards(_result(), "2026-09-11")[0]
    lines = set(card_text(cards).splitlines())
    lines |= {f"{chip['platform']} {chip['unit']}" for chip in cards[1]["chips"]}
    lines |= {step["text"] for step in cards[2]["steps"]}
    # 리드가 두 문장인 장이 있다. 스크립트는 문장마다 한 줄로 적으므로 문장 단위도 대조 대상에 넣는다.
    lines |= {f"{sentence.strip()}." for line in set(lines) for sentence in line.split(".") if sentence.strip()}
    for text in expected:
        pattern = re.sub(r"\\\{.+?\\\}", ".+?", re.escape(text))
        assert any(re.fullmatch(pattern, line) for line in lines), text
