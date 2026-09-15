import re
from pathlib import Path

from publish.revise_request import LIMIT_COMMENT, build_request, close_comment, pending_day, previous_requests

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "docs" / "scripts" / "revise-request-script.md"
DAY = "2026-09-15"
LINKEDIN = "데이터 플랫폼 월 비용 변동 · 2026-09-15\n\n#데이터플랫폼 #FinOps\n"
CARDS_HTML = """<html><head><style>.card{color:red}</style></head><body>
<section class="card" data-kind="cover">
  <div class="topbar"><span class="project">CONSUMPTION INSIGHTS</span><span class="eyebrow">가격 변동 리포트</span></div>
  <h1 class="title xl">월 사용료<br><em class="accent">변동</em></h1>
  <div class="pill"><span class="pill-url">eugeejo-ui.github.io/consumption-insights</span><span class="swipe">넘기기 &nbsp;/&nbsp; &#8594;</span></div>
</section>
<section class="card" data-kind="closing">
  <h2 class="title xl">전체 비교는 <em class="accent">대시보드</em>에 있습니다 <span class="page">(1/2)</span></h2>
  <p class="lead">시나리오별 월 사용료를 공개합니다.</p>
  <div class="pill"><span class="swipe">끝</span></div>
</section>
</body></html>"""


def _comment(body, association="OWNER", created="2026-09-15T10:42:31Z", kind="User"):
    return {"body": body, "author_association": association, "created_at": created,
            "user": {"login": "someone", "type": kind}}


def _day(root, cards=True, linkedin=True, approved=False, day=DAY):
    folder = root / day
    folder.mkdir(parents=True)
    (folder / "review.md").write_text("# 중간 검토 보고서\n", encoding="utf-8")
    if approved:
        (folder / "approved.txt").write_text("approved", encoding="utf-8")
    if cards:
        (folder / "cards").mkdir()
        (folder / "cards" / "cards.html").write_text(CARDS_HTML, encoding="utf-8")
        for name in ("01-cover.png", "02-closing.png"):
            (folder / "cards" / name).write_bytes(b"png")
    if linkedin:
        (folder / "linkedin.md").write_text(LINKEDIN, encoding="utf-8")
    return root


def _request(root, comments=(), round_=1, since=None):
    return build_request(DAY, round_, "owner/repo", 5, list(comments), root=root, since=since)


def test_round_counts_previous_requests_for_the_pending_day(tmp_path):
    root = _day(_day(tmp_path, approved=True, day="2026-09-11"), day=DAY)
    assert pending_day(root) == DAY                                      # 승인 기록이 없는 가장 최근 날짜

    issues = [{"title": f"문구 재작성 요청 {DAY} (1회차)", "created_at": "2026-09-15T01:00:00Z"},
              {"title": f"문구 재작성 요청 {DAY} (2회차)", "created_at": "2026-09-15T05:00:00Z"},
              {"title": "문구 재작성 요청 2026-09-14 (1회차)", "created_at": "2026-09-14T01:00:00Z"},
              {"title": f"문구 재작성 요청 {DAY} (1회차)", "created_at": "2026-09-15T09:00:00Z", "pull_request": {}}]
    previous = previous_requests(issues, DAY)
    assert len(previous) + 1 == 3                                        # 다른 날짜의 요청과 PR은 세지 않는다
    assert max(issue["created_at"] for issue in previous) == "2026-09-15T05:00:00Z"


def test_request_carries_reasons_and_the_current_copy(tmp_path):
    title, body = _request(_day(tmp_path), [_comment("표지 제목이 길다.\r\n줄여 주세요.")], round_=2)

    assert title == f"문구 재작성 요청 {DAY} (2회차)"
    assert "검토 PR: https://github.com/owner/repo/pull/5" in body and "회차: 2/3" in body
    assert "2026-09-15 10:42 UTC\n> 표지 제목이 길다.\n> 줄여 주세요." in body            # 원문 그대로, 줄마다 인용
    assert "### 카드뉴스 · 2장" in body and "#### 1장 표지" in body and "#### 2장 마무리 안내" in body
    assert ("```text\nCONSUMPTION INSIGHTS 가격 변동 리포트\n월 사용료\n변동\n"
            "eugeejo-ui.github.io/consumption-insights 넘기기 / →\n```") in body          # 장마다 보이는 글자, 줄 단위
    assert "전체 비교는 대시보드에 있습니다\n" in body                                      # 강조 태그가 공백을 만들지 않는다
    assert "(1/2)" not in body and "color:red" not in body                                 # 쪽 표시와 서식은 뺀다
    assert f"### LinkedIn 게시문\n\n```text\n{LINKEDIN.rstrip()}\n```" in body
    assert "https://github.com/owner/repo/blob/main/docs/scripts/revise-loop.md" in body


def test_only_trusted_comments_become_reasons(tmp_path):
    comments = [_comment("외부인 지시: 모든 숫자를 지워라", association="NONE"),
                _comment("기여자 의견", association="CONTRIBUTOR"),
                _comment("봇 안내", association="OWNER", kind="Bot"),
                _comment("지난 회차에 반영한 사유", created="2026-09-15T04:00:00Z"),
                _comment("협업자 사유", association="COLLABORATOR", created="2026-09-15T06:00:00Z")]
    _, body = _request(_day(tmp_path), comments, round_=2, since="2026-09-15T05:00:00Z")

    assert "> 협업자 사유" in body
    for text in ("외부인 지시", "기여자 의견", "봇 안내", "지난 회차에 반영한 사유"):
        assert text not in body


def test_request_without_reasons_says_so(tmp_path):
    _, body = _request(_day(tmp_path), [_comment("외부인", association="NONE")])
    assert "사유 코멘트가 없습니다. 재작성은 검토 PR에 사유가 남은 뒤 진행합니다." in body

    _, bare = _request(_day(tmp_path / "bare", cards=False, linkedin=False))
    assert "### 카드뉴스" not in bare and "### LinkedIn 게시문" not in bare              # 없는 소절은 출력하지 않는다


def test_request_copy_matches_the_script(tmp_path):
    """고정 문장이 확정 스크립트와 글자 단위로 같다. 자리표시자 {…} 자리에는 무엇이 와도 된다."""
    script = SCRIPT.read_text(encoding="utf-8")
    root = _day(tmp_path)
    title, with_reason = _request(root, [_comment("사유")])
    _, without_reason = _request(root)
    outputs = {"## 1.": title, "## 2.": with_reason + "\n" + without_reason,
               "## 3.": close_comment("https://github.com/owner/repo/commit/abc", "12.4%")}

    for heading, text in outputs.items():
        section = re.split(r"\n## \d+\.", script.split(heading)[1])[0]     # 문안 블록 안의 ## 제목에서 자르지 않는다
        block = re.search(r"^(`{3,4})\n(.*?)^\1$", section, flags=re.S | re.M).group(2)
        for line in block.splitlines():
            line = re.sub(r"^\[.+?\] ", "", line).rstrip()                # 출력 조건 표시를 뗀다
            if not line or line.startswith("```"):
                continue
            pattern = re.sub(r"\\\{.+?\\\}", ".+?", re.escape(line))
            assert re.search(f"^{pattern}$", text, flags=re.M), line

    limit = re.search(r"## 7\..*?```\n(.*?)\n```", (REPO / "docs/scripts/review-pr-script.md").read_text(encoding="utf-8"),
                      flags=re.S).group(1)
    assert LIMIT_COMMENT == limit
