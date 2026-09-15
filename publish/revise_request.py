"""문구 재작성 요청(Phase 3 Task 7). 검토 PR에 revise-copy 라벨이 붙으면 워크플로가 이 모듈로 요청 Issue를 만든다.
문안 정본: docs/scripts/revise-request-script.md(요청 Issue·처리 코멘트), docs/scripts/review-pr-script.md 7절(상한 코멘트).
PR 코멘트는 공개 저장소의 외부 입력이다. 워크플로 셸에 넣지 않고, gh api 응답 파일을 여기서 읽는다.

    python -m publish.revise_request pending-day                                  → 검토 중인 날짜
    python -m publish.revise_request request --day --repo --pr --issues <json> --comments <json> --out <폴더>
        → <폴더>/round 에 회차. 상한 이내면 title.txt·body.md, 넘으면 limit.md
"""
from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from publish.review_pr import CARD_NAMES

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
MAX_ROUNDS = 3                                        # 규칙 16: 같은 지적이 세 번 반복되면 스킬로 풀리는 문제가 아니다
TRUSTED = {"OWNER", "MEMBER", "COLLABORATOR"}         # 이 권한의 코멘트만 반려 사유로 싣는다(외부인의 지시 주입 차단)
TITLE = "문구 재작성 요청 {day} ({round}회차)"
LIMIT_COMMENT = f"자동 재작성 상한({MAX_ROUNDS}회)에 도달했습니다. 문안은 사람이 직접 수정합니다."
PROCEDURE = "docs/scripts/revise-loop.md"
_BLOCK_END = re.compile(r"<br\s*/?>|</(?:p|h1|h2|li|div)>", flags=re.I)


def pending_day(root: Path = Path("data/raw")) -> str:
    """검토 브랜치에서 승인 기록이 없는 가장 최근 검토 날짜. 검토 브랜치는 main에 그날 폴더 하나를 더한 것이다."""
    days = [d.name for d in Path(root).iterdir()
            if (d / "review.md").exists() and not (d / "approved.txt").exists()]
    if not days:
        raise SystemExit(f"{root}에 승인되지 않은 검토 스냅샷이 없다.")
    return max(days)


def previous_requests(issues: list[dict], day: str) -> list[dict]:
    """그날의 기존 재작성 요청. 워크플로는 copy-revision 라벨로 조회하고, 여기서 제목의 날짜로 거른다(PR은 뺀다)."""
    prefix = TITLE.format(day=day, round="").split("(")[0] + "("
    return [issue for issue in issues if "pull_request" not in issue and issue["title"].startswith(prefix)]


def reasons(comments: list[dict], since: str | None = None) -> list[dict]:
    """반려 사유 코멘트: 권한 있는 사람이 쓰고, 봇이 아니고, 직전 회차 요청 뒤에 남긴 것."""
    return [c for c in comments
            if c.get("author_association") in TRUSTED and (c.get("user") or {}).get("type") != "Bot"
            and (since is None or c["created_at"] > since)]


def card_texts(html: str) -> list[str]:
    """cards.html의 장마다 보이는 글자를 줄 단위로 뽑는다. 서식과 쪽 표시 (1/2)는 뺀다."""
    texts = []
    for section in re.findall(r'<section class="card".*?</section>', html, flags=re.S):
        section = re.sub(r'<span class="page">.*?</span>', "", section, flags=re.S)
        section = re.sub(r"</?em\b[^>]*>", "", section)   # 강조는 글자 사이에 있다(대시보드</em>에). 공백을 넣지 않는다
        section = unescape(re.sub(r"<[^>]+>", " ", _BLOCK_END.sub("\n", section)))
        lines = (" ".join(line.split()) for line in section.splitlines())
        texts.append("\n".join(line for line in lines if line))
    return texts


def _cards(folder: Path) -> list[dict]:
    html = folder / "cards" / "cards.html"
    if not html.exists():
        return []
    pngs = sorted((folder / "cards").glob("[0-9][0-9]-*.png"))
    texts = card_texts(html.read_text(encoding="utf-8"))
    if len(pngs) != len(texts):
        raise ValueError(f"카드 이미지 {len(pngs)}장과 cards.html의 {len(texts)}장이 다르다")
    return [{"number": int(png.name[:2]), "name": CARD_NAMES[png.stem[3:]], "text": text}
            for png, text in zip(pngs, texts)]


def _time(stamp: str) -> str:
    return stamp[:16].replace("T", " ") + " UTC"          # 2026-09-15T10:42:31Z → 2026-09-15 10:42 UTC


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)


def build_request(day: str, round_: int, repo: str, pr: int, comments: list[dict],
                  root: Path = Path("data/raw"), since: str | None = None) -> tuple[str, str]:
    folder = Path(root) / day
    linkedin = folder / "linkedin.md"
    items = [{"time": _time(c["created_at"]),
              "quote": "\n".join(f"> {line}".rstrip() for line in c["body"].replace("\r\n", "\n").strip().split("\n"))}
             for c in reasons(comments, since)]
    body = _env().get_template("revise_request.md.j2").render(
        pr_url=f"https://github.com/{repo}/pull/{pr}", round=round_, max_rounds=MAX_ROUNDS, reasons=items,
        cards=_cards(folder), linkedin=linkedin.read_text(encoding="utf-8").rstrip("\n") if linkedin.exists() else None,
        procedure_url=f"https://github.com/{repo}/blob/main/{PROCEDURE}")
    return TITLE.format(day=day, round=round_), body


def close_comment(commit_url: str, change_rate: str) -> str:
    """Claude가 재작성을 마치고 요청 Issue를 닫을 때 남기는 코멘트."""
    return (f"재작성을 반영했습니다. 검토 PR을 새 카드와 게시문으로 갱신했습니다.\n\n"
            f"문안 변경: {commit_url}\n\n변경률: {change_rate}\n")


def load_pages(text: str) -> list:
    """gh api --paginate는 쪽마다 JSON 배열을 이어 붙여 낸다. 이어 붙은 배열을 하나로 편다."""
    decoder, items, i = json.JSONDecoder(), [], 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        value, i = decoder.raw_decode(text, i)
        items.extend(value if isinstance(value, list) else [value])
    return items


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="문구 재작성 요청 Issue 본문을 만든다")
    sub = parser.add_subparsers(dest="command", required=True)
    day_parser = sub.add_parser("pending-day")
    day_parser.add_argument("--root", default="data/raw")
    req = sub.add_parser("request")
    req.add_argument("--day", required=True)
    req.add_argument("--repo", required=True, help="owner/name")
    req.add_argument("--pr", required=True, type=int)
    req.add_argument("--issues", required=True, help="copy-revision 라벨 Issue 목록(gh api 응답)")
    req.add_argument("--comments", required=True, help="검토 PR 코멘트 목록(gh api 응답)")
    req.add_argument("--out", required=True)
    req.add_argument("--root", default="data/raw")
    args = parser.parse_args(argv)
    if args.command == "pending-day":
        print(pending_day(Path(args.root)))
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    previous = previous_requests(load_pages(Path(args.issues).read_text(encoding="utf-8")), args.day)
    round_ = len(previous) + 1
    (out / "round").write_text(f"{round_}\n", encoding="utf-8")
    if round_ > MAX_ROUNDS:
        (out / "limit.md").write_text(LIMIT_COMMENT + "\n", encoding="utf-8")
        return
    since = max((issue["created_at"] for issue in previous), default=None)
    title, body = build_request(args.day, round_, args.repo, args.pr,
                                load_pages(Path(args.comments).read_text(encoding="utf-8")), Path(args.root), since)
    (out / "title.txt").write_text(title + "\n", encoding="utf-8")
    (out / "body.md").write_text(body, encoding="utf-8")


if __name__ == "__main__":
    main()
