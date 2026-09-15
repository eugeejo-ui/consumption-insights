"""카드뉴스 장별 데이터(Phase 3 Task 3). events.json을 장 목록으로 바꾼다. 디자인과 굽기는 render_cards의 일이다.
문안의 정본은 docs/scripts/cards-script.md다. 항목을 생략하지 않고(규칙 18), 카드의 숫자는 모두 events.json에 있어야 한다.
검사 셋(누락·글자 수·숫자) 중 하나라도 어긋나면 ValueError로 생성을 멈춘다. 잘라내거나 요약하지 않는다."""
from __future__ import annotations

from decimal import Decimal

from common.schema import REGIONS
from model.tco import CostRow
from publish.render_post import PLATFORM_LABELS, check_numbers

PER_PAGE = {"price": 5, "cost": 6, "rank": 2}                       # 디자인 계획 4-1
LIMITS = {"cover_title": 20, "closing_title": 20, "title": 28,      # 스크립트 4절: 한 줄 상한 × 줄 수 상한
          "lead": 90, "item": 32, "note": 40}                       # 항목과 각주는 한 줄씩 싣는다
SERVICE_LABELS = {"compute": "컴퓨트", "storage": "스토리지", "scan": "주문형 쿼리"}
REGION_LABELS = {"us": "미국 리전", "seoul": "서울 리전"}
DASHBOARD = "eugeejo-ui.github.io/consumption-insights"
CHART_NOTES = ["금액은 벤더 공시 통화인 미국 달러 기준입니다.", "약정 할인을 제외한 모델 추정치입니다."]


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
            "lead": "시나리오별 월 사용료, 서울 프리미엄, 가정과 산출 근거를 공개합니다.", "url": DASHBOARD}


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
        role = {"cover": "cover_title", "closing": "closing_title"}.get(card["kind"], "title")
        fields = [(role, _title_text(card)), ("lead", card["lead"])]
        fields += [("item", text) for item in card.get("items", []) for text in (item["strong"], item["rest"])]
        fields += [("note", text) for text in card.get("notes", [])]
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
        lines += card.get("notes", []) + [card.get("url", "")]
    return "\n".join(line for line in lines if line)
