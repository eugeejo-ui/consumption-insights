"""중간 검토 보고서(review.md). 파이프라인 1단계가 만들고 멈춘다.
사용자가 판단해 컨펌하면 2단계(pipeline.py --confirm)가 화면 생성과 승인 기록을 한다(CLAUDE.md 규칙 14)."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from common.schema import REGIONS, PriceRecord, read_snapshot
from model.tco import CostRow

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
REVIEW_FILE = "review.md"
APPROVED_FILE = "approved.txt"
REGION_LABELS = {"us": "미국", "seoul": "서울"}


def _key(r: PriceRecord) -> tuple[str, str, str, str]:
    return (r.platform, r.service, r.sku, r.region)


def previous_snapshot(day: str, root: Path = Path("data/raw")) -> list[PriceRecord] | None:
    """day보다 앞선 가장 최근의 **승인된** 스냅샷을 읽는다. 승인 기록이 없는(반려된) 날은 건너뛴다."""
    root = Path(root)
    if not root.exists():
        return None
    approved = sorted(p for p in root.iterdir() if p.is_dir() and p.name < day and (p / APPROVED_FILE).exists())
    if not approved:
        return None
    return [r for csv_path in sorted(approved[-1].glob("*.csv")) for r in read_snapshot(csv_path)]


def price_changes(current: list[PriceRecord], previous: list[PriceRecord] | None) -> list[dict] | None:
    """이전 승인 스냅샷 대비 단가 변화. 비교 대상이 없으면 None(첫 스냅샷)을 돌려준다."""
    if previous is None:
        return None
    cur = {_key(r): r for r in current}
    prev = {_key(r): r for r in previous}
    changes = []
    for key in sorted(set(cur) | set(prev)):
        c, p = cur.get(key), prev.get(key)
        if c is not None and p is not None and c.price_usd == p.price_usd:
            continue
        changes.append({
            "platform": key[0], "service": key[1], "sku": key[2], "region": key[3],
            "before": p.price_usd if p else None, "after": c.price_usd if c else None,
            "change_pct": round((c.price_usd / p.price_usd - 1) * 100, 1) if c and p else None,
        })
    return changes


def build_review(day: str, records: list[PriceRecord], changes: list[dict] | None, rows: list[CostRow],
                 t1_by_region: dict[str, dict], t2: dict, counts: dict[str, int] | None = None) -> str:
    if changes is None:
        changes_summary = "첫 스냅샷 (비교할 승인 스냅샷이 없다)"
    elif not changes:
        changes_summary = "변화 없음"
    else:
        changes_summary = f"변화 {len(changes)}건"
    counts_text = f" ({', '.join(f'{name} {n}' for name, n in counts.items())})" if counts else ""
    rankings = []
    for sid in dict.fromkeys(r.scenario for r in rows):
        for region in REGIONS:
            ranked = sorted((r for r in rows if r.scenario == sid and r.region == region), key=lambda r: r.total_usd)
            rankings.append((sid, REGION_LABELS[region], [(r.platform, r.total_usd) for r in ranked]))
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    return env.get_template("review.md.j2").render(
        day=day, records=sorted(records, key=_key), changes=changes, changes_summary=changes_summary,
        counts_text=counts_text, rankings=rankings, t1_by_region=t1_by_region, t2=t2, region_labels=REGION_LABELS)
