from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def test_workflows_install_fonts_first_and_pass_values_through_step_outputs():
    collect = (WORKFLOWS / "collect.yml").read_text(encoding="utf-8")
    publish = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
    yaml.safe_load(collect)
    yaml.safe_load(publish)

    # CI에는 한글 글꼴이 없다. 설치 전에 실제 굽기 테스트나 1단계가 돌면 두부 글자 카드가 된다.
    assert collect.index("fonts-noto-cjk") < collect.index("python -m pytest")
    assert collect.index("fonts-noto-cjk") < collect.index("python pipeline.py")
    # 검토 PR 본문은 테스트한 모듈로 만든다. 이미지 주소는 커밋 SHA로 고정한다.
    assert "python -m publish.review_pr" in collect and "git rev-parse HEAD" in collect
    # 승인일은 사람이 읽는 출력 문장을 파싱하지 않고 단계 출력으로 받는다(Task 5 회귀).
    assert "sed -n" not in publish and "steps.site.outputs.day" in publish


def test_revise_workflow_is_scoped_and_never_puts_comments_in_the_shell():
    text = (WORKFLOWS / "revise.yml").read_text(encoding="utf-8")
    revise = yaml.safe_load(text)
    collect = (WORKFLOWS / "collect.yml").read_text(encoding="utf-8")

    assert revise[True]["pull_request"]["types"] == ["labeled", "unlabeled"]      # PyYAML은 on: 을 True로 읽는다
    (job,) = revise["jobs"].values()
    for condition in ("github.event.label.name == 'revise-copy'", "startsWith(github.event.pull_request.head.ref, 'review/')",
                      "github.event.pull_request.head.repo.full_name == github.repository"):
        assert condition in job["if"]
    # 코멘트·제목·브랜치 이름 같은 사용자 입력은 식(${{ }})으로 셸에 넣지 않는다. 값은 env나 API 응답 파일로 받는다.
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs and all("${{" not in run for run in runs)
    assert "github.event.comment" not in text and "pull_request.body" not in text and "pull_request.title" not in text
    assert "python -m publish.revise_request" in text

    # 매일 수집이 검토 브랜치를 강제 push해도 라벨이 남아 있으면 보류 파일을 다시 넣는다.
    assert "revise-copy" in collect
    assert collect.index("copy-hold.txt") < collect.index('git commit -m "review: price snapshot')


def test_publish_runs_when_intro_cards_change():
    publish = yaml.safe_load((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))
    assert "data/cards/**" in publish[True]["push"]["paths"]             # 소개 카드만 바뀐 push에도 사이트에 올린다(D21)
