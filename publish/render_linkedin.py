"""LinkedIn 정기 게시문(Phase 3 Task 3)과 소개 게시문(Task 8). 문안의 정본은 docs/scripts/linkedin-post-script.md다.
게시는 사람이 한다(LinkedIn 약관). 이 모듈은 텍스트만 만든다. 바뀐 단가를 한 줄도 빠뜨리지 않고(규칙 18),
3,000자를 넘으면 항목을 자르지 않고 멈춘다. 카드와 독립적으로 만든다(카드가 실패해도 게시문은 남는다)."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from publish.card_data import DASHBOARD, REGION_LABELS, note_price_change_count, price_item, scenario_names
from publish.render_post import check_numbers

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
DASHBOARD_URL = f"https://{DASHBOARD}/"
MAX_CHARS = 3000                                                     # LinkedIn 본문 한도


def render_linkedin(events: dict, workloads: dict) -> str:
    names = scenario_names(workloads)
    count = note_price_change_count(events)
    top = max(events["cost_changes"], key=lambda c: abs(c["change_pct"]), default=None)   # 동률이면 목록의 첫 항목
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    text = env.get_template("post_linkedin.md.j2").render(
        e=events, count=count, items=[price_item(c) for c in events["price_changes"]], url=DASHBOARD_URL,
        top=top and {"scenario": names[top["scenario"]], "region": REGION_LABELS[top["region"]]})
    check_numbers(text, events)
    return _within_limit(text)


def render_intro_post(facts: dict) -> str:
    """소개 게시문(스크립트 2절, Task 8). events.json 없이 승인 스냅샷으로 만든다.
    리전 최대 차이는 소개 카드가 쓰는 사전(intro_cards의 facts)에서 받는다. 게시문에 숫자를 적어 두지 않는다."""
    gap = max(rise for _, _, rise in facts["region_costs"])
    if gap <= 0:                                                     # `최대 … 높습니다`가 거짓이 된다
        raise ValueError(f"서울 리전이 더 비싼 워크로드가 없다(최대 {gap:+.1f}%). 소개 게시문을 만들지 않는다")
    env = Environment(loader=FileSystemLoader(TEMPLATES), keep_trailing_newline=True)
    text = env.get_template("post_linkedin_intro.md.j2").render(url=DASHBOARD_URL, region_gap=f"{gap:.1f}%")
    check_numbers(text, facts)                                       # 카드와 다른 숫자를 말하지 않는다
    return _within_limit(text)


def _within_limit(text: str) -> str:
    if len(text) > MAX_CHARS:
        raise ValueError(f"게시문이 {len(text):,}자라 LinkedIn 한도 {MAX_CHARS:,}자를 넘는다. 항목을 자르지 않고 생성을 멈춘다")
    return text
