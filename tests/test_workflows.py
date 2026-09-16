import re
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


def test_sheet_append_runs_only_for_days_approved_in_this_run():
    """최근 승인일로 적재하면 첫 실제 변동을 승인한 뒤 코드를 push할 때마다 같은 행이 시트에 다시 쌓인다(3-9 코드 확인)."""
    publish = yaml.safe_load((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))
    build, log = publish["jobs"]["build"], publish["jobs"]["log"]
    record = next(step for step in build["steps"] if step.get("name") == "record approval for merged snapshots")
    assert record.get("id") == "record" and "confirmed=" in record["run"] and "GITHUB_OUTPUT" in record["run"]
    assert build["outputs"]["confirmed"] == "${{ steps.record.outputs.confirmed }}"
    assert "needs.build.outputs.confirmed" in log["if"]
    assert "needs.build.outputs.day" not in yaml.safe_dump(log)            # 최근 승인일로는 적재하지 않는다


def test_workflows_pin_actions_and_limit_oidc_and_shell_inputs():
    """보안 점검(2026-09-15): 액션은 커밋 SHA로 고정한다. OIDC 토큰은 인증이 필요한 작업에만 준다.
    사람이 넣는 값(workflow_dispatch 입력, 이벤트 본문)은 식으로 셸에 넣지 않는다."""
    oidc_jobs = set()
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "permissions" in workflow, path.name                      # 저장소 기본 토큰 권한에 기대지 않는다
        top = workflow["permissions"]
        for name, job in workflow["jobs"].items():
            permissions = job.get("permissions", top)
            if permissions.get("id-token") == "write":
                oidc_jobs.add(f"{path.stem}.{name}")
            for step in job["steps"]:
                if "uses" in step:
                    assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", step["uses"]), (path.name, step["uses"])
                run = step.get("run", "")
                assert "${{ inputs." not in run and "${{ github.event." not in run, (path.name, name)
    assert oidc_jobs == {"publish.deploy", "publish.log", "sheets-baseline.baseline"}


def test_publish_runs_when_intro_cards_change():
    publish = yaml.safe_load((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))
    assert "data/cards/**" in publish[True]["push"]["paths"]             # 소개 카드만 바뀐 push에도 사이트에 올린다(D21)


def test_bot_assigns_the_owner_so_notifications_reach_a_person():
    """저장소 구독자 수가 0이라, 담당자를 지정하지 않으면 봇이 연 검토 PR과 알림 Issue가
    메일로 오지 않는다 [확인 2026-09-16]. 계정 이름은 적지 않고 소유자 문맥값을 쓴다."""
    texts = {path.stem: path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml")}
    for name, text in texts.items():
        opened = text.count("gh issue create") + text.count("gh pr create")
        if not opened:
            continue
        assert opened == text.count('--assignee "$OWNER"'), name
        assert "OWNER: ${{ github.repository_owner }}" in text, name
    assert '--add-assignee "$OWNER"' in texts["collect"]        # 열려 있는 검토 PR을 갱신할 때도 담당자를 유지한다
