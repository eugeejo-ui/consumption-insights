# Phase 3 · Task 6: 워크플로 연결

| 항목 | 내용 |
|---|---|
| 상태 | **완료** (2026-09-15). push·CI 시뮬레이션 실측 완료. 테스트 108개. 코드 커밋 `d72560e` |
| 상위 계획 | `docs/plans/phase3-linkedin-cardnews.md` Task 6, 결정 D9, 규칙 4·14·16·18 |
| 담당 | C (사용자 확인 3회: 계획 승인, **검토 PR 본문 문안 승인**, **push·시뮬레이션 실행 승인**) |

## 목표

CI에서 카드가 실제로 구워지고, **검토 PR 본문에서 카드 그림과 게시문을 보고 판단할 수 있게** 한다. 머지 후 게시는 Task 5가 `--build`에 이미 연결했다.

이 Task에서 처음으로 Task 3~6 코드가 GitHub에 올라간다. 올라간 다음 날부터 매일 수집이 새 코드로 돈다.

## 착수 전 확인한 결함 (Task 5 회귀)

**게시 워크플로가 승인일을 읽지 못하게 됐다 [확인].**

- `publish.yml`은 `pipeline.py --build`의 출력 줄 `site written: … (<날짜> 승인 스냅샷)`에서 `sed`로 날짜를 뽑아, 시트 적재 단계에 넘긴다.
- Task 5에서 이 줄을 `(<날짜> 승인 스냅샷, 카드 N일분)`으로 바꿨다. `sed` 식이 맞지 않아 날짜가 빈 값이 된다.
- 결과: 시트 적재 단계가 `data/raw//events.json`을 찾지 못해 **조용히 적재를 건너뛴다.** 게시는 계속되므로 실패로 드러나지 않는다.
- push 전이라 운영에는 영향이 없다.

**수정:** 사람이 읽는 출력 문장을 파싱하지 않는다. `build_site()`가 단계 출력(`GITHUB_OUTPUT`)에 `day`를 직접 쓰고, `publish.yml`은 그 값을 쓴다. 테스트로 고정한다.

## 승인 결과 (2026-09-15)

사용자가 계획을 승인했다("어 승인한다").

## Step 0 실행 결과 (2026-09-15, 문안 승인됨)

`docs/scripts/review-pr-script.md`를 작성했다. 자리표시자 8개, 장 이름 6개, 절 3개(미리보기·실패·게시문)의 고정 문안과 출력 조건을 담았다.

**`/humanize-korean` 점검 [확인]:** run `2026-09-15-002`, light 경로(risk_band low, score 0). 변경률 0.0%, 터치율 0/21, 게이트 exit 0 수렴. 스킬이 보고한 제안 3건 중 2건을 반영했고, 반영본도 게이트를 통과했다(변경률 0.9%, 터치율 2/21).

| 위치 | 초안 | 확정 제안 | 이유 |
|---|---|---|---|
| 실패 절 제목 | `카드뉴스 생성 실패` | `카드뉴스·게시문 생성 실패` | 게시문만 실패한 날에도 이 절이 붙는다. 제목이 범위와 맞지 않았다 |
| 실패 안내 | `카드 또는 게시문 생성이 실패했습니다.` | `카드 또는 게시문 생성에 실패했습니다.` | 더 자연스러운 호응이다 |

유지한 제안 1건: 본문의 `카드`(낱장을 센다)와 절 제목의 `카드뉴스`(묶음)는 뜻이 달라 통일하지 않았다.

## 건드리는 파일

| 파일 | 동작 |
|---|---|
| `docs/scripts/review-pr-script.md` | **신규(Step 0, 규칙 16).** 검토 PR 본문에 새로 들어가는 문안 |
| `publish/review_pr.py` | 신규. 검토 PR 본문 조립(검토 보고서 + 글 초안 + 카드 + 게시문 + 실패 사유 + 장수 경고) |
| `templates/review_pr.md.j2` | 신규. 위 본문의 새 절 |
| `.github/workflows/collect.yml` | 한글 글꼴 설치(pytest보다 먼저), 설치 글꼴 기록, 본문을 `publish.review_pr`로 조립, 제한 시간 15 → 25분 |
| `.github/workflows/publish.yml` | 승인일을 단계 출력에서 읽는다(회귀 수정) |
| `pipeline.py` | `build_site()`가 `day`를 단계 출력에 쓴다 |
| `publish/render_cards.py` | 레이아웃 검사 통과 시 최소 여백·최대 오른쪽 끝을 한 줄로 출력한다(CI 기록용) |
| `tests/test_review_pr.py` | 신규. 테스트 5개 |
| `tests/test_workflows.py` | 신규. 테스트 1개 |
| `tests/test_pipeline.py` | 테스트 1개 추가 |
| `docs/tasks/phase3/task-6-workflow.md` | 이 파일. 실행 후 결과를 덧붙인다 |
| `docs/plans/phase3-linkedin-cardnews.md`, `docs/phases/phase-3-linkedin.md`, `CLAUDE.md` | 규칙 7에 따라 갱신 |

**건드리지 않는 것:** 카드 문안·템플릿·데이터, 기존 검토 보고서(`review.md.j2`)와 글 초안 문안(D17 교체는 다른 대화), 문구 반려 루프(`revise-copy`, Task 7), 소개 카드(Task 8).

## 검토 PR 본문 구성

순서는 기존 두 절 뒤에 새 절 두 개를 붙인다. 카드는 E1인 날에만 붙는다.

| 순서 | 절 | 조건 | 비고 |
|---|---|---|---|
| 1 | 검토 보고서(`review.md`) | 항상 | 기존 |
| 2 | 글 초안(`post.md`) | E1 | 기존 |
| 3 | **카드뉴스 미리보기** | 카드가 구워진 날 | 장마다 이미지. 이미지 주소는 `raw.githubusercontent.com/<저장소>/<커밋 SHA>/data/raw/<날짜>/cards/NN-*.png`. 원본 PDF 링크, 머지 후 게시 주소, 10장 초과 경고 |
| 3' | **카드뉴스 생성 실패** | `card-errors.txt`가 있는 날 | 사유를 코드 블록으로 그대로 싣는다 |
| 4 | **LinkedIn 게시문** | `linkedin.md`가 있는 날 | 복사하기 쉽게 코드 블록으로 싣는다 |

**이미지 주소에 브랜치 이름이 아니라 커밋 SHA를 쓴다.** 검토 브랜치는 같은 날 다시 돌면 강제 push로 갱신된다. 브랜치 이름으로 걸면 캐시 때문에 이전 카드가 보일 수 있다(상위 계획 Task 6).

**본문 조립을 셸이 아니라 파이썬 모듈로 옮긴다.** 조건이 네 가지로 늘어 YAML 안의 셸로는 검증할 수 없다. `python -m publish.review_pr --day <날짜> --repo <저장소> --sha <SHA>`가 본문을 출력하고, 테스트가 모든 조건을 확인한다.

## Step 0 스크립트 초안 (규칙 16, 승인 대상)

아래는 초안이다. `/humanize-korean` 점검을 거쳐 `docs/scripts/review-pr-script.md`에 확정한다. 자리표시자는 `{…}`로 적는다.

| 위치 | 초안 |
|---|---|
| 카드 절 제목 | `## 카드뉴스 미리보기 · {장수}장` |
| 원본 PDF | `원본 PDF: [cards.pdf]({PDF 주소})` |
| 게시 주소 | `머지 후 게시 주소: {사이트 카드 주소}` |
| 10장 초과 경고 | `카드가 {장수}장으로 10장을 넘습니다. 게시 분량은 검토자가 판단합니다.` |
| 이미지 대체 텍스트 | `{순번}장 {장 이름}`. 장 이름은 카드 스크립트의 장 제목을 쓴다(표지, 단가 변동 내역, 플랫폼별 월 사용료, 월 사용료 변동 내역, 순위 변동, 마무리 안내) |
| 실패 절 제목 | `## 카드뉴스·게시문 생성 실패` (점검 후 수정) |
| 실패 안내 | `카드 또는 게시문 생성에 실패했습니다. 검토 자료는 정상입니다.` (점검 후 수정) |
| 게시문 절 제목 | `## LinkedIn 게시문` |
| 게시문 안내 | `LinkedIn에는 사람이 직접 게시합니다.` |

## 인터페이스

```python
# publish/review_pr.py
WARN_OVER = 10                                       # 규칙 18: 10장을 넘으면 경고
CARD_NAMES = {"cover": "표지", "price": "단가 변동 내역", "chart": "플랫폼별 월 사용료",
              "cost": "월 사용료 변동 내역", "rank": "순위 변동", "closing": "마무리 안내"}

build_body(day: str, repo: str, sha: str, root: Path = Path("data/raw"),
           site: str = "https://eugeejo-ui.github.io/consumption-insights") -> str
    # data/raw/<날짜>/의 review.md, post.md, cards/, card-errors.txt, linkedin.md를 읽어 본문을 만든다
    # python -m publish.review_pr --day --repo --sha → 표준 출력

# pipeline.py
build_site(day=None)                                  # 기존 + write_outputs(day=<승인일>)

# publish/render_cards.py
check_layout(report, cards) -> dict                   # 기존 검사 + {"min_gap": px, "max_right": px} 반환. bake가 한 줄 출력
```

**`collect.yml` 변경**

```yaml
- name: install Korean fonts            # pytest보다 먼저. 없으면 두부 글자 카드가 된다 [확인 2026-09-12]
  run: sudo apt-get update && sudo apt-get install -y --no-install-recommends fonts-noto-cjk && fc-list :lang=ko family | sort -u
- run: python -m pytest -q
...
- name: open or update review PR
  run: |
    …git commit…
    SHA=$(git rev-parse HEAD)
    python -m publish.review_pr --day "$DAY" --repo "$GITHUB_REPOSITORY" --sha "$SHA" > "$BODY"
```

## 단계

- [x] **Step 0 검토 PR 본문 스크립트 (규칙 16).** 초안 작성 → `/humanize-korean` 점검 → **사용자 문안 승인.** 승인 전에는 Step 1로 넘어가지 않는다
- [x] **Step 1** 테스트 7개를 먼저 쓰고 실패를 확인한다
- [x] **Step 2** `publish/review_pr.py`와 `templates/review_pr.md.j2`를 구현한다
- [x] **Step 3** `build_site()`의 `day` 단계 출력과 `publish.yml` 수정(회귀 수정)
- [x] **Step 4** `collect.yml` 수정. `render_cards`의 레이아웃 요약 출력
- [x] **Step 5** 전체 테스트 → 108개 통과. 로컬에서 Task 5 임시 폴더 산출물로 본문을 만들어 마크다운을 눈으로 확인한다
- [x] **Step 6** 커밋 전 검사. **push할 전체 범위**(`origin/main..HEAD`, 현재 17개 커밋 + 이 Task)의 변경 내용에서 이메일·로컬 사용자 경로·개인 프로젝트 ID를 찾고, 커밋 작성자 이메일이 모두 noreply인지 확인한다. 커밋
- [x] **Step 7 사용자 승인 요청 (규칙 4).** 아래 외부 행동 세 가지를 한 번에 여쭙고, 승인 전에는 실행하지 않는다
  1. `origin/main`을 받아 그 위로 올린 뒤(매일 봇 커밋이 쌓여 있다) main에 push. **push하면 `publish.yml`이 돌아 대시보드를 다시 배포한다**(내용 변화 없음)
  2. `collect.yml`을 시뮬레이션으로 수동 실행(`review/simulated` 검토 PR 생성)
  3. 확인이 끝난 시뮬레이션 PR을 닫고 브랜치 삭제
- [x] **Step 8 CI 실측** (승인 후)
  - 글꼴 설치 시간, `fc-list` 결과에 `Noto Sans CJK KR`이 있는지(Task 4 조정안 6 [미확인] 해소)
  - pytest의 실제 굽기 테스트가 CI에서 **건너뛰지 않고 통과**하는지
  - 1단계 카드 굽기 시간, 레이아웃 요약(최소 여백)
  - PR 본문에 카드 5장이 보이는지. CI가 구운 PNG를 받아 두부 글자가 없는지 눈으로 확인한다
  - 게시 워크플로가 승인일을 읽는지(push로 돈 실행의 `log` 작업 기록)
  - 시뮬레이션 PR을 닫는다
- [x] **Step 9** 이 파일에 실행 결과를 덧붙이고 관련 문서를 갱신한다. **보고하고 멈춘다**(규칙 10)

## 테스트 목록

**`tests/test_review_pr.py` (5개)** — Task 5의 가짜 굽기처럼 파일을 만들어 검증한다.

| # | 이름 | 확인하는 것 |
|---|---|---|
| 1 | `test_body_shows_review_post_cards_and_linkedin_in_order` | 검토 보고서 → 글 초안 → 카드 → 게시문 순서. 이미지 주소가 SHA로 고정되고 파일 순번대로다. PDF 링크와 머지 후 게시 주소가 있다 |
| 2 | `test_body_has_no_card_section_on_a_non_e1_day` | 카드·게시문 파일이 없는 날에는 두 절이 없다 |
| 3 | `test_card_failure_is_shown_with_its_reason` | `card-errors.txt`가 있으면 실패 절이 생기고 사유가 코드 블록으로 그대로 실린다. 카드 절은 없다 |
| 4 | `test_more_than_ten_cards_adds_a_warning` | 11장이면 경고 문장이 있고, 10장이면 없다 |
| 5 | `test_fixed_copy_matches_the_script` | 본문의 고정 문장이 `docs/scripts/review-pr-script.md` 확정 문안과 글자 단위로 같다 |

**`tests/test_workflows.py` (1개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 6 | `test_collect_installs_korean_fonts_before_tests_and_uses_the_body_module` | `collect.yml`에서 `fonts-noto-cjk` 설치가 `pytest`보다 앞에 있고, 본문을 `publish.review_pr`로 만든다 |

**`tests/test_pipeline.py` (1개)**

| # | 이름 | 확인하는 것 |
|---|---|---|
| 7 | `test_build_writes_the_approved_day_to_the_step_output` | `--build`가 `GITHUB_OUTPUT`에 `day=<승인일>`을 쓴다(회귀 방지) |

**합계:** 101 → **108**

## 확인 방법 (증거)

| 확인 항목 | 방법 |
|---|---|
| 테스트 | 로컬 `pytest -q`, CI pytest 단계 기록(실제 굽기 테스트 통과·건너뜀 여부) |
| CI 글꼴 | `fc-list :lang=ko family` 출력 |
| CI 카드 품질 | 시뮬레이션 PR의 PNG를 받아 확인. 레이아웃 요약 줄 |
| PR 본문 | 시뮬레이션 PR 화면 |
| 회귀 수정 | push로 돈 `publish.yml` 실행의 승인일 값 |
| 시간 | 각 단계 소요 시간 |

## 위험

| 위험 | 대응 |
|---|---|
| push하면 매일 수집이 새 코드로 돈다. 실제 E1이 오면 CI가 카드를 굽는다 | 이 Task의 시뮬레이션으로 CI 굽기를 먼저 확인한다. 굽기가 실패해도 검토 PR은 열린다(Task 5) |
| 로컬과 CI 글꼴 차이로 CI에서만 레이아웃 검사에 걸린다 | 걸리면 카드 없이 사유가 PR에 보인다. 이 경우 멈추고 보고한 뒤 디자인 계획부터 고친다(규칙 10) |
| 글꼴 설치로 매일 수집 시간이 늘어난다 | 약 1~2분으로 추정한다 [가정]. 실측값을 기록한다. 제한 시간을 25분으로 늘린다 |
| 로컬 main이 `origin/main`보다 17개 커밋 앞서 있고, 그사이 봇 커밋이 쌓였다 | push 전에 받아서 그 위로 올린다. 봇은 `data/checks.csv`와 가격 지문 파일만 고치므로 충돌 가능성이 낮다. 충돌이 나면 멈추고 보고한다 |
| main 보호 규칙이 없어 잘못된 워크플로가 바로 반영된다 | 기존 결정·확인 대기 항목이다(저장소 보안 설정 4건). push 전 테스트와 YAML 문법 검사로 대신한다 |
| PR 본문의 이미지가 공개 저장소 원본 주소에 의존한다 | 공개 저장소라 인증 없이 보인다. 강제 push로 이전 SHA가 사라져도 본문은 매 실행 새 SHA로 갱신된다 |
| 시뮬레이션 카드는 게시 경로를 검증하지 못한다(승인되지 않으므로 복사되지 않는다) | 게시 복사는 Task 5 테스트와 로컬 실측으로 확인했다. 실제 게시는 Task 9 또는 첫 실제 E1에서 확인한다 |

## 상위 코드 계획과 달라지는 점

| 코드 계획 | 이 계획 | 이유 |
|---|---|---|
| 본문을 워크플로 셸에서 조립 | `publish/review_pr.py` 모듈 | 조건 4가지를 테스트로 검증한다 |
| PR 본문 문안 언급 없음 | Step 0 스크립트 단계 | 규칙 16. PR 본문도 사람이 읽는 자동 생성 문장이다 |
| `continue-on-error`로 카드 단계 분리 | 파이프라인이 실패를 흡수한다(Task 5) | 1단계가 이미 카드 실패를 잡는다. 워크플로에서 따로 분리할 필요가 없다 |
| 10장 초과 경고는 Task 3 | 이 Task | Task 3에서 옮겼다 |
| 회귀 수정 없음 | `publish.yml` 승인일 읽기 수정 | 계획 작성 중 발견한 Task 5 회귀 |
| 테스트: 워크플로 실측만 | +7 → 108 | 본문 조건, 워크플로 순서, 회귀를 코드로 고정한다 |

## 완료 기준

- 검토 PR 본문 문안이 승인됐다.
- 테스트 7개를 추가해 전체 108개가 통과한다.
- 사용자 승인 아래 push했고, 시뮬레이션 검토 PR에 CI가 구운 카드와 게시문이 보인다.
- CI 카드에 두부 글자가 없고 레이아웃 검사를 통과했다.
- 게시 워크플로가 승인일을 읽는다.
- 이 파일에 실행 결과가 덧붙고, 관련 문서가 갱신되고, 커밋됐다.

---

## 실행 결과 (2026-09-15)

사용자가 검토 PR 본문 문안을 승인했다("어 해봐"). Step 1~6을 마쳤다. 테스트 108개 통과. 코드 커밋 `d72560e`. **Step 7(외부 행동 승인)을 기다린다.**

### 실제로 한 일

| Step | 결과 |
|---|---|
| 1 | 테스트 7개 작성, 모두 실패 확인 |
| 2 | `publish/review_pr.py`, `templates/review_pr.md.j2` |
| 3 | `build_site()`가 `day`를 단계 출력에 쓴다. `publish.yml`에서 `tee`·`sed` 파싱을 없앴다(회귀 수정) |
| 4 | `collect.yml`: 글꼴 설치를 pytest 앞에 두고 설치된 글꼴을 기록, 본문을 모듈로 조립(SHA 고정), 제한 시간 25분. `check_layout`이 요약을 돌려주고 `bake`가 한 줄 출력 |
| 5 | 전체 **108개 통과**(87.5초) [확인]. Task 5 종단 실측 산출물로 본문을 만들어 확인했다: 6,186자, 검토 보고서 → 글 초안 → 카드 5장 → 게시문 순서 |
| 6 | 커밋 `d72560e`. push 범위 검사(아래) |

### push 범위 검사 [확인]

| 항목 | 결과 |
|---|---|
| 범위 | 로컬 main이 `origin/main`보다 **20개 커밋** 앞선다(Task 3~6 코드·문서) |
| 커밋 작성자·커미터 이메일 | 모두 GitHub noreply 한 가지 |
| 추가된 줄의 이메일 주소 | 0건(검사식이 `@pytest.fixture` 같은 데코레이터를 잡았으나 주소가 아니다) |
| 로컬 사용자 경로 | 0건 |
| 개인 프로젝트 ID | 0건 |
| 이미지·PDF·`_workspace/` 파일 | 0건(카드는 저장소에 올리지 않았다. CI가 검토 브랜치에 만든다) |
| 원격 main의 새 커밋 | 봇 커밋 4개(`data/checks.csv`, BigQuery 가격 지문). 로컬 변경 파일과 겹치는 파일 0개. 그 위로 올릴 때 충돌 가능성이 없다 |

### 구현 중 달라진 점

| 계획 | 실제 | 이유 |
|---|---|---|
| 테스트 6 이름 `test_collect_installs_korean_fonts_before_tests_and_uses_the_body_module` | `test_workflows_install_fonts_first_and_pass_values_through_step_outputs` | `publish.yml` 회귀 수정(`sed` 제거)도 같은 테스트에서 확인한다. `yaml.safe_load`로 두 워크플로의 문법도 검사한다 |
| `원본 PDF`와 `머지 후 게시 주소`를 두 줄로 | 빈 줄로 나눈 두 문단 | 마크다운은 이어진 두 줄을 한 문단으로 합친다. 스크립트의 줄 구분을 화면에서 지키기 위해서다. 문안은 같다 |

## 외부 행동과 CI 실측 (2026-09-15)

사용자가 외부 행동 3건을 승인했다("진행하지 승인한다"). **3-6 완료.**

### 실행한 외부 행동

| 행동 | 결과 |
|---|---|
| 1. main push | 원격에 봇 커밋이 5개로 늘어 있었다(`data/checks.csv`, 가격 지문). 그 위로 로컬 커밋 21개를 올렸다(충돌 0건). 올린 뒤 테스트 108개 통과를 다시 확인하고 push했다(`580284a..a7bd8ce`) |
| 2. 수집 워크플로 시뮬레이션 실행 | 실행 34931680729 성공. 검토 PR #4(`review/simulated`) 생성 |
| 3. 시뮬레이션 PR 닫기 | PR #4 닫음, 원격 브랜치 삭제. 머지하지 않았다 |

**리베이스로 커밋 해시가 바뀌었다.** Task 3~6 문서에 적은 해시를 새 해시로 모두 고쳤다(21개 커밋, 문서 7개에서 36곳).

### CI 실측 [확인]

**게시 워크플로(push로 실행, 34931656370): 성공**

| 항목 | 결과 |
|---|---|
| 회귀 수정 | `log` 작업의 `DAY`가 `2026-09-11`이다. 승인일이 시트 적재 단계로 넘어갔다 |
| pytest | 107개 통과, 1개 건너뜀(게시 서버에는 한글 글꼴을 설치하지 않으므로 실제 굽기 테스트를 건너뛴다. 설계대로다) |
| 사이트 | `site written: site/index.html (2026-09-11 승인 스냅샷, 카드 0일분)`. 배포 성공. 승인된 카드가 아직 없어 복사한 카드는 0일분이다 |

**수집 워크플로 시뮬레이션(34931680729): 성공, 전체 72초**

| 단계 | 시간 | 결과 |
|---|---|---|
| 한글 글꼴 설치 | 18초 | `fc-list :lang=ko`에 **`Noto Sans CJK KR`**이 있다. Task 4 조정안 6의 [미확인]을 해소했다 |
| pytest | 24초 | **108개 통과.** 실제 굽기 테스트가 건너뛰지 않고 CI Chrome으로 돌았다 |
| 1단계(카드 5장 굽기 포함) | 10초 | `레이아웃 검사 통과: 5장, 가장 좁은 여백 151px, 가장 오른쪽 글자 끝 1028/1032px` |
| 검토 PR 생성 | 6초 | PR #4. 본문 8,094자 |

**CI 카드 품질 (PR #4의 SHA 주소에서 PNG 5장을 받아 확인)**

- 두부 글자 없음. 한글과 라틴 글자 모두 Noto 계열로 그려졌다.
- PNG 56~93KB. 넘침·겹침 없음.
- 로컬과 줄바꿈이 다르다. 차트 장 리드와 마무리 장 리드가 로컬(맑은 고딕)에서는 두 줄, CI(Noto Sans CJK)에서는 한 줄이다. CI 한글 글자 폭이 더 좁다.
- **`1028/1032px`은 넘침이 아니다.** 마무리 장 리드 한 줄이 본문 폭을 꽉 채운 값이다. 글자가 더 길어지면 넘치지 않고 다음 줄로 내려간다(리드 상한 3줄). 넘침 검사가 막는 것은 줄을 바꿀 수 없는 긴 단어다.
- 사소한 차이: Noto의 가운뎃점(`·`) 앞뒤 여백이 맑은 고딕보다 넓다. 읽기에는 지장이 없다.

**PR #4 본문:** 검토 보고서 → 글 초안 → `## 카드뉴스 미리보기 · 5장`(원본 PDF 링크, 머지 후 게시 주소, 이미지 5장) → `## LinkedIn 게시문` 순서로 나왔다. 이미지 주소는 브랜치 커밋 SHA로 고정됐다.

### 계획과 달라진 점 (외부 행동 단계)

| 계획 | 실제 | 이유 |
|---|---|---|
| 원격 봇 커밋 4개 위로 올린다 | 5개 | 승인 요청과 실행 사이에 매일 수집 봇이 커밋 1개를 더 올렸다. 겹치는 파일은 여전히 0개였다 |
| 문서의 커밋 해시 유지 | 모두 새 해시로 교체 | 리베이스로 해시가 바뀌었다. 옛 해시는 원격에 없다 |

### 다음 Task에 넘기는 것

- **Task 7 (문구 반려 루프):** 검토 PR 본문은 `publish/review_pr.py`가 만든다. `revise-copy` 라벨 안내를 넣으려면 `docs/scripts/review-pr-script.md`에 문안을 먼저 추가한다(규칙 16).
- **Task 9 (종단 검증):** 승인된 카드의 사이트 게시(`site/cards/<날짜>/`)는 로컬 테스트와 실측으로만 확인했다. 시뮬레이션 스냅샷은 승인되지 않으므로 CI에서 게시 경로를 확인하려면 다른 방법이 필요하다.
- **운영:** 다음 날부터 매일 수집이 새 코드로 돈다. 가격이 바뀌지 않는 날은 글꼴 설치와 pytest만 늘어 약 45초가 더 걸린다.
- **문서 push:** 이 기록 커밋은 로컬에만 있다. 다음 push 때 함께 올린다.
