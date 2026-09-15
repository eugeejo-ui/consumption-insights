"""카드뉴스 HTML과 굽기(Phase 3 Task 4). card_data의 장별 데이터를 1080×1350 PNG 여러 장과 PDF 1개로 만든다.
디자인은 사용자 템플릿과 docs/plans/phase3-card-design.md를 따른다. 틀 문구는 docs/scripts/cards-script.md가 정본이다.
굽기 전에 브라우저 실측으로 겹침·넘침·줄 수·한 음절 줄을 검사하고, 어긋나면 ValueError로 멈춘다."""
from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from html import unescape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from publish import browser
from publish.card_data import DASHBOARD, PLATFORM_LABELS, usd_label
from publish.render_post import check_numbers

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
REPORT = "가격 변동 리포트"                     # 우측 상단 라벨(스크립트 1절)
INTRO = "소개"
MIN_GAP = 24                                    # 본문 블록과 상단 바·하단 알약 사이 최소 여백(px)
ORPHAN_EM = 1.6                                 # 마지막 줄 폭이 글자 크기의 이 배수 미만이면 한 음절 줄로 본다
SIZE = (1080, 1350)
FILE_NAMES = {"cover": "cover", "chips": "units", "flow": "flow", "chart": "chart", "banners": "rank", "closing": "closing"}


def render_html(cards: list[dict], eyebrow: str, *, only: int | None = None, measure: bool = False) -> str:
    """only=n이면 n번째 장만 그린다. 마지막 장(`끝`) 판단은 전체 목록 기준이다. measure=True면 측정 스크립트를 넣는다."""
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters.update(usd=usd_label, platform=PLATFORM_LABELS.get, order=lambda s: s.replace(" › ", " › "))
    pages = [(n, card) for n, card in enumerate(cards, start=1) if only is None or n == only]
    return env.get_template("cards/cards.html.j2").render(
        pages=pages, total=len(cards), eyebrow=eyebrow, dashboard=DASHBOARD, measure=measure)


def visible_text(html: str) -> str:
    """화면에 보이는 글자. 스타일·스크립트와 쪽 표시 (1/2)를 뺀다(쪽 표시는 데이터가 아니라 장 순번이다)."""
    html = re.sub(r"<(style|script)\b.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r'<span class="page">.*?</span>', " ", html, flags=re.S)
    return unescape(re.sub(r"<[^>]+>", " ", html))


def read_layout(dom: str) -> list[dict]:
    found = re.search(r'<pre id="layout-report">(.*?)</pre>', dom, flags=re.S)
    if not found:
        raise RuntimeError("레이아웃 측정값을 찾지 못했다")
    return json.loads(unescape(found.group(1)))


def check_layout(report: list[dict], cards: list[dict]) -> dict:
    """디자인 계획 6절 검수 기준을 브라우저 실측값으로 검사한다. 하나라도 어긋나면 굽지 않는다.
    통과하면 요약(가장 좁은 여백, 가장 오른쪽 글자 끝)을 돌려준다. CI 기록에서 여유를 확인하는 데 쓴다."""
    problems = [] if len(report) == len(cards) else [f"측정한 장 수 {len(report)}가 카드 장수 {len(cards)}와 다르다"]
    for page in report:
        where = f"{page['card']}장({cards[page['card'] - 1]['kind']})"
        if page["gap_top"] < MIN_GAP:
            problems.append(f"{where} 본문이 상단 바와 겹친다(여백 {page['gap_top']}px, 최소 {MIN_GAP}px)")
        if page["gap_bottom"] < MIN_GAP:
            problems.append(f"{where} 본문이 하단 알약과 겹친다(여백 {page['gap_bottom']}px, 최소 {MIN_GAP}px)")
        for field in page["fields"]:
            role = field["role"]
            if field["lines"] > field["max"]:
                problems.append(f"{where} {role} 줄 수 {field['lines']}줄이 상한 {field['max']}줄을 넘는다")
            if field["right"] > page["limit_right"] + 1:
                problems.append(f"{where} {role} 글자가 본문 폭을 넘친다(오른쪽 끝 {field['right']}px)")
            if field["orphan_check"] and field["lines"] > 1 and field["last_em"] < ORPHAN_EM:
                problems.append(f"{where} {role} 마지막 줄에 한 음절만 남는다(폭 {field['last_em']}em)")
    if problems:
        raise ValueError("레이아웃 검사 실패:\n" + "\n".join(problems))
    return {"min_gap": min(min(p["gap_top"], p["gap_bottom"]) for p in report),
            "max_right": max(f["right"] for p in report for f in p["fields"]),
            "limit_right": min(p["limit_right"] for p in report)}


def korean_font_available() -> bool:
    """한글 글꼴이 있는가. 없으면 굽기가 실패하지 않고 두부 글자 카드가 만들어진다(CI 서버) [확인 2026-09-12]."""
    if sys.platform in ("win32", "darwin"):
        return True                                 # 맑은 고딕·Apple SD Gothic Neo가 기본으로 들어 있다 [지식]
    fc_list = shutil.which("fc-list")
    if fc_list is None:
        return False
    found = subprocess.run([fc_list, ":lang=ko"], capture_output=True, text=True, timeout=30)
    return bool(found.stdout.strip())


def _png_size(path: Path) -> tuple[int, int]:
    return struct.unpack(">II", path.read_bytes()[16:24])


def _pdf_pages(path: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![s])", path.read_bytes()))


def bake(cards: list[dict], out_dir: Path, eyebrow: str, events: dict) -> list[Path]:
    """cards.html, 장마다 PNG, cards.pdf를 만든다. 검사 순서: 글꼴 → 숫자 → 레이아웃 → 굽기 → 크기·쪽수."""
    if not korean_font_available():
        raise RuntimeError("한글 글꼴이 없다. 두부 글자 카드를 만들지 않는다(fonts-noto-cjk 설치 필요)")
    html = render_html(cards, eyebrow)
    check_numbers(visible_text(html), events)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in [*out_dir.glob("[0-9][0-9]-*.png"), out_dir / "cards.html", out_dir / "cards.pdf"]:
        old.unlink(missing_ok=True)                  # 같은 날 다시 구우면 장수가 줄 수 있다
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        work = Path(tmp)
        measure = work / "measure.html"
        measure.write_text(render_html(cards, eyebrow, measure=True), encoding="utf-8")
        summary = check_layout(read_layout(browser.dump_dom(measure)), cards)
        print(f"레이아웃 검사 통과: {len(cards)}장, 가장 좁은 여백 {summary['min_gap']}px, "
              f"가장 오른쪽 글자 끝 {summary['max_right']}/{summary['limit_right']}px")

        (out_dir / "cards.html").write_text(html, encoding="utf-8")
        pngs = []
        for n, card in enumerate(cards, start=1):
            page = work / f"{n:02d}.html"
            page.write_text(render_html(cards, eyebrow, only=n), encoding="utf-8")
            name = card.get("group") or FILE_NAMES[card["kind"]]
            png = browser.screenshot(page, out_dir / f"{n:02d}-{name}.png", *SIZE)
            if _png_size(png) != SIZE:
                raise ValueError(f"{png.name} 크기가 {_png_size(png)}다. {SIZE}여야 한다")
            pngs.append(png)
    pdf = browser.print_pdf(out_dir / "cards.html", out_dir / "cards.pdf")
    if _pdf_pages(pdf) != len(cards):
        raise ValueError(f"cards.pdf가 {_pdf_pages(pdf)}쪽이다. 장수 {len(cards)}와 같아야 한다")
    return [out_dir / "cards.html", *pngs, pdf]
