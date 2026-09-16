"""파이프라인. 중간 검토 체크포인트(CLAUDE.md 규칙 14)가 있는 2단계 구조다.

1단계  .venv\\Scripts\\python.exe pipeline.py [--simulate]
       수집 → 이전 승인 스냅샷과 비교
       · 변화 없음: data/checks.csv에 한 줄 기록하고 끝낸다(스냅샷을 만들지 않는다)
       · 변화 있음(또는 첫 스냅샷): 스냅샷, review.md, events.json, (E1이면) post.md·linkedin.md·cards/ → 멈춤
         카드는 부가물이다. 카드·게시문이 실패해도 검토 자료는 남고, 사유는 card-errors.txt에 적는다
2단계  .venv\\Scripts\\python.exe pipeline.py --confirm <날짜>
       사용자가 검토 보고서를 컨펌한 뒤 실행한다. 사이트 생성 + 승인 기록(approved.txt) + 승인된 카드 복사
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shutil
from dataclasses import replace
from pathlib import Path

import yaml

from collectors import aws_prices, azure_prices, manual_prices
from common.schema import REGIONS, PriceRecord, read_snapshot, write_snapshot
from detect.events import detect
from model.tco import CostRow, PriceBook, estimate, ranking, seoul_premiums, t1_verdict, t2_verdict
from publish.card_data import intro_cards, price_change_cards
from publish.render_cards import INTRO, REPORT, bake
from publish.render_linkedin import render_intro_post, render_linkedin
from publish.render_post import render_post
from publish.render_site import render
from publish.review_pr import COPY_HOLD_FILE
from publish.review_report import (APPROVED_FILE, REVIEW_FILE, build_review, latest_approved_day,
                                   previous_snapshot)

RAW = Path("data/raw")
CHECKS = Path("data/checks.csv")
EVENTS_FILE = "events.json"
POST_FILE = "post.md"
CARDS_DIR = "cards"
LINKEDIN_FILE = "linkedin.md"
CARD_ERRORS_FILE = "card-errors.txt"
INTRO_DIR = Path("data/cards/intro")          # 소개 카드(날짜와 무관, D21). 로컬에서 굽고 실물 승인 후 커밋한다
SIMULATED = ("redshift", "compute", "us")     # --simulate: 이 단가만 5% 올려 검토 PR 흐름을 검증한다
SIMULATED_TAG = " (simulated)"
SIMULATION_NOTICE = "> **시뮬레이션:** 검증용 가짜 변동(Redshift 미국 RPU +5%)이다. 머지하지 말고 닫는다.\n\n"


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def analyze(records: list[PriceRecord]) -> dict:
    workloads = load_yaml("data/manual/workloads.yaml")
    thresholds = load_yaml("config/thresholds.yaml")
    book = PriceBook(records)
    premiums = seoul_premiums(records)
    return {
        "workloads": workloads,
        "thresholds": thresholds,
        "rows": estimate(book, workloads),
        "premiums": premiums,
        "t1_by_region": {region: t1_verdict(book, workloads, thresholds["t1_sensitivity"], region) for region in REGIONS},
        "t2": t2_verdict(premiums, thresholds["t2_min_spread_pp"]),
    }


def record_check(day: str, result: str, compared_to: str | None, path: Path = CHECKS) -> Path:
    """매일 확인 기록(day,result,compared_to). 같은 날 다시 실행하면 그 줄을 덮어쓴다."""
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["day"] != day]
    rows.append({"day": day, "result": result, "compared_to": compared_to or ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["day", "result", "compared_to"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["day"]))
    return path


def write_outputs(**values: str) -> None:
    """GitHub Actions 단계 출력(GITHUB_OUTPUT). 로컬에서는 아무것도 하지 않는다."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in values.items())


def simulate_change(records: list[PriceRecord], factor: float = 1.05) -> list[PriceRecord]:
    return [replace(r, price_usd=round(r.price_usd * factor, 6), source=r.source + SIMULATED_TAG)
            if (r.platform, r.service, r.region) == SIMULATED else r for r in records]


def dry_run() -> dict:
    """아무것도 쓰지 않고 오늘 가격과 판정만 확인한다(점검용)."""
    day = dt.date.today().isoformat()
    records = aws_prices.collect(day) + azure_prices.collect(day) + manual_prices.collect()
    result = analyze(records)
    compared_to = latest_approved_day(day, RAW)
    events = detect(day, records, previous_snapshot(day, RAW), compared_to, result["workloads"], result["thresholds"])
    print(f"[점검] {day} · 수집 {len(records)}행 · 비교 기준 {compared_to or '없음'} · 상태 {events['status']}"
          f" · 글 초안 대상 {'예' if events['significant'] else '아니오'}")
    for change in events["price_changes"] or []:
        print(f"  - {change['platform']} {change['sku']} {change['region']}: {change['before']} → {change['after']}")
    return events


def clear_card_outputs(folder: Path) -> None:
    """같은 날 다시 수집하면 앞선 실행의 카드와 게시문이 검토 PR에 섞이지 않게 먼저 지운다."""
    shutil.rmtree(folder / CARDS_DIR, ignore_errors=True)
    for name in (LINKEDIN_FILE, CARD_ERRORS_FILE):
        (folder / name).unlink(missing_ok=True)


def prepare_cards(events: dict, rows: list[CostRow], previous: list[PriceRecord] | None,
                  workloads: dict) -> tuple[list[dict] | None, str | None, list[str]]:
    """카드 데이터와 게시문 텍스트. events["display"]를 채우므로 events.json을 쓰기 전에 부른다.
    E1이 아니면 아무것도 만들지 않는다. 실패는 예외 대신 사유 목록으로 돌려준다(카드는 부가물이다)."""
    if not events["significant"]:
        return None, None, []
    cards, post, errors = None, None, []
    try:
        cards = price_change_cards(events, rows, estimate(PriceBook(previous), workloads), workloads)
    except ValueError as exc:
        errors.append(f"카드 데이터: {exc}")
    try:
        post = render_linkedin(events, workloads)
    except ValueError as exc:
        errors.append(f"게시문: {exc}")
    return cards, post, errors


def write_card_outputs(folder: Path, events: dict, cards: list[dict] | None, post: str | None,
                       errors: list[str]) -> str:
    """게시문을 쓰고 카드를 굽는다. 어떤 실패도 검토 자료를 막지 않는다. 결과 ok|failed|skipped를 돌려준다."""
    if post is not None:
        (folder / LINKEDIN_FILE).write_text(post, encoding="utf-8")
    baked = 0
    if cards is not None:
        try:
            bake(cards, folder / CARDS_DIR, REPORT, events)
            baked = len(cards)
        except Exception as exc:                    # 브라우저·글꼴·레이아웃 어느 실패든 검토 PR은 열려야 한다
            errors = [*errors, f"굽기: {exc}"]
            shutil.rmtree(folder / CARDS_DIR, ignore_errors=True)   # 도중에 실패한 반쪽 카드를 검토 PR에 올리지 않는다
    if errors:
        (folder / CARD_ERRORS_FILE).write_text("\n".join(errors) + "\n", encoding="utf-8")
        print(f"카드·게시문 생성 실패 {len(errors)}건. 사유: {folder / CARD_ERRORS_FILE}")
    status = "skipped" if not events["significant"] else "failed" if errors else "ok"
    write_outputs(cards=status, card_count=str(baked))
    return status


def collect_and_review(simulate: bool = False) -> Path:
    """1단계: 변화가 있으면 검토 자료까지만 만들고 멈춘다. 화면 생성과 커밋은 컨펌 이후에 한다."""
    day = dt.date.today().isoformat()
    if (RAW / day / APPROVED_FILE).exists():
        raise SystemExit(f"{day} 스냅샷은 이미 승인됐다. 같은 날 다시 수집하지 않는다.")
    # 세 수집기가 모두 성공한 뒤에만 쓴다(수동 가격표 게이트에서 멈추면 아무것도 남기지 않는다).
    collected = {
        "aws": aws_prices.collect(day),
        "azure": azure_prices.collect(day),
        "manual": manual_prices.collect(),
    }
    if simulate:
        collected["aws"] = simulate_change(collected["aws"])
    records = [r for recs in collected.values() for r in recs]
    result = analyze(records)
    compared_to = latest_approved_day(day, RAW)
    previous = previous_snapshot(day, RAW)
    events = detect(day, records, previous, compared_to, result["workloads"], result["thresholds"])
    write_outputs(day=day, status=events["status"], significant=str(events["significant"]).lower())

    if events["status"] == "unchanged":
        out = record_check(day, "unchanged", compared_to)
        print(f"변화 없음({compared_to} 승인 스냅샷과 같다). 기록: {out}")
        return out

    for name, recs in collected.items():
        write_snapshot(recs, day, name, root=RAW)
    folder = RAW / day
    review = folder / REVIEW_FILE
    text = build_review(day, records, events["price_changes"], result["rows"], result["t1_by_region"], result["t2"],
                        counts={name: len(recs) for name, recs in collected.items()},
                        significant=events["significant"])
    review.write_text((SIMULATION_NOTICE if simulate else "") + text, encoding="utf-8")
    clear_card_outputs(folder)
    cards, post, card_errors = prepare_cards(events, result["rows"], previous, result["workloads"])
    (folder / EVENTS_FILE).write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if events["significant"]:
        (folder / POST_FILE).write_text(render_post(events), encoding="utf-8")
    write_card_outputs(folder, events, cards, post, card_errors)
    if not simulate:
        record_check(day, "review", compared_to)
    print(f"검토 보고서: {review}")
    print(f"검토 후 컨펌: 검토 PR Merge, 또는 로컬에서 .venv\\Scripts\\python.exe pipeline.py --confirm {day}")
    return review


def snapshot_records(day: str) -> list[PriceRecord]:
    return [r for p in sorted((RAW / day).glob("*.csv")) for r in read_snapshot(p)]


def rebuild_cards(day: str) -> Path:
    """--cards DAY: 저장된 events.json으로 카드와 게시문을 다시 만든다(문안·템플릿을 고친 뒤 등).
    명시적으로 부른 명령이라 실패를 잡지 않고 드러낸다. 승인 기록은 건드리지 않는다."""
    folder = RAW / day
    events_path = folder / EVENTS_FILE
    if not events_path.exists():
        raise SystemExit(f"{events_path}가 없다. 1단계를 먼저 실행한다.")
    events = json.loads(events_path.read_text(encoding="utf-8"))
    if not events.get("significant"):
        raise SystemExit(f"{day}는 E1 이벤트가 아니다. 카드를 만들지 않는다.")
    result = analyze(snapshot_records(day))
    workloads = result["workloads"]
    previous = estimate(PriceBook(snapshot_records(events["compared_to"])), workloads)
    cards = price_change_cards(events, result["rows"], previous, workloads)
    post = render_linkedin(events, workloads)
    clear_card_outputs(folder)
    events_path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / LINKEDIN_FILE).write_text(post, encoding="utf-8")
    bake(cards, folder / CARDS_DIR, REPORT, events)
    print(f"cards written: {folder / CARDS_DIR} ({len(cards)}장)")
    return folder / CARDS_DIR


def rebuild_intro() -> Path:
    """--cards intro: 최신 승인 스냅샷으로 소개 카드와 소개 게시문을 data/cards/intro/에 만든다(Task 8).
    승인한 값만 쓴다(규칙 14). 승인 기록은 건드리지 않는다. 명시적으로 부른 명령이라 실패를 드러낸다."""
    day = latest_approved_day(dt.date.max.isoformat(), RAW)
    if day is None:
        raise SystemExit("승인된 스냅샷이 없다. 소개 카드는 승인한 값으로만 만든다.")
    cards, facts = intro_cards(analyze(snapshot_records(day)), day)
    post = render_intro_post(facts)
    bake(cards, INTRO_DIR, INTRO, facts)
    (INTRO_DIR / LINKEDIN_FILE).write_text(post, encoding="utf-8")
    print(f"intro cards written: {INTRO_DIR} ({len(cards)}장, {day} 승인 스냅샷 기준)")
    return INTRO_DIR


def publish_cards(site: Path = Path("site")) -> list[Path]:
    """승인된 날의 카드와 게시문을 site/cards/<날짜>/로, 소개 카드를 site/cards/intro/로 복사한다.
    승인 기록이 없는 날(반려·시뮬레이션)은 게시하지 않는다(규칙 14, D9). 소개 카드는 대화에서 실물을 승인한 뒤 커밋한다(D21)."""
    target = site / CARDS_DIR
    shutil.rmtree(target, ignore_errors=True)
    published = []
    days = sorted(p for p in RAW.iterdir() if p.is_dir()) if RAW.exists() else []
    for folder in days:
        if not (folder / APPROVED_FILE).exists() or not (folder / CARDS_DIR).is_dir():
            continue
        dest = target / folder.name
        shutil.copytree(folder / CARDS_DIR, dest)
        if (folder / LINKEDIN_FILE).exists():
            shutil.copy2(folder / LINKEDIN_FILE, dest / LINKEDIN_FILE)
        published.append(dest)
    if INTRO_DIR.is_dir():
        shutil.copytree(INTRO_DIR, target / "intro")
        published.append(target / "intro")
    return published


def previous_ranks(day: str, workloads: dict) -> dict:
    """이전 승인 스냅샷의 순위. 화면의 순위 변동 삼각형에 쓴다."""
    previous = previous_snapshot(day, RAW)
    if previous is None:
        return {}
    rows = estimate(PriceBook(previous), workloads)
    return {sid: {region: ranking(rows, sid, region) for region in REGIONS} for sid in workloads["scenarios"]}


def build_site(day: str | None = None) -> Path:
    """승인된 스냅샷으로 사이트만 다시 그린다. 승인 기록은 건드리지 않는다(게시 워크플로용)."""
    day = day or latest_approved_day("9999-12-31", RAW)
    if day is None:
        raise SystemExit("승인된 스냅샷이 없다. 검토 PR을 머지한 뒤에 게시한다.")
    if not (RAW / day / APPROVED_FILE).exists():
        raise SystemExit(f"{day}는 승인된 스냅샷이 아니다.")
    records = snapshot_records(day)
    result = analyze(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)
    out = render(result["rows"], result["premiums"], result["t1_by_region"], result["t2"], result["workloads"],
                 price_dates, built_on=day, prev_ranks=previous_ranks(day, result["workloads"]))
    cards = publish_cards(out.parent)
    write_outputs(day=day)                           # 게시 워크플로가 시트 적재에 넘긴다. 출력 문장을 파싱하지 않는다
    dated = [p for p in cards if p.name != "intro"]
    intro = " + 소개 카드" if len(dated) < len(cards) else ""
    print(f"site written: {out} ({day} 승인 스냅샷, 카드 {len(dated)}일분{intro})")
    return out


def confirm(day: str) -> Path:
    """2단계: 검토 보고서가 있는 스냅샷만 반영한다. 사이트를 만들고 승인 기록을 남긴다."""
    snapshot = RAW / day
    if not (snapshot / REVIEW_FILE).exists():
        raise SystemExit(f"{snapshot / REVIEW_FILE}가 없다. 검토 보고서가 없는 스냅샷은 반영하지 않는다(먼저 pipeline.py 실행).")
    if (snapshot / COPY_HOLD_FILE).exists():         # revise-copy 라벨이 붙은 PR을 머지해도 승인·게시하지 않는다(Task 7)
        raise SystemExit(f"{day}는 문구 재작성 중이다({COPY_HOLD_FILE}). 반영하지 않는다. 라벨을 떼면 보류가 풀린다.")
    records = snapshot_records(day)
    if any(r.source.endswith(SIMULATED_TAG) for r in records):
        raise SystemExit(f"{day}는 시뮬레이션 스냅샷이다. 반영하지 않는다.")
    result = analyze(records)
    price_dates: dict[str, str] = {}
    for r in records:
        price_dates[r.platform] = max(price_dates.get(r.platform, ""), r.fetched_at)
    out = render(result["rows"], result["premiums"], result["t1_by_region"], result["t2"], result["workloads"],
                 price_dates, built_on=day, prev_ranks=previous_ranks(day, result["workloads"]))
    (snapshot / APPROVED_FILE).write_text(f"approved_at: {dt.datetime.now().isoformat(timespec='seconds')}\n",
                                          encoding="utf-8")
    publish_cards(out.parent)                        # 승인 기록을 남긴 뒤라야 이날 카드도 포함된다
    print(f"site written: {out}")
    return out


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="1단계: 수집·비교·검토 자료 작성 후 멈춤 / 2단계: --confirm으로 반영")
    parser.add_argument("--confirm", metavar="DAY", help="검토 보고서를 컨펌한 스냅샷(DAY)으로 사이트를 만든다")
    parser.add_argument("--simulate", action="store_true", help="검증용 가짜 변동을 넣는다(검토 PR 흐름 확인용, 머지 금지)")
    parser.add_argument("--build", nargs="?", const="", metavar="DAY",
                        help="승인된 스냅샷(생략하면 가장 최근)으로 사이트만 다시 그린다. 게시 워크플로가 쓴다")
    parser.add_argument("--dry-run", action="store_true", help="아무것도 쓰지 않고 오늘 가격과 판정만 확인한다")
    parser.add_argument("--cards", metavar="DAY", help="저장된 events.json으로 그날 카드와 게시문을 다시 만든다(승인 기록은 바꾸지 않는다)")
    args = parser.parse_args(argv)
    if args.dry_run:
        return dry_run()
    if args.cards:
        return rebuild_intro() if args.cards == "intro" else rebuild_cards(args.cards)
    if args.confirm:
        return confirm(args.confirm)
    if args.build is not None:
        return build_site(args.build or None)
    return collect_and_review(simulate=args.simulate)


if __name__ == "__main__":
    main()
