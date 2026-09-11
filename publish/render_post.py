"""E1 이벤트 글 초안(Phase 2-3). 템플릿 문장에 events.json 값만 넣는다.
게시 전 검사: 글에 나온 모든 숫자가 events.json에 있어야 한다(표시 반올림 허용). 없으면 ValueError."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from publish.review_report import REGION_LABELS

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
PLATFORM_LABELS = {"snowflake": "Snowflake", "databricks": "Databricks", "redshift": "Redshift", "bigquery": "BigQuery"}
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")   # W1 같은 식별자 속 숫자는 제외한다


def _price(v: float | None) -> str:
    return "없음" if v is None else "$" + f"{v:.6f}".rstrip("0").rstrip(".")


def check_numbers(post: str, events: dict) -> None:
    allowed = [float(t.replace(",", "")) for t in NUMBER.findall(json.dumps(events, ensure_ascii=False))]
    for token in NUMBER.findall(post):
        value = float(token.replace(",", ""))
        decimals = len(token.split(".")[1]) if "." in token else 0
        if not any(round(a, decimals) == value for a in allowed):
            raise ValueError(f"글의 숫자 {token}이(가) events.json에 없다")


def render_post(events: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters.update(
        platform=PLATFORM_LABELS.get, region=REGION_LABELS.get, price=_price,
        usd0=lambda v: f"${v:,.0f}", pct=lambda v: "" if v is None else f" ({v:+.1f}%)",
        num=lambda v: f"{v:g}", order=lambda ps: " > ".join(PLATFORM_LABELS[p] for p in ps))
    post = env.get_template("post_price_change.md.j2").render(e=events)
    check_numbers(post, events)
    return post
