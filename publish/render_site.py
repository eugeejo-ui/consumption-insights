"""TCO 결과를 정적 HTML(site/index.html)로 만든다. 차트는 Plotly(CDN).
Phase 1의 기능 확인용 임시 디자인이다. 공개 대시보드 디자인은 Phase 2-5a에서 사용자 템플릿을 바탕으로 정한다."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs_version

from model.tco import PLATFORMS, CostRow

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "site"
REGION_LABELS = {"us": "미국", "seoul": "서울"}


def cost_chart(rows: list[CostRow], scenario: str) -> str:
    fig = go.Figure()
    for region in ("us", "seoul"):
        selected = {r.platform: r for r in rows if r.scenario == scenario and r.region == region}
        fig.add_bar(name=REGION_LABELS[region], x=list(PLATFORMS), y=[round(selected[p].total_usd, 2) for p in PLATFORMS])
    fig.update_layout(barmode="group", yaxis_title="USD / month", height=320, margin=dict(l=40, r=10, t=30, b=30))
    return fig.to_html(full_html=False, include_plotlyjs=False)


def render(rows: list[CostRow], premiums: list[dict], t1_by_region: dict[str, dict], t2: dict, workloads: dict,
           price_dates: dict[str, str], built_on: str, out_dir: Path = Path("site")) -> Path:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template("index.html.j2").render(
        rows=rows, premiums=premiums, t1_by_region=t1_by_region, t2=t2, workloads=workloads,
        charts={sid: cost_chart(rows, sid) for sid in workloads["scenarios"]},
        price_dates=price_dates, built_on=built_on, region_labels=REGION_LABELS,
        plotly_cdn=f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js",
    )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
