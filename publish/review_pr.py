"""검토 PR 본문(Phase 3 Task 6·7). 검토 보고서·글 초안 뒤에 카드뉴스 미리보기, 생성 실패 사유, LinkedIn 게시문, 문구 반려 안내를 붙인다.
문구 재작성 중(copy-hold.txt)이면 맨 위에 보류 알림을 둔다.
새 절의 문안 정본은 docs/scripts/review-pr-script.md다. 조건이 여럿이라 워크플로 셸이 아니라 여기서 조립해 테스트한다.

    python -m publish.review_pr --day <날짜> --repo <owner/name> --sha <커밋 SHA>   → 표준 출력
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
SITE = "https://eugeejo-ui.github.io/consumption-insights"
WARN_OVER = 10                                       # 규칙 18: 장수 상한은 없고, 10장을 넘으면 경고만 남긴다
CARD_NAMES = {"cover": "표지", "price": "단가 변동 내역", "chart": "플랫폼별 월 사용료",
              "cost": "월 사용료 변동 내역", "rank": "순위 변동", "closing": "마무리 안내"}
POST_HEADING = "\n---\n## 글 초안 (post.md)\n\n"     # 기존 워크플로가 붙이던 형식 그대로
COPY_HOLD_FILE = "copy-hold.txt"                     # 첫 줄은 재작성 요청 Issue 주소. 상한을 넘으면 비어 있다(Task 7)


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def build_body(day: str, repo: str, sha: str, root: Path = Path("data/raw"), site: str = SITE) -> str:
    folder = Path(root) / day
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    body = folder.joinpath("review.md").read_text(encoding="utf-8")
    hold = _read(folder / COPY_HOLD_FILE)
    if hold is not None:                             # 머지 버튼을 누르기 전에 보이도록 검토 보고서보다 앞에 둔다
        body = env.get_template("review_pr_hold.md.j2").render(request_url=hold.strip()) + body
    post = _read(folder / "post.md")
    if post is not None:
        body += POST_HEADING + post
    images = []
    for png in sorted((folder / "cards").glob("[0-9][0-9]-*.png")):
        number, name = re.match(r"(\d+)-(\w+)\.png$", png.name).groups()
        images.append({"number": int(number), "name": CARD_NAMES[name],
                       "url": f"https://raw.githubusercontent.com/{repo}/{sha}/data/raw/{day}/cards/{png.name}"})
    errors = _read(folder / "card-errors.txt")
    linkedin = _read(folder / "linkedin.md")
    return body + env.get_template("review_pr.md.j2").render(
        images=images, warn_over=WARN_OVER,
        pdf_url=f"https://github.com/{repo}/blob/{sha}/data/raw/{day}/cards/cards.pdf",
        site_url=f"{site}/cards/{day}/cards.pdf",
        errors=errors.rstrip("\n") if errors else None, linkedin=linkedin.rstrip("\n") if linkedin else None)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="검토 PR 본문을 표준 출력으로 낸다")
    parser.add_argument("--day", required=True)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--sha", required=True, help="이미지 주소를 고정할 커밋 SHA")
    parser.add_argument("--root", default="data/raw")
    args = parser.parse_args(argv)
    sys.stdout.buffer.write(build_body(args.day, args.repo, args.sha, Path(args.root)).encode("utf-8"))


if __name__ == "__main__":
    main()
