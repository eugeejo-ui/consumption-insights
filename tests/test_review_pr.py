import re
from pathlib import Path

from publish.review_pr import CARD_NAMES, build_body

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "docs" / "scripts" / "review-pr-script.md"
DAY = "2026-09-15"
LINKEDIN = "데이터 플랫폼 월 비용 변동 · 2026-09-15\n\n#데이터플랫폼 #FinOps\n"


def _day(root, cards=5, errors=None, linkedin=True, post=True):
    """검토 PR에 올라가는 파일을 만든다. 카드 파일 이름은 굽기와 같은 NN-이름.png 형식이다."""
    folder = root / DAY
    folder.mkdir(parents=True)
    (folder / "review.md").write_text("# 중간 검토 보고서\n본문\n", encoding="utf-8")
    if post:
        (folder / "post.md").write_text("# 글 초안\n본문\n", encoding="utf-8")
    if cards:
        (folder / "cards").mkdir()
        middle = ["price", "chart", "cost"] * 4
        for n in range(1, cards + 1):
            name = "cover" if n == 1 else "closing" if n == cards else middle[n - 2]
            (folder / "cards" / f"{n:02d}-{name}.png").write_bytes(b"png")
        (folder / "cards" / "cards.pdf").write_bytes(b"pdf")
    if errors:
        (folder / "card-errors.txt").write_text(errors, encoding="utf-8")
    if linkedin:
        (folder / "linkedin.md").write_text(LINKEDIN, encoding="utf-8")
    return root


def _body(root):
    return build_body(DAY, "owner/repo", "abc123", root=root)


def test_body_shows_review_post_cards_and_linkedin_in_order(tmp_path):
    body = _body(_day(tmp_path))

    marks = ["# 중간 검토 보고서", "## 글 초안 (post.md)", "## 카드뉴스 미리보기 · 5장", "## LinkedIn 게시문"]
    positions = [body.index(mark) for mark in marks]
    assert positions == sorted(positions)
    raw = "https://raw.githubusercontent.com/owner/repo/abc123/data/raw/2026-09-15/cards"
    images = re.findall(r"^!\[(.+?)\]\((.+?)\)$", body, flags=re.M)
    assert images == [("1장 표지", f"{raw}/01-cover.png"), ("2장 단가 변동 내역", f"{raw}/02-price.png"),
                      ("3장 플랫폼별 월 사용료", f"{raw}/03-chart.png"), ("4장 월 사용료 변동 내역", f"{raw}/04-cost.png"),
                      ("5장 마무리 안내", f"{raw}/05-closing.png")]
    assert "원본 PDF: [cards.pdf](https://github.com/owner/repo/blob/abc123/data/raw/2026-09-15/cards/cards.pdf)" in body
    assert "머지 후 게시 주소: https://eugeejo-ui.github.io/consumption-insights/cards/2026-09-15/cards.pdf" in body
    assert f"```text\n{LINKEDIN.rstrip()}\n```" in body


def test_body_has_no_card_section_on_a_non_e1_day(tmp_path):
    body = _body(_day(tmp_path, cards=0, linkedin=False, post=False))
    assert body == "# 중간 검토 보고서\n본문\n"                        # 검토 보고서만 그대로 올린다


def test_card_failure_is_shown_with_its_reason(tmp_path):
    reason = "굽기: 한글 글꼴이 없다. 두부 글자 카드를 만들지 않는다(fonts-noto-cjk 설치 필요)\n"
    body = _body(_day(tmp_path, cards=0, errors=reason))
    assert "## 카드뉴스·게시문 생성 실패" in body
    assert f"```text\n{reason.rstrip()}\n```" in body                     # 요약하지 않고 원문 그대로
    assert "카드뉴스 미리보기" not in body
    assert "## LinkedIn 게시문" in body                                   # 게시문은 만들어졌으면 싣는다


def test_more_than_ten_cards_adds_a_warning(tmp_path):
    warning = "카드가 11장으로 10장을 넘습니다. 게시 분량은 검토자가 판단합니다."
    assert warning in _body(_day(tmp_path / "eleven", cards=11))
    assert "10장을 넘습니다" not in _body(_day(tmp_path / "ten", cards=10))


def test_fixed_copy_matches_the_script(tmp_path):
    """본문의 고정 문장이 확정 스크립트와 글자 단위로 같다. 자리표시자 {…} 자리에는 무엇이 와도 된다."""
    script = SCRIPT.read_text(encoding="utf-8")
    table = dict(re.findall(r"^\| `(\w+)` \| (.+?) \|$", script.split("## 1. 장 이름")[1].split("## 2.")[0], flags=re.M))
    assert table == CARD_NAMES

    body = _body(_day(tmp_path, cards=11, errors="굽기: 실패 사유\n"))
    sections = script.split("## 2.")[1].split("## 5.")[0]
    blocks = [m.group(2) for m in re.finditer(r"^(`{3,4})\n(.*?)^\1$", sections, flags=re.S | re.M)]
    assert len(blocks) == 3
    for block in blocks:
        for line in block.splitlines():
            line = re.sub(r"^\[.+?\] ", "", line.split("      ←")[0]).rstrip()   # 출력 조건 표시와 설명을 뗀다
            if not line or line.startswith("```"):
                continue
            pattern = re.sub(r"\\\{.+?\\\}", ".+?", re.escape(line))
            assert re.search(f"^{pattern}$", body, flags=re.M), line
