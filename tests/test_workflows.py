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
