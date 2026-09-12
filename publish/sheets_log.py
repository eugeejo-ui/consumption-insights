"""컨펌(검토 PR 머지) 뒤 가격 변동 이력을 사용자의 비공개 Google 스프레드시트에 쌓는다(Phase 2-2b).
- 인증: 서비스 계정 키 JSON(환경변수 GOOGLE_SA_KEY, GitHub Secret). 키 내용은 출력하거나 파일로 남기지 않는다.
- 시트: 환경변수 PRICE_SHEET_ID. 첫 번째 시트 탭의 A:J 열에 행을 덧붙인다.
- 정본은 Git의 CSV 스냅샷이고, 시트는 사용자가 보는 기록장이다."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote

from common.schema import PriceRecord, read_snapshot

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
APPEND_URL = "https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range}:append"
RANGE = "A:J"
HEADER = ["감지일", "비교 기준일", "플랫폼", "항목", "SKU", "리전", "이전 단가", "새 단가", "변동률(%)", "커밋"]


def _blank(v):
    return "" if v is None else v


def rows_from_events(events: dict, commit_url: str = "") -> list[list]:
    return [[events["day"], _blank(events["compared_to"]), c["platform"], c["service"], c["sku"], c["region"],
             _blank(c["before"]), _blank(c["after"]), _blank(c["change_pct"]), commit_url]
            for c in events["price_changes"] or []]


def baseline_rows(day: str, records: list[PriceRecord], commit_url: str = "") -> list[list]:
    """처음 연결할 때 한 번: 머리글 + 승인 스냅샷의 현재 단가(기준선)."""
    ordered = sorted(records, key=lambda r: (r.platform, r.service, r.sku, r.region))
    return [HEADER] + [[day, "기준선", r.platform, r.service, r.sku, r.region, "", r.price_usd, "", commit_url]
                       for r in ordered]


def append_rows(rows: list[list], sheet_id: str, session) -> int:
    if not rows:
        return 0
    url = APPEND_URL.format(sheet_id=quote(sheet_id, safe=""), range=quote(RANGE, safe=""))
    resp = _ok(session.post(url, params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                            json={"values": rows}, timeout=30), "시트 적재")
    return resp.json()["updates"]["updatedRows"]


def _ok(response, what: str):
    """실패하면 응답 본문까지 보여 준다. Google API는 이유를 본문에 적는다."""
    if not response.ok:
        raise SystemExit(f"{what} 실패 {response.status_code}: {response.text[:600]}")
    return response


def session_from_env():
    """GitHub Actions에서는 워크로드 아이덴티티가 준 자격을 쓴다(키 파일 없음).
    GOOGLE_SA_KEY가 있으면 그 서비스 계정 키를 쓴다(로컬 점검용)."""
    from google.auth.transport.requests import AuthorizedSession

    key = os.environ.get("GOOGLE_SA_KEY")
    if key:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(json.loads(key), scopes=SCOPES)
    else:
        import google.auth
        credentials, _ = google.auth.default(scopes=SCOPES)
    return AuthorizedSession(credentials)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="승인된 가격 변동을 Google 스프레드시트에 적재한다")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--events", type=Path, help="승인된 스냅샷의 events.json")
    group.add_argument("--baseline", metavar="DAY", help="처음 한 번: 승인 스냅샷 DAY의 단가를 기준선으로 기록")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args(argv)
    if args.events:
        rows = rows_from_events(json.loads(args.events.read_text(encoding="utf-8")), args.commit_url)
    else:
        folder = Path("data/raw") / args.baseline
        if not (folder / "approved.txt").exists():
            raise SystemExit(f"{args.baseline}는 승인된 스냅샷이 아니다.")
        records = [r for p in sorted(folder.glob("*.csv")) for r in read_snapshot(p)]
        rows = baseline_rows(args.baseline, records, args.commit_url)
    n = append_rows(rows, os.environ["PRICE_SHEET_ID"], session_from_env())
    print(f"시트에 {n}행을 추가했다.")
    return n


if __name__ == "__main__":
    main()
