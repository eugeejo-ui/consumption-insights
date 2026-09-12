"""TCO 결과를 정적 HTML(site/index.html) 한 장으로 만든다.

디자인은 사용자가 준 Figma 대시보드 템플릿을 따른다(2-5a 결정 D4~D6).
- 차트는 CSS 막대다(템플릿의 트랙 + 라운드 캡을 재현하고, 외부 차트 라이브러리를 쓰지 않는다).
- 글꼴은 시스템 글꼴이고, 외부 요청과 외부 이미지는 없다.
- 리전·시나리오 전환은 페이지 안의 작은 스크립트로 한다(패널을 미리 그려 두고 보이기만 바꾼다).
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from model.tco import CostRow

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "site"
REGION_LABELS = {"us": "미국", "seoul": "서울"}
PLATFORM_LABELS = {"snowflake": "Snowflake", "databricks": "Databricks", "redshift": "Redshift", "bigquery": "BigQuery"}
PLATFORM_COLORS = {"snowflake": "#29B5E8", "databricks": "#E8442C", "redshift": "#8C4FFF", "bigquery": "#4285F4"}
REPO_URL = "https://github.com/eugeejo-ui/consumption-insights"


def _delta(platform: str, rank: int, prev_order: list[str] | None) -> str:
    """이전 승인 스냅샷 대비 순위 변동. 비교 대상이 없으면 none."""
    if not prev_order or platform not in prev_order:
        return "none"
    before = prev_order.index(platform) + 1
    if before == rank:
        return "flat"
    return "up" if rank < before else "down"


def ranking(rows: list[CostRow], scenario: str, region: str, prev_order: list[str] | None = None) -> list[dict]:
    selected = sorted((r for r in rows if r.scenario == scenario and r.region == region), key=lambda r: r.total_usd)
    top = selected[-1].total_usd if selected else 0.0

    def pct(value: float) -> float:
        return round(value / top * 100, 1) if top else 0.0

    return [{
        "rank": i, "platform": r.platform, "label": PLATFORM_LABELS[r.platform], "color": PLATFORM_COLORS[r.platform],
        "compute": r.compute_usd, "storage": r.storage_usd, "total": r.total_usd,
        "total_pct": pct(r.total_usd), "compute_pct": pct(r.compute_usd), "storage_pct": pct(r.storage_usd),
        "delta": _delta(r.platform, i, prev_order),
    } for i, r in enumerate(selected, start=1)]


def panels(rows: list[CostRow], workloads: dict, prev_ranks: dict | None = None) -> list[dict]:
    """시나리오 × 리전 패널. 필터가 이 중 하나만 보여 준다."""
    prev_ranks = prev_ranks or {}
    out = []
    for sid, scenario in workloads["scenarios"].items():
        for region in REGION_LABELS:
            # 키 이름에 items/keys/values를 쓰지 않는다. Jinja에서 dict 메서드와 부딪힌다.
            bars = ranking(rows, sid, region, (prev_ranks.get(sid) or {}).get(region))
            cheapest, priciest = bars[0], bars[-1]
            top = priciest["total"]
            out.append({
                "id": f"{sid}|{region}", "scenario": sid, "region": region,
                "scenario_name": scenario.get("name", sid), "region_label": REGION_LABELS[region],
                "bars": bars, "cheapest": cheapest, "priciest": priciest,
                "gap_pct": round((top / cheapest["total"] - 1) * 100, 1) if cheapest["total"] else 0.0,
                "ticks": [top, top * 2 / 3, top / 3, 0],
                "rankings": [{"region_label": REGION_LABELS[r],
                              "rows": ranking(rows, sid, r, (prev_ranks.get(sid) or {}).get(r))}
                             for r in REGION_LABELS],
            })
    return out


def render(rows: list[CostRow], premiums: list[dict], t1_by_region: dict[str, dict], t2: dict, workloads: dict,
           price_dates: dict[str, str], built_on: str, prev_ranks: dict | None = None,
           out_dir: Path = Path("site")) -> Path:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    ordered = sorted(premiums, key=lambda p: p["premium_pct"], reverse=True)
    html = env.get_template("index.html.j2").render(
        panels=panels(rows, workloads, prev_ranks),
        premiums=ordered, premium_high=ordered[:3], premium_low=list(reversed(ordered[-3:])),
        premium_max=max((abs(p["premium_pct"]) for p in ordered), default=1.0),
        t1_by_region=t1_by_region, t2=t2, workloads=workloads, price_dates=price_dates, built_on=built_on,
        region_labels=REGION_LABELS, platform_labels=PLATFORM_LABELS, platform_colors=PLATFORM_COLORS,
        repo_url=REPO_URL, snapshot_url=f"{REPO_URL}/tree/main/data/raw/{built_on}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
