"""가격 확인 알림(Phase 2-6).

- **BigQuery**: 가격 페이지를 하루 한 번 받아 **가격 문자열 지문만** 비교한다. Google 약관이 허용하고
  robots.txt도 이 경로를 막지 않는다 [확인 2026-09-12]. 지문이 바뀌면 Issue로 알리고, 사람이 표를 고친다.
- **Snowflake·Databricks**: 사이트 약관이 자동 모니터링을 금지한다. 자동으로 접근하지 않는다.
  수동 가격표의 확인일이 오래되면 "직접 확인하라"는 알림만 만든다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path

import requests

from collectors.manual_prices import collect as collect_manual

BIGQUERY_PRICING_URL = "https://cloud.google.com/bigquery/pricing"
USER_AGENT = "consumption-insights price watcher (+https://github.com/eugeejo-ui/consumption-insights)"
FINGERPRINT_FILE = Path("data/manual/bigquery_pricing_fingerprint.json")
# 가격처럼 생긴 문자열만 본다. 페이지의 nonce·스크립트 변화는 지문에 들어가지 않는다.
PRICE_TOKEN = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d+\.\d{4,}\b")
MANUAL_CHECK_DAYS = 90          # 분기 1회
VENDOR_PAGES = {
    "snowflake": "https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf",
    "databricks": "https://www.databricks.com/product/pricing",
    "bigquery": BIGQUERY_PRICING_URL,
}


def fetch_page(url: str = BIGQUERY_PRICING_URL) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def fingerprint(html: str) -> dict:
    tokens = sorted({token.replace(" ", "") for token in PRICE_TOKEN.findall(html)})
    return {"hash": hashlib.sha256("|".join(tokens).encode("utf-8")).hexdigest(), "tokens": len(tokens)}


def check_bigquery(day: str, fetch=fetch_page, path: Path = FINGERPRINT_FILE) -> dict:
    """지문을 비교한다. 처음이면 changed=False로 두고 기준만 만든다."""
    path = Path(path)
    current = fingerprint(fetch(BIGQUERY_PRICING_URL))
    stored = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return {
        "checked_on": day, "first": stored is None,
        "changed": stored is not None and stored["hash"] != current["hash"],
        "before": stored, "after": {**current, "checked_on": day},
    }


def save_fingerprint(result: dict, path: Path = FINGERPRINT_FILE) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result["after"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def stale_manual_prices(day: str, manual_dir: Path = Path("data/manual"), max_days: int = MANUAL_CHECK_DAYS) -> list[dict]:
    """확인일이 오래된 수동 가격표. 플랫폼마다 가장 오래된 확인일을 기준으로 삼는다."""
    today = dt.date.fromisoformat(day)
    oldest: dict[str, str] = {}
    for record in collect_manual(manual_dir):
        current = oldest.get(record.platform)
        oldest[record.platform] = record.fetched_at if current is None else min(current, record.fetched_at)
    stale = []
    for platform, confirmed_on in sorted(oldest.items()):
        days = (today - dt.date.fromisoformat(confirmed_on)).days
        if days >= max_days:
            stale.append({"platform": platform, "confirmed_on": confirmed_on, "days": days})
    return stale


def reminder_body(stale: list[dict], day: str) -> str:
    lines = [f"수동 가격표의 확인일이 {MANUAL_CHECK_DAYS}일을 넘었습니다. 공식 페이지를 직접 보고 값을 갱신해 주세요.", ""]
    for item in stale:
        page = VENDOR_PAGES.get(item["platform"], "")
        lines.append(f"- [ ] **{item['platform']}** · 마지막 확인 {item['confirmed_on']} ({item['days']}일 전) · {page}")
    lines += [
        "",
        "## 확인 방법",
        f"1. 위 링크에서 미국·서울 리전 단가를 확인합니다(기준일 {day}).",
        "2. `data/manual/<플랫폼>_prices.csv`의 `price_usd`와 `confirmed_on`을 고칩니다.",
        "3. 값이 바뀌었다면 다음 수집에서 검토 PR이 열립니다. 바뀌지 않았다면 확인일만 갱신하면 됩니다.",
        "",
        "Snowflake와 Databricks 사이트는 약관상 자동으로 확인할 수 없어 사람이 직접 봅니다.",
    ]
    return "\n".join(lines) + "\n"


def bigquery_issue_body(result: dict) -> str:
    before, after = result["before"], result["after"]
    return "\n".join([
        f"BigQuery 가격 페이지의 가격 문자열이 바뀌었습니다(확인일 {result['checked_on']}).",
        "",
        f"- 이전 지문: `{before['hash'][:16]}` · 가격 문자열 {before['tokens']}개 · 확인 {before.get('checked_on', '기록 없음')}",
        f"- 현재 지문: `{after['hash'][:16]}` · 가격 문자열 {after['tokens']}개",
        f"- 페이지: {BIGQUERY_PRICING_URL}",
        "",
        "## 확인 방법",
        "1. 페이지에서 미국·서울 리전의 슬롯 단가, 온디맨드 스캔 단가, 물리 스토리지 단가를 확인합니다.",
        "2. 바뀐 값이 있으면 `data/manual/bigquery_prices.csv`의 `price_usd`와 `confirmed_on`을 고칩니다.",
        "3. 지문만 바뀌고 우리가 쓰는 값은 그대로일 수 있습니다. 그때는 확인일만 갱신하고 이 Issue를 닫습니다.",
    ]) + "\n"


def write_outputs(**values: str) -> None:
    """GitHub Actions 단계 출력. 로컬에서는 아무것도 하지 않는다."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in values.items())


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="BigQuery 가격 지문 비교 + 수동 가격표 확인 알림")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Issue 본문을 쓸 폴더")
    parser.add_argument("--day", default=dt.date.today().isoformat())
    args = parser.parse_args(argv)

    result = check_bigquery(args.day)
    save_fingerprint(result)
    stale = stale_manual_prices(args.day)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if result["changed"]:
        (args.out_dir / "bigquery_issue.md").write_text(bigquery_issue_body(result), encoding="utf-8")
    if stale:
        (args.out_dir / "vendor_reminder.md").write_text(reminder_body(stale, args.day), encoding="utf-8")
    write_outputs(day=args.day, bigquery_changed=str(result["changed"]).lower(), stale_count=str(len(stale)),
                  quarter=f"{args.day[:4]}년 {(int(args.day[5:7]) - 1) // 3 + 1}분기")
    print(f"BigQuery 지문: {'바뀜' if result['changed'] else ('기준 생성' if result['first'] else '그대로')}"
          f" · 확인일이 오래된 가격표: {len(stale)}건")
    return {"bigquery": result, "stale": stale}


if __name__ == "__main__":
    main()
