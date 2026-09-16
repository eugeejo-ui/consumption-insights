"""카드뉴스 장별 데이터(Phase 3 Task 3·8). events.json을 장 목록으로 바꾼다. 디자인과 굽기는 render_cards의 일이다.
문안의 정본은 docs/scripts/cards-script.md다. 항목을 생략하지 않고(규칙 18), 카드의 숫자는 모두 events.json에 있어야 한다.
소개 카드(Task 8)는 events.json이 없어 승인 스냅샷의 판정 결과로 만든 기준 사전으로 숫자를 검사한다.
검사 셋(누락·글자 수·숫자) 중 하나라도 어긋나면 ValueError로 생성을 멈춘다. 잘라내거나 요약하지 않는다."""
from __future__ import annotations

from decimal import Decimal

from common.schema import REGIONS
from model.tco import CostRow  # noqa: F401  (rank_items·price_change_cards의 자료형)
from publish.render_post import PLATFORM_LABELS, check_numbers

PER_PAGE = {"price": 5, "cost": 6, "rank": 2, "unit": 5}           # 디자인 계획 4-1, 스크립트 4-1절
LIMITS = {"cover_line": 10, "closing_title": 20, "title": 28,       # 스크립트 4절: 한 줄 상한 × 줄 수 상한
          "lead": 90, "item": 32, "note": 40, "basis": 44,           # 항목·각주·비교 기준은 한 줄씩 싣는다
          "chip": 12, "step": 16}                                   # 소개 카드 칩·흐름 단계는 한 줄
SERVICE_LABELS = {"compute": "컴퓨트", "storage": "스토리지", "scan": "주문형 쿼리"}
REGION_LABELS = {"us": "미국 리전", "seoul": "서울 리전"}
DASHBOARD = "eugeejo-ui.github.io/consumption-insights"
CHART_NOTES = ["금액은 벤더 공시 통화인 미국 달러 기준입니다.", "약정 할인을 제외한 모델 추정치입니다."]
# 소개 4장 각주는 명사구로 끝맺는다(2026-09-16 사용자 수정). 읽는 문장이 아니라 조건 표시다(규칙 17).
INTRO_NOTES = ["금액은 벤더 공시 통화인 달러 기준", "약정 할인을 제외한 모델 추정치"]
BASIS = "비교 기준: 소형 컴퓨트 월 {hours}시간 · 스토리지 {storage_tb}TB(압축 후)"   # 순위가 나온 조건. 각주보다 작게 싣는다
UNIT_LEAD = "같은 상품의 서울 리전 단가가 미국 리전보다 높습니다."
UNIT_LEAD_CHEAPER = "항목에 따라 서울 리전 단가가 더 낮은 경우도 있습니다."   # 서울이 더 싼 항목이 있는 날만 붙인다
UNIT_NOTE = "단가는 벤더 공시 통화인 달러 기준"
REGION_LEAD = "같은 워크로드를 서울 리전에서 돌릴 때의 월 사용료입니다."
INTRO_UNITS = [("Snowflake", "크레딧"), ("Databricks", "DBU-시간"), ("Redshift", "RPU-시간"), ("BigQuery", "슬롯-시간")]
INTRO_FLOW = ["매일 수집", "월 사용료 계산", "검토 요청에서 정지", "승인 후 게시"]
INTRO_STOP = "검토 요청에서 정지"                                      # 사람의 승인을 기다리는 지점. 흐름 장에서 구분한다


def _title(plain: str, accent: str, after: str = "") -> list[dict]:
    parts = [{"text": plain, "accent": False}, {"text": accent, "accent": True}]
    return parts + [{"text": after, "accent": False}] if after else parts


def price_label(value: float | None) -> str:
    """단가는 반올림하지 않는다. 소수 둘째 자리까지는 0을 채운다(스크립트 0-2절)."""
    if value is None:
        return "없음"
    amount = Decimal(repr(value)).normalize()                       # repr가 가장 짧은 정확한 표기다
    if amount.as_tuple().exponent > -2:
        amount = amount.quantize(Decimal("0.01"))
    return f"${amount:f}"


def usd_label(value: float) -> str:
    return f"${value:,.0f}"


def _rate(pct: float | None) -> str:
    return "" if pct is None else f" ({pct:+.1f}%)"


def _order(platforms: list[str]) -> str:
    return " › ".join(PLATFORM_LABELS[p] for p in platforms)


def price_item(change: dict) -> dict:
    return {"strong": f"{PLATFORM_LABELS[change['platform']]} {SERVICE_LABELS[change['service']]} · {REGION_LABELS[change['region']]}",
            "rest": f"{price_label(change['before'])} → {price_label(change['after'])}{_rate(change['change_pct'])}"}


def scenario_names(workloads: dict) -> dict[str, str]:
    return {sid: scenario["name"] for sid, scenario in workloads["scenarios"].items()}


def note_price_change_count(events: dict) -> int:
    """표지 부제·게시문의 `단가 N건`이 숫자 검사를 통과하도록 events에 기록한다."""
    count = len(events["price_changes"])
    events.setdefault("display", {})["price_change_count"] = count
    return count


def cover_title(events: dict) -> list[dict]:
    if events["rank_changes"]:
        return _title("월 사용료 ", "순위 변동")
    if events["cost_changes"]:
        return _title("월 사용료 ", "변동")
    return _title("단가 ", "변동")


def representative_scenario(rows: list[CostRow], prev_rows: list[CostRow]) -> str:
    """월 사용료 변화율(소수 첫째 자리)의 절댓값이 가장 큰 조합의 시나리오. 동률이면 계산 순서의 첫 조합.
    cost_changes가 비어 있는 날(순위만 변동)에도 정해지도록 전체 조합에서 고른다."""
    before = {(r.scenario, r.region, r.platform): r.total_usd for r in prev_rows}
    best = max(rows, key=lambda r: abs(round((r.total_usd / before[(r.scenario, r.region, r.platform)] - 1) * 100, 1)))
    return best.scenario


def _pages(items: list, size: int) -> list[tuple[list, str | None]]:
    chunks = [items[i:i + size] for i in range(0, len(items), size)]
    return [(chunk, f"({n}/{len(chunks)})" if len(chunks) > 1 else None) for n, chunk in enumerate(chunks, start=1)]


def price_change_cards(events: dict, rows: list[CostRow], prev_rows: list[CostRow], workloads: dict) -> list[dict]:
    """정기 카드(가격 변동 리포트). events를 제자리에서 보강한다(display.price_change_count, display.chart)."""
    if not events.get("significant"):
        raise ValueError("월 사용료 변동이나 순위 변동이 없는 날에는 카드를 만들지 않는다")
    names = scenario_names(workloads)
    count = note_price_change_count(events)
    sid = representative_scenario(rows, prev_rows)
    series = {region: {r.platform: round(r.total_usd) for r in rows if r.scenario == sid and r.region == region}
              for region in REGIONS}
    events["display"]["chart"] = {"scenario": sid, **{region: dict(amounts) for region, amounts in series.items()}}

    cards = [{"kind": "cover", "title": cover_title(events), "subtitle": f"{events['day']} · 단가 {count}건",
              "lead": f"직전 승인 가격({events['compared_to']}) 대비 변동 사항입니다."}]
    for items, page in _pages([price_item(c) for c in events["price_changes"]], PER_PAGE["price"]):
        cards.append({"kind": "bullets", "group": "price", "page": page, "title": _title("단가 ", "변동 내역"),
                      "lead": "직전 승인 가격과 달라진 항목입니다.", "items": items})
    cards.append({"kind": "chart", "title": _title("플랫폼별 ", "월 사용료"),
                  "lead": f"월 사용료 변동 폭이 가장 큰 시나리오는 {names[sid]}입니다.",
                  "scenario": sid, "series": series, "notes": list(CHART_NOTES)})
    costs = [{"strong": f"{names[c['scenario']]} · {REGION_LABELS[c['region']]} {PLATFORM_LABELS[c['platform']]}",
              "rest": f"{usd_label(c['before'])} → {usd_label(c['after'])}{_rate(c['change_pct'])}"}
             for c in events["cost_changes"]]
    for items, page in _pages(costs, PER_PAGE["cost"]):
        cards.append({"kind": "bullets", "group": "cost", "page": page, "title": _title("월 사용료 ", "변동 내역"),
                      "lead": f"월 사용료가 ±{events['min_cost_change_pct']:g}% 이상 바뀐 조합입니다.", "items": items})
    banners = [{"label": f"{names[r['scenario']]} · {REGION_LABELS[r['region']]}",
                "before": _order(r["before"]), "after": _order(r["after"])} for r in events["rank_changes"]]
    for group, page in _pages(banners, PER_PAGE["rank"]):
        cards.append({"kind": "banners", "page": page, "title": _title("순위 ", "변동"),
                      "lead": "월 사용료가 낮은 순서입니다.", "banners": group})
    cards.append(closing_card())

    check_complete(cards, events)
    check_lengths(cards)
    check_numbers(card_text(cards), events)
    return cards


def closing_card() -> dict:
    """모든 카드뉴스의 마지막 장(D20). 소개 카드(Task 8)도 같은 장을 쓴다."""
    return {"kind": "closing", "title": _title("전체 비교는 ", "대시보드", "에 있습니다"),
            "lead": "워크로드별 월 사용료, 리전별 가격 차이, 계산 가정을 공개합니다.", "url": DASHBOARD}


def rank_items(rows: list[CostRow], scenario: str) -> tuple[list[dict], dict]:
    """월 사용료가 낮은 순서로 플랫폼 항목을 만든다(스크립트 3절 4장). 금액은 두 리전을 한 줄에 싣는다.

    한 항목에 두 리전을 묶으므로 순서가 같아야 한다. 다르면 문안이 성립하지 않아 멈춘다.
    """
    cost = {(r.region, r.platform): r.total_usd for r in rows if r.scenario == scenario}
    orders = {region: sorted({p for r, p in cost if r == region}, key=lambda p: cost[(region, p)]) for region in REGIONS}
    if len({tuple(order) for order in orders.values()}) > 1:
        raise ValueError(f"리전마다 순위가 다르다({orders}). 한 항목에 두 리전을 묶을 수 없으니 스크립트를 고친다")
    items = [{"strong": f"{n}위 {PLATFORM_LABELS[platform]}",
              "rest": f"{REGION_LABELS['us']} {usd_label(cost[('us', platform)])} · "
                      f"{REGION_LABELS['seoul']} {usd_label(cost[('seoul', platform)])}"}
             for n, platform in enumerate(orders["us"], start=1)]
    amounts = {region: {platform: round(cost[(region, platform)]) for platform in orders[region]} for region in REGIONS}
    return items, amounts


def unit_price_cards(premiums: list[dict], day: str) -> tuple[list[dict], list]:
    """상품 단가를 미국 리전과 서울 리전으로 비교한다(스크립트 3절). 차이가 큰 순이며 항목을 생략하지 않는다."""
    ranked = sorted(premiums, key=lambda p: -p["premium_pct"])
    lead = UNIT_LEAD + (f" {UNIT_LEAD_CHEAPER}" if any(p["premium_pct"] < 0 for p in ranked) else "")
    items = [{"strong": f"{PLATFORM_LABELS[p['platform']]} {SERVICE_LABELS[p['service']]}",
              "rest": f"{price_label(p['us'])} → {price_label(p['seoul'])} ({p['premium_pct']:+.1f}%)"}
             for p in ranked]
    cards = [{"kind": "bullets", "group": "unit", "page": page, "title": _title("서울 리전 ", "단가 차이"),
              "lead": lead, "items": chunk, "notes": [f"{day} 승인 스냅샷 기준", UNIT_NOTE]}
             for chunk, page in _pages(items, PER_PAGE["unit"])]
    return cards, [[p["us"], p["seoul"], round(p["premium_pct"], 1)] for p in ranked]


def region_cost_card(rows: list[CostRow], scenario: str, day: str, basis: str) -> tuple[dict, list]:
    """같은 워크로드를 두 리전에서 돌렸을 때의 월 사용료(스크립트 3절). 증가율이 낮은 순이다."""
    cost = {(r.region, r.platform): r.total_usd for r in rows if r.scenario == scenario}
    rise = {platform: cost[("seoul", platform)] / cost[("us", platform)] - 1
            for region, platform in cost if region == "us"}
    platforms = sorted(rise, key=lambda platform: rise[platform])
    card = {"kind": "bullets", "group": "region", "page": None, "title": _title("서울 리전 ", "월 사용료"),
            "lead": REGION_LEAD,
            "items": [{"strong": PLATFORM_LABELS[platform],
                       "rest": f"{usd_label(cost[('us', platform)])} → {usd_label(cost[('seoul', platform)])} "
                               f"({rise[platform] * 100:+.1f}%)"} for platform in platforms],
            "notes": [f"{day} 승인 스냅샷 기준", INTRO_NOTES[0]], "basis": basis}
    return card, [[round(cost[("us", p)]), round(cost[("seoul", p)]), round(rise[p] * 100, 1)] for p in platforms]


def intro_cards(result: dict, day: str) -> tuple[list[dict], dict]:
    """소개 카드 5장(스크립트 3절). result는 승인 스냅샷의 analyze() 결과(rows, workloads), day는 그 승인일이다.
    소개 카드에는 events.json이 없으므로 숫자 검사 기준 사전을 함께 돌려준다. 굽기의 숫자 검사도 이 사전을 쓴다."""
    workloads = result["workloads"]
    scenario = next(iter(workloads["scenarios"]))                   # 대시보드를 열면 처음 보이는 워크로드
    hours = workloads["scenarios"][scenario]["hours_per_month"]
    storage_tb = round(workloads["storage_gb"] / 1000)
    items, amounts = rank_items(result["rows"], scenario)
    basis = BASIS.format(hours=hours, storage_tb=storage_tb)
    unit, unit_prices = unit_price_cards(result["premiums"], day)
    region, region_costs = region_cost_card(result["rows"], scenario, day, basis)
    cards = [
        {"kind": "cover", "title": _title("데이터 플랫폼 네 곳의 ", "월 사용료 추적"),
         "subtitle": "Snowflake · Databricks · BigQuery · Redshift",
         "lead": "같은 워크로드를 기준으로 월 사용료를 환산해 비교합니다."},
        {"kind": "chips", "title": _title("가격표만으로는 ", "비교되지 않습니다"), "break_before_accent": True,   # 강조 구절을 한 줄에 둔다
         "lead": "네 플랫폼은 과금 단위가 서로 다릅니다.",
         "chips": [{"platform": platform, "unit": unit} for platform, unit in INTRO_UNITS],
         "notes": ["단가를 나란히 놓아도 어느 쪽의 월 사용료가 낮은지 판단할 수 없습니다."]},
        {"kind": "flow", "title": _title("사람의 ", "승인", "을 거칩니다"), "lead": "",
         "steps": [{"text": text, "stop": text == INTRO_STOP} for text in INTRO_FLOW],
         "notes": ["가격이 바뀐 날에만 검토 요청이 열립니다.", "승인한 값만 기록과 비교 기준에 사용합니다."]},
        {"kind": "bullets", "group": "result", "page": None, "title": _title("월 사용료 ", "현재 순위"),
         "lead": "월 사용료가 낮은 순서입니다.", "items": items,
         "notes": [f"{day} 승인 스냅샷 기준", *INTRO_NOTES], "basis": basis},
        *unit,
        region,
        closing_card(),
    ]
    facts = {"day": day, "ranks": list(range(1, len(items) + 1)), "hours": hours, "storage_tb": storage_tb,
             "amounts": amounts, "unit_prices": unit_prices, "region_costs": region_costs}
    check_lengths(cards)
    check_numbers(card_text(cards), facts)
    return cards, facts


def check_complete(cards: list[dict], events: dict) -> None:
    """규칙 18 누락 검사: 카드에 실린 항목 수가 events.json의 항목 수와 같아야 한다."""
    carried = {"price": 0, "cost": 0, "rank": 0}
    for card in cards:
        if card["kind"] == "bullets":
            carried[card["group"]] += len(card["items"])
        elif card["kind"] == "banners":
            carried["rank"] += len(card["banners"])
    expected = {"price": len(events["price_changes"]), "cost": len(events["cost_changes"]),
                "rank": len(events["rank_changes"])}
    for group, n in expected.items():
        if carried[group] != n:
            raise ValueError(f"누락: {group} 항목이 events.json에는 {n}건, 카드에는 {carried[group]}건이다")


def _title_text(card: dict) -> str:
    text = "".join(part["text"] for part in card["title"])
    return f"{text} {card['page']}" if card.get("page") else text


def check_lengths(cards: list[dict]) -> None:
    """스크립트 4절 글자 수 상한. 넘치면 잘라내지 않고 멈춘다. 문안이 길어지면 스크립트를 고친다."""
    for n, card in enumerate(cards, start=1):
        if card["kind"] == "cover":
            # 표지 제목은 일반 부분과 강조 부분이 줄로 나뉜다. 줄마다 공백을 빼고 센다.
            # 104px에서 공백 폭은 한글 한 글자의 1/4 안팎이다: 공백 3개가 든 12자 줄이 968px 폭에 들어간다 [확인 2026-09-15].
            fields = [("cover_line", part["text"].replace(" ", "")) for part in card["title"]]
        else:
            fields = [({"closing": "closing_title"}.get(card["kind"], "title"), _title_text(card))]
        fields.append(("lead", card["lead"]))
        fields += [("item", text) for item in card.get("items", []) for text in (item["strong"], item["rest"])]
        fields += [("note", text) for text in card.get("notes", [])]
        fields += [("basis", card["basis"])] if card.get("basis") else []
        fields += [("chip", text) for chip in card.get("chips", []) for text in (chip["platform"], chip["unit"])]
        fields += [("step", step["text"]) for step in card.get("steps", [])]
        for name, text in fields:
            if len(text) > LIMITS[name]:
                raise ValueError(f"글자 수: {n}장 {name} {len(text)}자가 상한 {LIMITS[name]}자를 넘는다: {text}")


def card_text(cards: list[dict]) -> str:
    """카드에 찍히는 문자열(숫자 검사용). 쪽 표시 (1/2)는 데이터가 아니라 장 순번이라 뺀다."""
    lines = []
    for card in cards:
        lines += ["".join(part["text"] for part in card["title"]), card.get("subtitle", ""), card["lead"]]
        lines += [text for item in card.get("items", []) for text in (item["strong"], item["rest"])]
        lines += [text for banner in card.get("banners", []) for text in banner.values()]
        lines += [usd_label(v) for amounts in card.get("series", {}).values() for v in amounts.values()]
        lines += [text for chip in card.get("chips", []) for text in (chip["platform"], chip["unit"])]
        lines += [step["text"] for step in card.get("steps", [])]
        lines += card.get("notes", []) + [card.get("basis", ""), card.get("url", "")]
    return "\n".join(line for line in lines if line)
